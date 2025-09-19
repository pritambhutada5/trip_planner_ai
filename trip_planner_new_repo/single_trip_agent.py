from dotenv import load_dotenv
import requests
import json
import os
from typing import Optional, Dict, Any, List

load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Currency Exchange API Configuration
EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/"


# --- Helper Function for Gemini API Calls ---
def call_gemini_api(prompt: str, response_schema: Optional[dict] = None) -> Any:
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
            if response_schema:
                try:
                    return json.loads(result["candidates"][0]["content"]["parts"][0]["text"])
                except json.JSONDecodeError:
                    print(f"JSON Decode Error: {result['candidates'][0]['content']['parts'][0]['text']}")
                    return {"error": "Failed to parse JSON response from AI. Check AI output format."}
            else:
                return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return {"error": "No content found in the AI response."}
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        return {"error": f"Could not retrieve information from AI. Details: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred. Details: {e}"}

# --- Consolidated Full Trip Planning Agent ---
def plan_full_trip_agent(destination: str, dates: str, preferences: str = "") -> Dict[str, Any]:
    """
    Agent to plan a full trip, including hotels, restaurants, and tourist spots,
    returning structured JSON with verified absolute map links.
    """
    if not destination or not dates:
        return {"error": "Please provide destination and dates to plan the trip."}

    # Define the comprehensive JSON schema for the full trip plan
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "hotels": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "description": {"type": "STRING"},
                        "price_range": {"type": "STRING"},
                        "map_link": {"type": "STRING", "description": "Full Google Maps search link"}
                    },
                    "required": ["name", "description", "map_link"]
                }
            },
            "restaurants": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "cuisine": {"type": "STRING"},
                        "recommendation_reason": {"type": "STRING"},
                        "map_link": {"type": "STRING", "description": "Full Google Maps search link"}
                    },
                    "required": ["name", "cuisine", "recommendation_reason", "map_link"]
                }
            },
            "itinerary": {
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
        },
        "required": ["hotels", "restaurants", "itinerary"]
    }

    # Comprehensive prompt for the full trip plan
    prompt = (f"Plan a complete trip to {destination} for dates {dates}. "
              f"Consider these preferences: {preferences if preferences else 'any'}. "
              f"Provide the output as a JSON object with three top-level keys: 'hotels', 'restaurants', and 'itinerary'.\n\n"
              f"For 'hotels', suggest 3 highly-rated hotels. Include name, description, approximate price range, and a full, absolute Google Maps search clickable links which will directly open google maps and point to particular hotels \n\n"
              f"For 'restaurants', suggest 3 popular restaurants. Include name, cuisine type, a brief reason for recommendation, anda full, absolute Google Maps search clickable links which will directly open google maps and point to particular restaurants \n\n"
              f"For 'itinerary', plan a day-by-day itinerary. Each day should have a 'day' (integer), 'date' (string), and an 'activities' array. Each activity should have a 'name', 'description', and a 'map_link' and a full, absolute Google Maps search clickable links which will directly open google maps and point to particular spots "
              f"Ensure all map_links are full, absolute Google Maps search URLs that will directly open Google Maps and point to the particular location.")

    full_trip_info = call_gemini_api(prompt, response_schema=response_schema)

    return full_trip_info

# --- Utility Agents (kept separate as they are not part of the core trip plan) ---

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
    print("--- Testing Full Trip Agent ---")
    full_trip_info = plan_full_trip_agent("Kyoto, Japan", "Oct 10-15, 2025", "historical, nature, luxury")
    print(json.dumps(full_trip_info, indent=2))
    print("\n" + "="*50 + "\n")

    print("--- Testing Currency Converter Agent ---")
    converted_value = convert_currency_agent(100, "USD", "EUR")
    print(converted_value)
    print("\n" + "="*50 + "\n")

