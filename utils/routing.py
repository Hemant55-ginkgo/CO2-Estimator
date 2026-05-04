# =============================================================================
# routing.py — Road Distance via OpenRouteService API
# =============================================================================
# This file does one job: take two city names, ask the OpenRouteService API
# for the real road distance between them, and return that distance in km.
#
# It works in three stages:
#   1. Convert city names → GPS coordinates (geocoding)
#   2. Send those coordinates to the routing engine
#   3. Extract the distance in km from the JSON response
# =============================================================================

import requests                        # sends HTTP requests (like a browser does)
import os                              # reads environment variables
from dotenv import load_dotenv         # loads our .env file into environment variables

# Load the .env file so Python can read ORS_API_KEY
# This must happen before we try to read the key
load_dotenv()


# -----------------------------------------------------------------------------
# CONSTANTS — fixed values used throughout this file
# -----------------------------------------------------------------------------

# The base URL for all OpenRouteService API calls
ORS_BASE = "https://api.openrouteservice.org"

# Read the API key from the .env file (never hardcode it here!)
API_KEY = os.getenv("ORS_API_KEY")


# -----------------------------------------------------------------------------
# FUNCTION 1: Convert a city name to GPS coordinates
# -----------------------------------------------------------------------------
# The routing API doesn't understand "Munich" — it needs numbers like
# (48.1351, 11.5820). This function does that translation.
# In logistics terms: this is like converting a city name to a locode.
# -----------------------------------------------------------------------------

def geocode_city(city_name: str) -> tuple[float, float]:
    """
    Convert a European city name to (longitude, latitude) coordinates.

    Parameters:
        city_name — e.g. "Munich" or "Paris"

    Returns:
        A tuple of (longitude, latitude) — note: ORS wants longitude FIRST
        e.g. (11.5820, 48.1351) for Munich

    Raises:
        ValueError if the city can't be found
    """

    # Build the geocoding API endpoint URL
    url = f"{ORS_BASE}/geocode/search"

    # These are the query parameters sent with the request
    # Think of them as fields on a booking form
    params = {
        "api_key":          API_KEY,
        "text":             city_name,      # the city we're searching for
        "boundary.country": "AT,BE,BG,CH,CY,CZ,DE,DK,EE,ES,FI,FR,GB,GR,"
                            "HR,HU,IE,IT,LT,LU,LV,MT,NL,NO,PL,PT,RO,SE,"
                            "SI,SK,TR",     # restrict to European countries
        "size":             1,              # only return the top result
    }

    # Make the API call — this is like sending a query to a tracking portal
    response = requests.get(url, params=params, timeout=10)

    # If the server returned an error code (4xx, 5xx), raise an exception
    response.raise_for_status()

    # Parse the JSON response into a Python dictionary
    data = response.json()

    # Navigate the nested "filing cabinet" to find the coordinates
    # Structure: data → "features" → first item → "geometry" → "coordinates"
    # Coordinates come back as [longitude, latitude]
    features = data.get("features", [])

    if not features:
        raise ValueError(
            f"City '{city_name}' not found. "
            "Try a different spelling or add the country (e.g. 'Lyon, France')."
        )

    coordinates = features[0]["geometry"]["coordinates"]
    # coordinates = [longitude, latitude]  ← ORS uses this order

    return coordinates[0], coordinates[1]   # return as (longitude, latitude)


# -----------------------------------------------------------------------------
# FUNCTION 2: Get the road distance between two cities
# -----------------------------------------------------------------------------
# This is the main function the rest of the app will call.
# It uses geocode_city() internally — the app never needs to think about
# coordinates, it just passes city names.
# -----------------------------------------------------------------------------

def get_road_distance_km(origin: str, destination: str) -> tuple[float, str, str]:
    """
    Get the real road distance in km between two European cities.

    Parameters:
        origin      — departure city name, e.g. "Hamburg"
        destination — arrival city name, e.g. "Warsaw"

    Returns:
        A tuple of (distance_km, resolved_origin, resolved_destination)
        distance_km is a float rounded to 1 decimal place
        resolved names confirm what the API actually found

    Raises:
        ValueError if either city can't be geocoded
        requests.RequestException if the API call fails
    """

    if not API_KEY or API_KEY == "your_api_key_here":
        raise ValueError(
            "No API key found. Open your .env file and add your "
            "OpenRouteService key as ORS_API_KEY=your_key_here"
        )

    # --- Stage 1: Convert city names to coordinates ---
    origin_lon, origin_lat           = geocode_city(origin)
    destination_lon, destination_lat = geocode_city(destination)

    # --- Stage 2: Call the routing API with those coordinates ---
    url = f"{ORS_BASE}/v2/directions/driving-hgv"
    # We use "driving-hgv" (Heavy Goods Vehicle) profile — more accurate
    # for freight than the standard car routing profile

    # The request body — sent as JSON in the POST request
    # ORS wants coordinates as [[lon, lat], [lon, lat]]
    body = {
        "coordinates": [
            [origin_lon,      origin_lat],
            [destination_lon, destination_lat],
        ]
    }

    headers = {
        "Authorization": API_KEY,
        "Content-Type":  "application/json",
    }

    response = requests.post(url, json=body, headers=headers, timeout=15)
    response.raise_for_status()

    # --- Stage 3: Extract the distance from the nested JSON response ---
    # The filing cabinet structure:
    #   data
    #   └── "routes"          ← list of route options
    #        └── [0]          ← we take the first (best) route
    #             └── "summary"
    #                  └── "distance"  ← distance in METRES
    data = response.json()

    distance_metres = data["routes"][0]["summary"]["distance"]

    # Convert metres → kilometres and round to 1 decimal
    distance_km = round(distance_metres / 1000, 1)

    return distance_km, origin, destination


# -----------------------------------------------------------------------------
# TEST BLOCK — run this file directly to verify your API key works
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    # Test route: Munich → Paris (should be roughly 1,050–1,100 km by road)
    TEST_ORIGIN      = "Munich"
    TEST_DESTINATION = "Paris"

    print("=" * 55)
    print("  Routing Module — API Connection Test")
    print("=" * 55)
    print(f"  Testing route: {TEST_ORIGIN} → {TEST_DESTINATION}")
    print("  Calling OpenRouteService API...")
    print()

    try:
        km, origin, dest = get_road_distance_km(TEST_ORIGIN, TEST_DESTINATION)
        print(f"  ✓ Success!")
        print(f"  Road distance: {km} km")
        print(f"  (Expected: roughly 1,050–1,100 km)")

    except ValueError as e:
        # This catches our custom errors (city not found, missing API key)
        print(f"  ✗ Error: {e}")

    except requests.exceptions.HTTPError as e:
        # This catches API errors — most likely a bad API key
        print(f"  ✗ API Error: {e}")
        print("  → Double-check your ORS_API_KEY in the .env file")

    except requests.exceptions.ConnectionError:
        print("  ✗ No internet connection — check your network")

    print("=" * 55)
