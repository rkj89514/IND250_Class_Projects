import requests
import sys

def get_coordinates(city, state):
    """
    Converts City and State to Latitude/Longitude.
    Supports both 2-letter abbreviations and full state names.
    """
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    
    # Dictionary to map abbreviations to full names for reliable API matching
    us_states = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
        'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
        'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
        'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
        'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
        'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }

    # Normalize state input
    state_input = state.strip().upper()
    full_state_name = us_states.get(state_input, state.strip())

    params = {
        "name": city.strip(),
        "count": 20,
        "language": "en",
        "format": "json"
    }

    try:
        response = requests.get(geo_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results")
        if not results:
            return None

        # Filter for the specific State and Country
        for res in results:
            is_us = res.get("country_code") == "US"
            # Match against the full state name (e.g., "Virginia")
            is_state = res.get("admin1", "").lower() == full_state_name.lower()
            
            if is_us and is_state:
                return res
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Network error during location lookup: {e}")
        sys.exit(1)

def get_weather(lat, lon, timezone):
    """Retrieves 10-day forecast in Fahrenheit and Inches."""
    weather_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": timezone,
        "forecast_days": 10
    }

    try:
        response = requests.get(weather_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error during weather retrieval: {e}")
        sys.exit(1)

def main():
    print("--- Weather Forcaster ---")
    
    # Prompt user for input
    city_in = input("Enter the City: ").strip()
    state_in = input("Enter the State: ").strip()

    if not city_in or not state_in:
        print("Error: Both city and state are required.")
        sys.exit(1)

    # 1. Geocoding
    location = get_coordinates(city_in, state_in)

    if not location:
        print(f"Error: Location '{city_in}, {state_in}' not found.")
        sys.exit(1)

    # 2. Extract location details
    lat = location['latitude']
    lon = location['longitude']
    display_city = location.get('name', city_in)
    display_state = location.get('admin1', state_in)
    tz = location.get('timezone', 'auto')

    # 3. Fetch Weather
    forecast = get_weather(lat, lon, tz)
    daily = forecast.get("daily", {})

    # 4. Tabular Output
    print(f"\n10-Day Forecast for: {display_city}, {display_state}")
    print(f"{'Date':<12} | {'Max (°F)':<10} | {'Min (°F)':<10} | {'Precip (in)':<10}")
    print("-" * 52)

    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])

    for i in range(len(dates)):
        print(f"{dates[i]:<12} | {max_temps[i]:>8.1f} | {min_temps[i]:>8.1f} | {precip[i]:>10.2f}")

if __name__ == "__main__":
    main()