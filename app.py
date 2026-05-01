# =============================================================================
# app.py — European Freight CO2 Estimator
# =============================================================================
# This is the main application file. It is the front door of the entire project.
# When you run "streamlit run app.py", Streamlit reads this file top-to-bottom
# and builds the web page you see in your browser.
#
# This file does NOT do any heavy lifting itself — it delegates to the utils:
#   routing.py    → gets the real road distance from the API
#   calculator.py → applies the GLEC formula to get CO2 numbers
#   pdf_export.py → generates the downloadable PDF report
#
# Think of app.py as the freight coordinator: it takes the customer's order,
# hands it to the right specialist, and presents the final result.
# =============================================================================

import streamlit as st          # the web framework — builds the entire UI
import plotly.graph_objects as go  # creates the interactive bar chart
import time                     # used to add a small delay for UX polish

# Import our three utility modules
from utils.routing    import get_road_distance_km
from utils.calculator import calculate_emissions
from utils.pdf_export import generate_pdf


# =============================================================================
# PAGE CONFIGURATION
# Must be the very first Streamlit command — sets the browser tab title,
# icon, and layout width before anything else renders
# =============================================================================

st.set_page_config(
    page_title = "Freight CO₂ Estimator",
    page_icon  = "🚛",
    layout     = "wide",
    initial_sidebar_state = "collapsed",
)


# =============================================================================
# CUSTOM CSS — injecting styles directly into the page
# =============================================================================
# Streamlit has a default look, but we can override it with CSS.
# st.markdown() with unsafe_allow_html=True lets us inject raw HTML/CSS.
# Think of CSS as the visual style guide for the page.

