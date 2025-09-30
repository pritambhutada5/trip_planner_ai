import logging
import json
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Import our centralized logging configuration
# This only needs to be configured once at the app entry point (main.py)
# but we get the logger instance in each module.
logger = logging.getLogger(__name__)

load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/"

# --- Load the Vector Store on Application Startup ---
logger.info("Initializing embedding model...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
logger.info("Loading FAISS vector store from 'faiss_store'...")
try:
    vector_db = FAISS.load_local("faiss_store", embeddings, allow_dangerous_deserialization=True)
    logger.info("FAISS vector store loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load FAISS vector store: {e}", exc_info=True)
    vector_db = None  # Ensure vector_db is None if loading fails


def get_context_with_sources(query: str, db: FAISS):
    """Retrieves context and sources based on a similarity search."""
    if not db:
        logger.warning("Vector store not available. Skipping RAG retrieval.")
        return "", []

    retrieved_docs_with_scores = db.similarity_search_with_relevance_scores(query, k=3)

    context = ""
    sources = set()
    RELEVANCE_THRESHOLD = 0.4

    logger.debug("--- RAG Retrieval Scores ---")
    for doc, score in retrieved_docs_with_scores:
        logger.debug(f"Retrieved '{doc.metadata.get('source')}' with score: {score:.4f}")
        if score > RELEVANCE_THRESHOLD:
            context += doc.page_content + "\n\n---\n\n"
            sources.add(doc.metadata['source'])
    logger.debug("--- End of RAG Scores ---")

    if sources:
        logger.info(f"RAG retrieval found {len(sources)} relevant source(s).")
    else:
        logger.info("No relevant context found above the similarity threshold.")

    return context, list(sources)


def call_gemini_api(prompt: str, response_schema: Optional[dict] = None) -> Any:
    """Calls the Gemini API and handles response parsing."""
    logger.info("Calling Gemini API...")
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    if response_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        logger.info("Successfully received response from Gemini API.")

        if result.get("candidates"):
            parts = result["candidates"][0].get("content", {}).get("parts", [{}])
            text_content = parts[0].get("text", "")
            if response_schema:
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response from AI. Raw text: {text_content}")
                    return {"error": "Failed to parse JSON response from AI."}
            else:
                return text_content
        else:
            logger.warning("No candidates found in the AI response.")
            return {"error": "No content found in the AI response."}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        return {"error": f"Could not retrieve information from AI. Details: {e}"}
    except Exception as e:
        logger.error(f"An unexpected error occurred in call_gemini_api: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred. Details: {e}"}


def sanitize_map_link(url: str) -> str:
    """Cleans up a URL that might contain erroneous Markdown link formatting."""
    match = re.search(r'\[.*?\]\((https?://.*?)\)', url)
    if match:
        clean_url = match.group(1)
        logger.debug(f"Sanitized URL: '{url}' -> '{clean_url}'")
        return clean_url
    return url


def plan_full_trip_agent(destination: str, from_date: str, to_date: str, preferences: str = "") -> Dict[str, Any]:
    """
    Agent to plan a full trip, including hotels, restaurants, and tourist spots,
    returning structured JSON with verified absolute map links.
    """
    logger.info(f"Starting full trip plan for destination: '{destination}'")
    if not all([destination, from_date, to_date]):
        return {"error": "Please provide destination, from_date, and to_date."}

    try:
        start_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
        num_days = (end_date_obj - start_date_obj).days + 1
        date_list = [(start_date_obj + timedelta(days=i)).strftime("%b %d, %Y") for i in range((end_date_obj - start_date_obj).days + 1)]
    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}

    # --- RAG Step 1: Retrieve Context and Sources ---
    rag_query = f"Provide a detailed travel itinerary for {destination} with a focus on {preferences}."
    retrieved_context, retrieved_sources = get_context_with_sources(rag_query, vector_db)
    logger.debug("\n" + "="*20 + " RETRIEVED CONTEXT " + "="*20)
    logger.debug(retrieved_context, retrieved_sources)
    logger.debug("="*60 + "\n")
    logger.info("Context retrieved successfully.")

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
            },
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of source documents used to generate the plan."
            }
        },
        "required": ["hotels", "restaurants", "itinerary", "sources"]
    }

    if retrieved_context and retrieved_sources:
        # PATH 1: RAG-AUGMENTED PROMPT ---
        formatted_sources = ", ".join(retrieved_sources)
        prompt = f"""
        You are an expert travel planner. You MUST generate a trip plan based ONLY on the provided context.
        **Context:**
        ---
        {retrieved_context}
        ---
        **Source Filenames:** {formatted_sources}
        **Instructions:**
        1. Generate a detailed trip plan for the user's request.
        2. Your response MUST be a single, valid JSON object that strictly adheres to the required schema.
        3. The "sources" field in your JSON output MUST contain ONLY the exact filenames listed in "Source Filenames" above. Do not invent or use any other sources.
        4.  f"Provide the output as a JSON object with three top-level keys: 'hotels', 'restaurants', and 'itinerary'.\n\n"
          f"For 'hotels', suggest 3 highly-rated hotels. Include name, description, approximate price range, and a full, absolute Google Maps search clickable links which will directly open google maps and point to particular hotels \n\n"
          f"For 'restaurants', suggest 3 popular restaurants. Include name, cuisine type, a brief reason for recommendation, anda full, absolute Google Maps search clickable links which will directly open google maps and point to particular restaurants \n\n"
          f"For 'itinerary', plan a day-by-day itinerary. Each day should have a 'day' (integer), 'date' (string), and an 'activities' array. Each activity should have a 'name', 'description', and a 'map_link' and a full, absolute Google Maps search clickable links which will directly open google maps and point to particular spots "
          f"Ensure all map_links are full, absolute Google Maps search URLs that will directly open Google Maps and point to the particular location.")
        """
    else:
        # --- PATH 2: GENERAL KNOWLEDGE PROMPT (with precise dates) ---
        logger.info("INFO: No relevant context found. Using general knowledge.")
        prompt = f"""
        You are an expert travel planner. You have NO relevant documents.
        You MUST IGNORE any previous context and generate a BRAND NEW trip plan from scratch...
        **User's Request to Fulfill:**
        - Destination: {destination}
        - Dates: The trip will cover these exact dates: {', '.join(date_list)}.
        - Preferences: {preferences if preferences else 'any'}
        **Instructions:**
        1. Generate a detailed trip plan for the specified destination covering the exact dates provided.
        2. Your response MUST be a single, valid JSON object...
        3. For each day in the itinerary, you MUST use the corresponding date from the provided list for the 'date' field.
        4. The "sources" field... MUST be an empty array [].
        5.  f"Provide the output as a JSON object with three top-level keys: 'hotels', 'restaurants', and 'itinerary'.\n\n"
              f"For 'hotels', suggest 5 highly-rated hotels. Include name, description, approximate price range, and a full, absolute Google Maps search clickable links which will directly open google maps and point to particular hotels \n\n"
              f"For 'restaurants', suggest 5 popular restaurants. Include name, cuisine type, a brief reason for recommendation, anda full, absolute Google Maps search clickable links which will directly open google maps and point to particular restaurants \n\n"
              f"For 'itinerary', plan a day-by-day itinerary. Each day should have a 'day' (integer), 'date' (string), and an 'activities' array. Each activity should have a 'name', 'description', and a 'map_link' and a full, absolute Google Maps search clickable links which will directly open google maps and point to particular spots "
              f"Ensure all map_links are full, absolute Google Maps search URLs that will directly open Google Maps and point to the particular location.")
        """

    full_trip_info = call_gemini_api(prompt, response_schema=response_schema)

    if isinstance(full_trip_info, dict) and "error" in full_trip_info:
        logger.error(f"ERROR from call_gemini_api: {full_trip_info['error']}")
        return full_trip_info

    logger.info("Sanitizing map links in the generated plan...")
    for section in ["hotels", "restaurants"]:
        if section in full_trip_info:
            for item in full_trip_info[section]:
                if "map_link" in item:
                    item["map_link"] = sanitize_map_link(item["map_link"])

    if "itinerary" in full_trip_info:
        for day_plan in full_trip_info["itinerary"]:
            for activity in day_plan.get("activities", []):
                if "map_link" in activity:
                    activity["map_link"] = sanitize_map_link(activity["map_link"])


    # 2. Check if the response is valid and contains the essential data
    if not full_trip_info or not full_trip_info.get("itinerary"):
        print(f"ERROR: API response for {destination} was invalid or missing itinerary.")
        # Return a structured error that the frontend can display
        return {
            "error": f"Could not generate a valid trip plan for {destination}. The AI may not have information on this location or failed to generate a response."}

    itinerary_from_llm = full_trip_info.get("itinerary", [])
    trimmed_itinerary = itinerary_from_llm[:num_days]

    for i, day_plan in enumerate(trimmed_itinerary):
        day_plan['date'] = date_list[i]
        day_plan['day'] = i + 1 # Also correct the day number

    # Assign the corrected itinerary back to the main object
    full_trip_info['itinerary'] = trimmed_itinerary

    # 3. If all checks pass, return the complete plan
    logger.info(f"Successfully generated and finalized trip plan for '{destination}'.")
    return full_trip_info


def convert_currency_agent(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Agent to convert currency using an external API.
    """
    logger.info(f"Starting currency conversion for {amount} {from_currency} to {to_currency}")
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
            logger.info("Successfully converted currency.")
            return f"{amount:.2f} {from_currency} is approximately {converted_amount:.2f} {to_currency}."
        else:
            return "Error: Could not retrieve exchange rates from the API."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling currency API: {e}", exc_info=True)
        return f"Error: Failed to fetch exchange rates. Details: {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred during currency conversion: {e}", exc_info=True)
        return f"Error: An unexpected error occurred. Details: {e}"


if __name__ == "__main__":
    from logging_config import setup_logging
    setup_logging() # Setup logging when running file directly

    logger.info("--- Testing Full Trip Agent ---")
    test_plan = plan_full_trip_agent("Kyoto, Japan", "2025-10-10", "2025-10-15", "historical, nature, luxury")
    logger.info(json.dumps(test_plan, indent=2))

    logger.info("\n--- Testing Currency Converter Agent ---")
    test_conversion = convert_currency_agent(100, "USD", "EUR")
    logger.info(test_conversion)
