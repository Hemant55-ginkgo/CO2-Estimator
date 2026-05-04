# =============================================================================
# pdf_export.py — PDF Report Generator
# =============================================================================
# This file takes the CO2 calculation results and produces a clean,
# downloadable PDF report using the fpdf2 library.
#
# Think of this module like a document template in a freight office —
# it always produces the same structured layout, just filled with
# different shipment data each time.
#
# The PDF contains:
#   1. Header with project title and generation date
#   2. Shipment input summary (origin, destination, weight)
#   3. Results table (one row per transport mode)
#   4. Methodology note citing the GLEC Framework
# =============================================================================

from fpdf import FPDF          # the PDF generation library
from datetime import datetime  # to print the report generation date


# -----------------------------------------------------------------------------
# COLOUR PALETTE — defined once here so the whole report stays consistent
# -----------------------------------------------------------------------------
# Colors are RGB tuples: (Red, Green, Blue) — each value is 0 to 255

COLOUR_DARK       = (30,  41,  59)    # near-black for titles
COLOUR_ACCENT     = (16, 185, 129)    # green — used for header bar
COLOUR_LIGHT_ROW  = (240, 253, 244)   # very light green for alternating rows
COLOUR_WHITE      = (255, 255, 255)
COLOUR_GREY_TEXT  = (100, 116, 139)   # muted grey for secondary text
COLOUR_BORDER     = (203, 213, 225)   # light grey for table borders


# -----------------------------------------------------------------------------
# MAIN FUNCTION: generate_pdf()
# -----------------------------------------------------------------------------
# This is the only function the rest of the app needs to call.
# It receives the data, builds the PDF, and returns it as bytes.
#
# "bytes" means raw binary data — like the contents of a file before
# it's saved to disk. Streamlit's download button accepts bytes directly,
# so we never need to save a temporary file on the server.
# -----------------------------------------------------------------------------