st.markdown("""
<style>
    /* Import a clean, professional font from Google */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    /* Apply font to everything */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Page background — dark professional tone */
    .stApp {
        background-color: #0f172a;
        color: #e2e8f0;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }

    /* Hero header section */
    .hero-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f4c35 100%);
        border: 1px solid #10b981;
        border-radius: 16px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin: 0;
        font-weight: 400;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(16,185,129,0.15);
        border: 1px solid rgba(16,185,129,0.4);
        color: #10b981;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
        text-transform: uppercase;
    }

    /* Input card */
    .input-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.75rem;
        margin-bottom: 1.5rem;
    }
    .card-title {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #10b981;
        margin-bottom: 1rem;
    }

    /* Result metric boxes */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: border-color 0.2s;
    }
    .metric-card:hover {
        border-color: #10b981;
    }
    .metric-mode {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        font-family: 'DM Mono', monospace;
        line-height: 1;
        margin-bottom: 0.25rem;
    }
    .metric-unit {
        font-size: 0.8rem;
        color: #64748b;
    }
    .metric-value.highlight {
        color: #10b981;
    }
    .metric-value.warning {
        color: #f59e0b;
    }
    .metric-value.danger {
        color: #ef4444;
    }

    /* Formula breakdown box */
    .formula-box {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-left: 3px solid #10b981;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        font-family: 'DM Mono', monospace;
        font-size: 0.82rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }
    .formula-result {
        color: #10b981;
        font-weight: 600;
    }

    /* Section divider */
    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #475569;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .section-label::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #1e293b;
    }

    /* Insight callout */
    .insight-box {
        background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(16,185,129,0.03));
        border: 1px solid rgba(16,185,129,0.25);
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin: 1.5rem 0;
    }
    .insight-label {
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #10b981;
        margin-bottom: 0.4rem;
    }
    .insight-text {
        font-size: 0.95rem;
        color: #cbd5e1;
        line-height: 1.6;
    }
    .insight-text strong {
        color: #f1f5f9;
    }

    /* Streamlit widget overrides */
    .stTextInput > div > div > input {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16,185,129,0.15) !important;
    }
    .stNumberInput > div > div > input {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    .stSelectbox > div > div {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: #10b981 !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.02em !important;
        width: 100%;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #059669 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(16,185,129,0.3) !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: transparent !important;
        border: 1px solid #334155 !important;
        color: #94a3b8 !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        width: 100%;
        transition: all 0.2s !important;
    }
    .stDownloadButton > button:hover {
        border-color: #10b981 !important;
        color: #10b981 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# HERO HEADER
# =============================================================================

st.markdown("""
<div class="hero-header">
    <div class="hero-badge">🌍 GLEC Framework v3.0</div>
    <h1 class="hero-title">European Freight CO₂ Estimator</h1>
    <p class="hero-subtitle">
        Compare carbon emissions across Road FTL, Road LTL, and Air Freight
        using real road distances and published emission factors.
    </p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# LAYOUT — two columns: left for inputs, right for results
# =============================================================================
# st.columns([2, 3]) creates two columns where the right is 1.5x wider
# Think of it as splitting the page into an input panel and a results panel

col_input, col_results = st.columns([2, 3], gap="large")


# =============================================================================
# LEFT COLUMN: INPUT PANEL
# =============================================================================

with col_input:

    st.markdown('<div class="card-title">📦 Shipment Details</div>', unsafe_allow_html=True)

    # City inputs
    origin = st.text_input(
        "Origin City",
        placeholder="e.g. Hamburg",
        help="Any European city. Try: Munich, Lyon, Warsaw, Barcelona"
    )

    destination = st.text_input(
        "Destination City",
        placeholder="e.g. Warsaw",
        help="Any European city."
    )

    # Weight input
    weight_kg = st.number_input(
        "Shipment Weight (kg)",
        min_value    = 1,
        max_value    = 24000,    # max legal payload for a standard European truck
        value        = 5000,
        step         = 100,
        help         = "Max 24,000 kg — standard European FTL payload limit"
    )

    # Shipment type selector — for context, doesn't change the formula
    # (the formula already calculates all three modes simultaneously)
    shipment_type = st.selectbox(
        "Primary Shipment Type",
        options = ["Full Truckload (FTL)", "Groupage / LTL", "Air Freight"],
        help    = "Your actual shipment type — all three modes are always compared"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # The main Calculate button
    # st.button() returns True the moment it is clicked, False otherwise
    calculate_clicked = st.button(
        "⚡ Calculate Emissions",
        type = "primary",
        use_container_width = True,
    )

    # Methodology note under the button
    st.markdown("""
    <div style="margin-top:1.5rem; padding: 1rem; background:#0f172a;
                border-radius:8px; border:1px solid #1e293b;">
        <div style="font-size:0.65rem; font-weight:700; letter-spacing:0.08em;
                    text-transform:uppercase; color:#475569; margin-bottom:0.5rem;">
            Methodology
        </div>
        <div style="font-size:0.78rem; color:#64748b; line-height:1.6;">
            Emission factors from the <strong style="color:#94a3b8;">GLEC Framework v3.0</strong>
            (Smart Freight Centre).<br><br>
            Road distances via <strong style="color:#94a3b8;">OpenRouteService</strong>
            HGV routing profile.<br><br>
            Results are indicative TTW estimates for modal comparison.
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# RIGHT COLUMN: RESULTS PANEL
# =============================================================================

with col_results:

    # This block only runs when the Calculate button has been clicked
    if calculate_clicked:

        # --- Input validation ---
        # Check that the user actually typed something in both city fields
        if not origin or not destination:
            st.error("⚠️ Please enter both an origin and a destination city.")
            st.stop()   # halt execution — nothing below this runs

        if origin.strip().lower() == destination.strip().lower():
            st.error("⚠️ Origin and destination must be different cities.")
            st.stop()

        # --- API call with a loading spinner ---
        # st.spinner() shows an animated spinner while the indented code runs
        # The API call can take 2–4 seconds, so this reassures the user
        with st.spinner("🗺️ Calculating route distance..."):
            try:
                distance_km, resolved_origin, resolved_dest = get_road_distance_km(
                    origin, destination
                )
            except ValueError as e:
                st.error(f"⚠️ {e}")
                st.stop()
            except Exception as e:
                st.error(
                    f"⚠️ Could not reach the routing API. "
                    f"Check your internet connection or API key.\n\n{e}"
                )
                st.stop()

        # --- CO2 calculation (instant — no API needed) ---
        results = calculate_emissions(distance_km, weight_kg)

        # Small pause for UX — lets the spinner feel intentional
        time.sleep(0.3)

        # ---------------------------------------------------------------
        # ROUTE SUMMARY LINE
        # ---------------------------------------------------------------
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:0.75rem;
                    margin-bottom:1.5rem; flex-wrap:wrap;">
            <span style="font-size:1.1rem; font-weight:600; color:#f1f5f9;">
                {resolved_origin}
            </span>
            <span style="color:#10b981; font-size:1.2rem;">→</span>
            <span style="font-size:1.1rem; font-weight:600; color:#f1f5f9;">
                {resolved_dest}
            </span>
            <span style="background:#1e293b; border:1px solid #334155;
                         padding:0.2rem 0.75rem; border-radius:999px;
                         font-size:0.8rem; color:#94a3b8; font-family:'DM Mono',monospace;">
                {distance_km:,.1f} km road distance
            </span>
            <span style="background:#1e293b; border:1px solid #334155;
                         padding:0.2rem 0.75rem; border-radius:999px;
                         font-size:0.8rem; color:#94a3b8;">
                {weight_kg:,.0f} kg
            </span>
        </div>
        """, unsafe_allow_html=True)

        # ---------------------------------------------------------------
        # THREE METRIC CARDS — one per transport mode
        # ---------------------------------------------------------------
        m1, m2, m3 = st.columns(3)

        # Assign colour classes based on relative emissions
        colours = ["highlight", "warning", "danger"]
        icons   = ["🚛", "📦", "✈️"]

        for col, (mode, data), colour, icon in zip(
            [m1, m2, m3], results.items(), colours, icons
        ):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-mode">{icon} {data['label']}</div>
                    <div class="metric-value {colour}">{data['co2_kg']:,.1f}</div>
                    <div class="metric-unit">kg CO₂e</div>
                </div>
                """, unsafe_allow_html=True)

        # ---------------------------------------------------------------
        # BAR CHART — plotly interactive chart
        # ---------------------------------------------------------------
        st.markdown('<div class="section-label">Emissions Comparison</div>',
                    unsafe_allow_html=True)

        # Extract data for the chart
        labels  = [d["label"]  for d in results.values()]
        values  = [d["co2_kg"] for d in results.values()]
        colours_chart = ["#10b981", "#f59e0b", "#ef4444"]

        # Build the plotly figure
        # go.Bar() creates a bar chart trace (one set of bars)
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x           = labels,
            y           = values,
            marker_color = colours_chart,
            text        = [f"{v:,.1f} kg" for v in values],  # labels on bars
            textposition = "outside",
            textfont    = dict(color="#94a3b8", size=11, family="DM Mono"),
            hovertemplate = "<b>%{x}</b><br>CO₂e: %{y:,.1f} kg<extra></extra>",
        ))

        # Style the chart to match the dark theme
        fig.update_layout(
            plot_bgcolor  = "#1e293b",
            paper_bgcolor = "#1e293b",
            font          = dict(color="#94a3b8", family="DM Sans"),
            margin        = dict(t=30, b=10, l=10, r=10),
            height        = 300,
            showlegend    = False,
            xaxis = dict(
                showgrid    = False,
                tickfont    = dict(size=11, color="#94a3b8"),
                linecolor   = "#334155",
            ),
            yaxis = dict(
                showgrid    = True,
                gridcolor   = "#334155",
                tickfont    = dict(size=10, color="#64748b"),
                ticksuffix  = " kg",
                linecolor   = "#334155",
            ),
        )

        # Render the chart in the Streamlit page
        # use_container_width=True makes it fill the column width
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ---------------------------------------------------------------
        # FORMULA BREAKDOWN — shows the calculation for each mode
        # ---------------------------------------------------------------
        st.markdown('<div class="section-label">Formula Breakdown</div>',
                    unsafe_allow_html=True)

        for mode, data in results.items():
            st.markdown(f"""
            <div class="formula-box">
                <strong style="color:#e2e8f0;">{data['label']}</strong><br>
                {distance_km:,.1f} km
                × {data['weight_tonnes']:.3f} t
                × {data['factor']} kg/t·km
                = <span class="formula-result">{data['co2_kg']:,.2f} kg CO₂e</span>
            </div>
            """, unsafe_allow_html=True)

        # ---------------------------------------------------------------
        # KEY INSIGHT CALLOUT
        # ---------------------------------------------------------------
        ftl_co2 = results["road_ftl"]["co2_kg"]
        air_co2 = results["air"]["co2_kg"]
        ltl_co2 = results["road_ltl"]["co2_kg"]
        air_ratio = round(air_co2 / ftl_co2, 1)
        ltl_ratio = round(ltl_co2 / ftl_co2, 1)

        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-label">💡 Key Insight</div>
            <div class="insight-text">
                On this route, air freight emits
                <strong>{air_ratio}× more CO₂e than full truckload</strong>.
                Switching from LTL to FTL would reduce emissions by
                <strong>{((ltl_co2 - ftl_co2)/ltl_co2*100):.0f}%</strong>.
                These factors are increasingly material under
                <strong>CSRD Scope 3 reporting obligations</strong>.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---------------------------------------------------------------
        # PDF DOWNLOAD BUTTON
        # ---------------------------------------------------------------
        st.markdown('<div class="section-label">Export</div>',
                    unsafe_allow_html=True)

        # Generate the PDF bytes — this calls our pdf_export.py module
        pdf_bytes = generate_pdf(
            origin      = resolved_origin,
            destination = resolved_dest,
            weight_kg   = weight_kg,
            distance_km = distance_km,
            results     = results,
        )

        # Build a clean filename: e.g. "co2_Hamburg_Warsaw.pdf"
        filename = (
            f"co2_{resolved_origin.replace(' ','_')}"
            f"_{resolved_dest.replace(' ','_')}.pdf"
        )

        # st.download_button() creates a button that triggers a file download
        # when clicked — no server needed, the bytes go straight to the browser
        st.download_button(
            label     = "📄 Download PDF Report",
            data      = pdf_bytes,
            file_name = filename,
            mime      = "application/pdf",
            use_container_width = True,
        )

    else:
        # ---------------------------------------------------------------
        # PLACEHOLDER STATE — shown before the button is clicked
        # ---------------------------------------------------------------
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center;
                    justify-content:center; height:400px; text-align:center;
                    border:1px dashed #1e293b; border-radius:12px;">
            <div style="font-size:3rem; margin-bottom:1rem;">🚛</div>
            <div style="font-size:1rem; font-weight:600; color:#475569;
                        margin-bottom:0.5rem;">
                Ready to calculate
            </div>
            <div style="font-size:0.85rem; color:#334155; max-width:280px;
                        line-height:1.6;">
                Enter your shipment details on the left and click
                <strong style="color:#64748b;">Calculate Emissions</strong>
                to compare CO₂e across all three transport modes.
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; border-top:1px solid #1e293b;
            margin-top:3rem;">
    <div style="font-size:0.75rem; color:#334155; line-height:2;">
        Emission factors: <strong style="color:#475569;">GLEC Framework v3.0</strong>
        · Smart Freight Centre &nbsp;|&nbsp;
        Routing: <strong style="color:#475569;">OpenRouteService HGV</strong> &nbsp;|&nbsp;
        Results are indicative TTW estimates
    </div>
    <div style="font-size:0.7rem; color:#1e293b; margin-top:0.5rem;">
        Built with Python · Streamlit · Plotly
    </div>
</div>
""", unsafe_allow_html=True)
