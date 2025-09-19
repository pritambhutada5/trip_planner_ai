from dotenv import load_dotenv
import requests
import json
import os
from typing import Optional, Dict, Any

load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# New: Currency Exchange API Configuration
EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/"


# --- Helper Function for Gemini API Calls ---
def call_gemini_api(prompt: str, response_schema: Optional[dict] = None) -> str:
    """
    Calls the Gemini API with a given prompt and returns the generated text or JSON.
    """
    headers = {
        "Content-Type": "application/json",
    }
    params = {
        "key": GEMINI_API_KEY
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    if response_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        if result and "candidates" in result and len(result["candidates"]) > 0 and \
           "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"] and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            # If a schema was provided, the response will be a JSON string. Parse it.
            if response_schema:
                try:
                    return json.loads(result["candidates"][0]["content"]["parts"][0]["text"])
                except json.JSONDecodeError:
                    return {"error": "Failed to parse JSON response from AI."}
            else:
                return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "No content found in the API response."
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        return {"error": f"Could not retrieve information. Details: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred. Details: {e}"}

# --- Agent Functions ---

def find_hotels_agent(destination: str, dates: str, preferences: str = "") -> str:
    """
    Agent to find hotel recommendations, ensuring direct and absolute Google Maps search links.
    """
    if not destination or not dates:
        return "Please provide destination and dates to find hotels."
    prompt = (f"Find 3 highly-rated hotels in {destination} for {dates}. Consider these preferences: {preferences if preferences else 'any'}. For each hotel, provide its name, a brief description, approximate price range, and "
              f"a full, absolute Google Maps search clickable links which will directly open google maps and point to particular hotels ")
    return call_gemini_api(prompt)

def find_restaurants_agent(destination: str, preferences: str = "") -> str:
    """
    Agent to find restaurant recommendations, ensuring direct and absolute Google Maps search links.
    """
    if not destination:
        return "Please provide a destination to find restaurants."
    prompt = (f"Suggest 3 popular restaurants in {destination}. Consider these preferences: {preferences if preferences else 'any'}. For each restaurant, provide its name, cuisine type, a brief reason for recommendation, and "
              f"a full, absolute Google Maps search clickable links which will directly open google maps and point to particular restaurants")
    return call_gemini_api(prompt)

def plan_tourist_spots_agent(destination: str, dates: str, preferences: str = "") -> dict:
    """
    Agent to plan tourist spots itinerary, requesting structured JSON output.
    """
    if not destination or not dates:
        return {"error": "Please provide destination and dates to plan tourist spots."}

    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "day": {"type": "INTEGER"},
                "date": {"type": "STRING"},
                "activities": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "time": {"type": "STRING", "description": "Optional time for the activity"},
                            "name": {"type": "STRING", "description": "Name of the tourist spot or activity"},
                            "description": {"type": "STRING", "description": "Brief description of the activity"},
                            "map_link": {"type": "STRING", "description": "Full Google Maps search link"}
                        },
                        "required": ["name", "description", "map_link"]
                    }
                }
            },
            "required": ["day", "date", "activities"]
        }
    }

    prompt = (f"Plan a itinerary for tourist spots in {destination} for dates {dates}. Consider these preferences: {preferences if preferences else 'any'}. For each spot, include a mix of activities, brief descriptions, and "
              f"a full absolute Google Maps search link which are clickable and once i click those it should point to particular destination point.")

    return call_gemini_api(prompt, response_schema=response_schema)

def convert_currency_agent(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Agent to convert currency using an external API.
    """
    if not isinstance(amount, (int, float)) or amount <= 0:
        return "Please provide a valid positive amount for currency conversion."
    if not from_currency or not to_currency:
        return "Please provide both 'from' and 'to' currencies."

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    try:
        response = requests.get(f"{EXCHANGE_RATE_API_URL}{from_currency}")
        response.raise_for_status()
        data = response.json()

        if data and data.get("rates"):
            rates = data["rates"]
            if from_currency not in rates:
                return f"Error: '{from_currency}' is not a valid currency code or exchange rate not found."
            if to_currency not in rates:
                return f"Error: '{to_currency}' is not a valid currency code or exchange rate not found."

            rate_from_to_usd = rates.get(to_currency) / rates.get(from_currency)
            converted_amount = amount * rate_from_to_usd

            return f"{amount:.2f} {from_currency} is approximately {converted_amount:.2f} {to_currency}."
        else:
            return "Error: Could not retrieve exchange rates from the API."
    except requests.exceptions.RequestException as e:
        print(f"Error calling currency API: {e}")
        return f"Error: Failed to fetch exchange rates. Details: {e}"
    except Exception as e:
        print(f"An unexpected error occurred during currency conversion: {e}")
        return f"Error: An unexpected error occurred. Details: {e}"


# --- Example Usage (for testing the Python functions directly) ---
if __name__ == "__main__":
    print("--- Testing Hotel Agent ---")
    hotel_info = find_hotels_agent("Kyoto, Japan", "Oct 10-15, 2025", "luxury, near temples")
    print(hotel_info)
    print("\n" + "="*50 + "\n")

    print("--- Testing Restaurant Agent ---")
    restaurant_info = find_restaurants_agent("Kyoto, Japan", "traditional Japanese, vegan options")
    print(restaurant_info)
    print("\n" + "="*50 + "\n")

    print("--- Testing Tourist Spot Agent ---")
    tourist_spot_info = plan_tourist_spots_agent("Kyoto, Japan", "Oct 10-15, 2025", "historical, nature")
    print(json.dumps(tourist_spot_info, indent=2))
    print("\n" + "="*50 + "\n")

    print("--- Testing Currency Converter Agent ---")
    converted_value = convert_currency_agent(100, "USD", "EUR")
    print(converted_value)
    print("\n" + "="*50 + "\n")