def generate_pdf(
    origin:      str,
    destination: str,
    weight_kg:   float,
    distance_km: float,
    results:     dict,
) -> bytes:
    """
    Generate a CO2 emissions report as a PDF and return it as bytes.

    Parameters:
        origin      — departure city name
        destination — arrival city name
        weight_kg   — shipment weight in kg
        distance_km — road distance from the ORS API
        results     — dictionary from calculator.py with all three modes

    Returns:
        PDF file contents as bytes, ready for Streamlit's download button
    """

    # Create a new PDF object
    # "P" = Portrait, "mm" = millimetres, "A4" = standard European page size
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ------------------------------------------------------------------
    # SECTION 1: HEADER BAR
    # ------------------------------------------------------------------
    # Draw a solid green rectangle across the top of the page
    pdf.set_fill_color(*COLOUR_ACCENT)
    pdf.rect(x=0, y=0, w=210, h=28, style="F")   # F = filled rectangle

    # Title text inside the header bar
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.set_text_color(*COLOUR_WHITE)
    pdf.set_xy(10, 7)
    # Note: we write "CO2" not "CO2" with subscript —
    # fpdf2 built-in fonts don't support Unicode subscript characters
    pdf.cell(0, 10, "European Freight CO2 Estimator", ln=True)

    # Subtitle: report generation timestamp
    pdf.set_font("Helvetica", size=9)
    pdf.set_xy(10, 18)
    date_str = datetime.now().strftime("%d %B %Y, %H:%M")
    pdf.cell(0, 5, f"Report generated: {date_str}", ln=True)

    # Reset text colour to dark for everything below the header
    pdf.set_text_color(*COLOUR_DARK)

    # ------------------------------------------------------------------
    # SECTION 2: SHIPMENT SUMMARY
    # ------------------------------------------------------------------
    pdf.set_xy(10, 36)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 7, "Shipment Summary", ln=True)

    # Thin green underline beneath the section title
    pdf.set_draw_color(*COLOUR_ACCENT)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # Helper function — prints one label + value row
    # This is a function defined INSIDE another function, which is allowed.
    # It "closes over" the pdf object so it can use it without being passed it.
    def summary_row(label: str, value: str):
        pdf.set_font("Helvetica", style="B", size=9)
        pdf.set_text_color(*COLOUR_GREY_TEXT)
        pdf.cell(48, 6, label.upper(), ln=False)
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(*COLOUR_DARK)
        pdf.cell(0, 6, value, ln=True)

    summary_row("Origin",        origin)
    summary_row("Destination",   destination)
    summary_row("Weight",        f"{weight_kg:,.0f} kg  ({weight_kg / 1000:.3f} tonnes)")
    summary_row("Road Distance", f"{distance_km:,.1f} km  (OpenRouteService HGV routing)")

    pdf.ln(5)

    # ------------------------------------------------------------------
    # SECTION 3: RESULTS TABLE
    # ------------------------------------------------------------------
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.set_text_color(*COLOUR_DARK)
    pdf.cell(0, 7, "CO2 Emissions by Transport Mode", ln=True)

    pdf.set_draw_color(*COLOUR_ACCENT)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # Column widths — must total 190mm (210mm page minus 10mm margin each side)
    col_mode    = 50
    col_formula = 84
    col_co2     = 36
    col_vs_ftl  = 20

    # Table header row — dark background, white text
    pdf.set_fill_color(*COLOUR_DARK)
    pdf.set_text_color(*COLOUR_WHITE)
    pdf.set_font("Helvetica", style="B", size=8)
    pdf.set_draw_color(*COLOUR_DARK)
    pdf.set_line_width(0.3)

    pdf.cell(col_mode,    7, "Transport Mode", border=1, fill=True, align="C")
    pdf.cell(col_formula, 7, "Calculation",    border=1, fill=True, align="C")
    pdf.cell(col_co2,     7, "CO2e (kg)",      border=1, fill=True, align="C")
    pdf.cell(col_vs_ftl,  7, "vs FTL",         border=1, fill=True, align="C")
    pdf.ln()

    # Get FTL CO2 as the baseline for the comparison column
    ftl_co2 = results.get("road_ftl", {}).get("co2_kg", 1)

    # Table data rows
    pdf.set_draw_color(*COLOUR_BORDER)

    for i, (mode, data) in enumerate(results.items()):

        # Alternate row shading: white / light green
        fill_colour = COLOUR_LIGHT_ROW if i % 2 == 1 else COLOUR_WHITE
        pdf.set_fill_color(*fill_colour)
        pdf.set_text_color(*COLOUR_DARK)

        # Column 1: Mode name
        pdf.set_font("Helvetica", style="B", size=8)
        pdf.cell(col_mode, 8, data["label"], border=1, fill=True, align="L")

        # Column 2: Formula — distance x weight x factor
        formula_str = (
            f"{distance_km:,.1f} km"
            f" x {data['weight_tonnes']:.3f} t"
            f" x {data['factor']}"
        )
        pdf.set_font("Helvetica", size=7)
        pdf.cell(col_formula, 8, formula_str, border=1, fill=True, align="C")

        # Column 3: CO2 result in kg
        pdf.set_font("Helvetica", style="B", size=9)
        pdf.cell(col_co2, 8, f"{data['co2_kg']:,.2f}", border=1, fill=True, align="C")

        # Column 4: Multiple vs FTL baseline
        if mode == "road_ftl":
            pdf.set_font("Helvetica", style="I", size=7)
            vs_label = "baseline"
        else:
            multiplier = data["co2_kg"] / ftl_co2
            vs_label = f"{multiplier:.1f}x"
            pdf.set_font("Helvetica", style="B", size=8)

        pdf.cell(col_vs_ftl, 8, vs_label, border=1, fill=True, align="C")
        pdf.ln()

    pdf.ln(6)

    # ------------------------------------------------------------------
    # SECTION 4: KEY INSIGHT CALLOUT BOX
    # ------------------------------------------------------------------
    air_co2  = results.get("air", {}).get("co2_kg", 0)
    ratio    = round(air_co2 / ftl_co2, 1) if ftl_co2 > 0 else 0

    box_y = pdf.get_y()
    pdf.set_fill_color(*COLOUR_LIGHT_ROW)
    pdf.set_draw_color(*COLOUR_ACCENT)
    pdf.set_line_width(0.8)
    pdf.rect(10, box_y, 190, 16, style="FD")

    pdf.set_xy(14, box_y + 2)
    pdf.set_font("Helvetica", style="B", size=9)
    pdf.set_text_color(*COLOUR_ACCENT)
    pdf.cell(0, 5, "Key Insight", ln=True)

    pdf.set_xy(14, box_y + 8)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(*COLOUR_DARK)
    pdf.cell(
        0, 5,
        f"Air freight produces {ratio}x more CO2e than Full Truckload "
        f"on this route ({origin} to {destination}).",
        ln=True
    )

    pdf.ln(8)

    # ------------------------------------------------------------------
    # SECTION 5: METHODOLOGY NOTE
    # ------------------------------------------------------------------
    pdf.set_font("Helvetica", style="B", size=9)
    pdf.set_text_color(*COLOUR_DARK)
    pdf.cell(0, 6, "Methodology", ln=True)

    pdf.set_draw_color(*COLOUR_ACCENT)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(*COLOUR_GREY_TEXT)

    # multi_cell automatically wraps long text to fit the page width
    pdf.multi_cell(
        0, 5,
        "Emission factors sourced from the Global Logistics Emissions Council (GLEC) "
        "Framework v3.0, published by the Smart Freight Centre. "
        "Values used: Road FTL = 0.0623 kg CO2e/tonne-km, "
        "Road LTL = 0.1025 kg CO2e/tonne-km, "
        "Air Freight = 0.602 kg CO2e/tonne-km. "
        "Road distance calculated using the OpenRouteService HGV routing profile. "
        "Results represent indicative tank-to-wheel (TTW) emissions "
        "intended for modal comparison purposes only."
    )

    pdf.ln(3)

    # CSRD relevance note in italic
    pdf.set_font("Helvetica", style="I", size=7.5)
    pdf.multi_cell(
        0, 4,
        "CSRD Relevance: Under the EU Corporate Sustainability Reporting Directive (CSRD) "
        "and ESRS E1 standards, companies must disclose Scope 3 transport emissions. "
        "This tool supports preliminary freight emissions quantification for reporting purposes."
    )

    # ------------------------------------------------------------------
    # FOOTER
    # ------------------------------------------------------------------
    # set_y(-15) positions the cursor 15mm from the bottom of the page
    pdf.set_y(-15)
    pdf.set_font("Helvetica", style="I", size=7)
    pdf.set_text_color(*COLOUR_GREY_TEXT)
    pdf.cell(
        0, 5,
        "European Freight CO2 Estimator  |  GLEC Framework v3.0  |  For indicative purposes only",
        align="C"
    )

    # ------------------------------------------------------------------
    # RETURN THE PDF AS BYTES
    # ------------------------------------------------------------------
    # pdf.output() with no filename argument returns raw bytes.
    # Streamlit's st.download_button() accepts bytes directly —
    # no temporary file needed on the server.
    return bytes(pdf.output())


