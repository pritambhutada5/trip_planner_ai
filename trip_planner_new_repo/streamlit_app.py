import streamlit as st
import requests
from datetime import date
import os

API_URL = os.getenv("API_URL", "http://backend:8000/api/plan-full-trip")

# Set the page configuration
st.set_page_config(page_title="AI Trip Planner", layout="wide", initial_sidebar_state="expanded")

# --- CSS for the Professional Dark Theme ---
st.markdown("""
<style>
    /* Main body to match the dark theme */
    body { color: #fafafa; }
    h1, h2 { color: #20c997; }

    /* Styling for the main section expanders */
    div[data-testid="stExpander"] {
        background-color: #1c2833 !important;
        border-radius: 15px !important;
        border: 1px solid #292f36 !important;
        box-shadow: 0 4px 20px rgba(32, 201, 151, 0.2) !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stExpander"] > div[role="button"] {
        padding: 15px !important;
    }

    /* Text inside expanders */
    div[data-testid="stExpander"] p, div[data-testid="stExpander"] b {
        color: #d1d5db;
    }

    /* Links */
    .link { color: #48dbfb; font-weight: 600; text-decoration: none; }
    .link:hover { color: #0abde3; text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

st.title("✨ AI Trip Planner")
st.markdown("Your intelligent guide to creating the perfect itinerary.")

# --- Sidebar for User Inputs ---
with st.sidebar:
    st.header("Plan Your Next Adventure")
    destination = st.text_input("Destination", placeholder="E.g., Tokyo, Paris")
    from_date = st.date_input("From Date", value=date.today())
    to_date = st.date_input("To Date", value=date.today())
    preferences = st.text_area("Preferences", placeholder="E.g., family-friendly, museums, nightlife", height=100)
    plan_button = st.button("Generate Itinerary")

# --- Main Display Area ---
if plan_button:
    if not destination or not from_date or not to_date:
        st.sidebar.error("Please provide a destination and both start and end dates.")
    elif from_date > to_date:
        st.sidebar.error("The 'From Date' cannot be after the 'To Date'.")
    else:
        with st.spinner("🎨 Designing your custom itinerary..."):
            payload = {"destination": destination, "from_date": from_date.strftime("%Y-%m-%d"),
                       "to_date": to_date.strftime("%Y-%m-%d"), "preferences": preferences}
            try:
                response = requests.post(API_URL, json=payload, timeout=300)
                if response.status_code == 200:
                    response_data = response.json()
                    plan = response_data.get("data", {})
                    if "error" in plan:
                        st.error(plan["error"])
                    else:
                        # --- Main Sections using Expanders ---

                        # --- HOTELS: Nested Expander Layout ---
                        with st.expander("🏨 Hotels", expanded=True):
                            if plan.get("hotels"):
                                for i, hotel in enumerate(plan.get("hotels", []), 1):
                                    with st.expander(f"{i}. {hotel.get('name')}"):
                                        st.markdown(f"<p>{hotel.get('description')}</p>", unsafe_allow_html=True)
                                        st.markdown(f"<p><b>Price Range:</b> {hotel.get('price_range')}</p>",
                                                    unsafe_allow_html=True)
                                        st.markdown(
                                            f"<p><a href='{hotel.get('map_link')}' class='link' target='_blank'>View on Map</a></p>",
                                            unsafe_allow_html=True)
                            else:
                                st.write("No hotel recommendations available.")

                        # --- RESTAURANTS: Nested Expander Layout ---
                        with st.expander("🍽️ Restaurants", expanded=True):
                            if plan.get("restaurants"):
                                for i, rest in enumerate(plan.get("restaurants", []), 1):
                                    with st.expander(f"{i}. {rest.get('name')}"):
                                        st.markdown(f"<p><b>Cuisine:</b> {rest.get('cuisine')}</p>",
                                                    unsafe_allow_html=True)
                                        st.markdown(
                                            f"<p>{rest.get('recommendation_reason', rest.get('description', ''))}</p>",
                                            unsafe_allow_html=True)
                                        st.markdown(
                                            f"<p><a href='{rest.get('map_link')}' class='link' target='_blank'>View on Map</a></p>",
                                            unsafe_allow_html=True)
                            else:
                                st.write("No restaurant recommendations available.")

                        # --- Itinerary Section ---
                        with st.expander("📅 Itinerary", expanded=True):
                            if plan.get("itinerary"):
                                for day_plan in plan.get("itinerary", []):
                                    with st.expander(f"**Day {day_plan.get('day', '')} - {day_plan.get('date', '')}**",
                                                     expanded=True):
                                        for i, activity in enumerate(day_plan.get("activities", []), 1):
                                            st.markdown(f"**{i}. {activity.get('name', '')}**")
                                            st.write(activity.get('description', ''))
                                            st.markdown(
                                                f"<p><a href='{activity.get('map_link', '#')}' class='link' target='_blank'>View on Map</a><p>",
                                                unsafe_allow_html=True)
                                            if i < len(day_plan.get("activities", [])):
                                                st.markdown(
                                                    "<hr style='margin-top:10px; margin-bottom:10px; border-color: #262730;'>",
                                                    unsafe_allow_html=True)
                            else:
                                st.write("No itinerary available.")

                        # --- Sources Section ---
                        sources = plan.get("sources", [])
                        if sources:
                            with st.expander("📚 Sources", expanded=False):
                                source_text = " | ".join(sources)
                                st.info(f"This plan was generated using information from: **{source_text}**")
                else:
                    st.error(
                        f"Failed to get a response from the planner. Error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the AI Trip Planner backend. Please ensure it is running. Details: {e}")
