# =============================================================================
# calculator.py — CO₂ Emissions Calculator
# =============================================================================
# This file contains the core formula logic for the estimator.
# It has NO dependency on the API or the internet — it just does math.
#
# THE FORMULA (from the GLEC Framework):
#   CO₂e (kg) = distance (km) × weight (tonnes) × emission factor (kg/tonne-km)
#
# Think of it like freight cost calculation:
#   Price = distance × weight × rate_per_tonne_km
#   CO₂   = distance × weight × emissions_per_tonne_km
# =============================================================================

import pandas as pd   # pandas reads our CSV lookup table like a spreadsheet
import os             # os helps us build file paths that work on any computer

# -----------------------------------------------------------------------------
# STEP 1: Load the emission factors from the CSV file
# -----------------------------------------------------------------------------
# os.path.dirname(__file__) means "the folder where THIS file lives" (utils/)
# os.path.join builds a path that works on Mac, Windows, and Linux
# ".." means "go up one folder" — from utils/ up to co2-estimator/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTORS_PATH = os.path.join(BASE_DIR, "data", "glec_factors.csv")

# Read the CSV into a pandas DataFrame (think of it as a small in-memory table)
# Then set the "mode" column as the index so we can look up rows by mode name
factors_df = pd.read_csv(FACTORS_PATH).set_index("mode")


# -----------------------------------------------------------------------------
# STEP 2: Define the main calculation function
# -----------------------------------------------------------------------------
# WHAT IS A FUNCTION?
# A function is like a Standard Operating Procedure (SOP) in a warehouse.
# You write the procedure once, give it a name, and call it whenever needed.
# You pass in inputs (parameters), it does the work, and hands back a result.
#
# WHAT DOES "return" DO?
# "return" is the function handing the result back to whoever called it —
# like a driver returning a signed Proof of Delivery. Without "return",
# the result stays inside the function and disappears.
# -----------------------------------------------------------------------------

def calculate_emissions(distance_km: float, weight_kg: float) -> dict:
    """
    Calculate CO₂e emissions for all three transport modes.

    Parameters:
        distance_km  — road distance between origin and destination
        weight_kg    — shipment weight in kilograms

    Returns:
        A dictionary with results for each transport mode.
        Example: {"road_ftl": {"label": "Road (FTL)", "co2_kg": 15.6, ...}, ...}
    """

    # Convert kg to tonnes — emission factors are per tonne-km, not per kg-km
    # 1 tonne = 1,000 kg, so divide by 1000
    weight_tonnes = weight_kg / 1000

    # This dictionary will hold our results — one entry per transport mode
    results = {}

    # Loop through each row in our GLEC factors table
    # "mode" will be e.g. "road_ftl", "road_ltl", "air"
    # "row" will contain the label, factor, and description for that mode
    for mode, row in factors_df.iterrows():

        # THE CORE FORMULA — this is the heart of the entire application
        factor = row["factor_kg_per_tonne_km"]
        co2_kg = distance_km * weight_tonnes * factor

        # Store the result for this mode in our results dictionary
        results[mode] = {
            "label":      row["label"],           # Human-readable name
            "co2_kg":     round(co2_kg, 2),       # Rounded to 2 decimal places
            "distance_km": distance_km,
            "weight_kg":  weight_kg,
            "weight_tonnes": round(weight_tonnes, 4),
            "factor":     factor,                 # The GLEC emission factor used
            "description": row["description"],    # Mode description from CSV
        }

    return results  # Hand the completed results dictionary back to the caller


# -----------------------------------------------------------------------------
# STEP 3: Test block — only runs when you execute THIS file directly
# -----------------------------------------------------------------------------
# "if __name__ == '__main__'" is Python's way of saying:
# "Only run this block if someone runs THIS file directly (not when it's
#  imported by another file like app.py)."
# It's like a test shipment — you run it to verify before going live.
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    # --- Hardcoded test values ---
    TEST_DISTANCE_KM = 500    # e.g. approximate Munich → Paris road distance
    TEST_WEIGHT_KG   = 5000   # 5 tonnes — a typical LTL shipment

    print("=" * 55)
    print("  European Freight CO₂ Estimator — Formula Test")
    print("=" * 55)
    print(f"  Distance : {TEST_DISTANCE_KM} km")
    print(f"  Weight   : {TEST_WEIGHT_KG} kg ({TEST_WEIGHT_KG/1000} tonnes)")
    print("=" * 55)

    # Call our function with the test values
    results = calculate_emissions(TEST_DISTANCE_KM, TEST_WEIGHT_KG)

    # Print each mode's result in a readable format
    for mode, data in results.items():
        print(f"\n  [{data['label']}]")
        print(f"    Formula : {TEST_DISTANCE_KM} km"
              f" × {data['weight_tonnes']} t"
              f" × {data['factor']} kg/t-km")
        print(f"    CO₂e    : {data['co2_kg']} kg")

    print("\n" + "=" * 55)
    print("  ✓ If you see three results above, the formula works.")
    print("=" * 55)