# -----------------------------------------------------------------------------
# TEST BLOCK — run this file directly to generate a sample PDF on disk
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    # Simulate the data that would come from calculator.py
    test_results = {
        "road_ftl": {
            "label": "Road (FTL)", "co2_kg": 155.75,
            "weight_tonnes": 5.0,  "factor": 0.0623,
            "description": "Full Truckload"
        },
        "road_ltl": {
            "label": "Road (LTL)", "co2_kg": 256.25,
            "weight_tonnes": 5.0,  "factor": 0.1025,
            "description": "Groupage / LTL"
        },
        "air": {
            "label": "Air Freight", "co2_kg": 1505.0,
            "weight_tonnes": 5.0,  "factor": 0.602,
            "description": "Air cargo"
        },
    }

    # Generate the PDF
    pdf_bytes = generate_pdf(
        origin      = "Munich",
        destination = "Paris",
        weight_kg   = 5000,
        distance_km = 500.0,
        results     = test_results,
    )

    # Save to disk so you can open and inspect it
    output_path = "test_report.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print("=" * 55)
    print("  PDF Export — Test Complete")
    print("=" * 55)
    print(f"  File saved: {output_path}")
    print(f"  Size      : {len(pdf_bytes):,} bytes")
    print()
    print("  Open test_report.pdf to inspect the layout.")
    print("  If it looks good, the PDF module is ready.")
    print("=" * 55)
