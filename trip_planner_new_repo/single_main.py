import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from fastapi.staticfiles import StaticFiles  # Import StaticFiles


# Import the consolidated agent and utility agents
from single_trip_agent import plan_full_trip_agent, convert_currency_agent

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Trip Planner Backend",
    description="API for comprehensive trip planning, currency conversion, and weather.",
    version="1.0.0",
)

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:3000", # Default port for React development server
    "http://localhost:5173", # Common port for Vite React development server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Request Body Validation ---
class TripPlanRequest(BaseModel): # Renamed for clarity
    destination: str = Field(..., min_length=1, description="The desired travel destination.")
    dates: str = Field(..., min_length=1, description="Travel dates (e.g., 'Dec 1-7, 2025').")
    preferences: Optional[str] = Field(None, description="Optional preferences for the trip.")

class CurrencyConvertRequest(BaseModel):
    amount: float = Field(..., gt=0, description="The amount to convert.")
    from_currency: str = Field(..., min_length=3, max_length=3, description="The currency code to convert from (e.g., 'USD').")
    to_currency: str = Field(..., min_length=3, max_length=3, description="The currency code to convert to (e.g., 'EUR').")


# --- API Endpoints ---

# New: Full Trip Planning Endpoint
@app.post("/api/plan-full-trip")
async def plan_full_trip(request: TripPlanRequest) -> Dict[str, Any]:
    """
    Plans a comprehensive trip including hotels, restaurants, and a daily itinerary.
    """
    try:
        full_trip_info = plan_full_trip_agent(
            request.destination,
            request.dates,
            request.preferences
        )
        # Check if the agent returned an error dictionary
        if isinstance(full_trip_info, dict) and "error" in full_trip_info:
            raise HTTPException(status_code=500, detail=full_trip_info["error"])

        return {"data": full_trip_info} # This will now be a comprehensive JSON object
    except HTTPException as e:
        raise e # Re-raise FastAPI's HTTPException
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to plan full trip: {e}")

# Keep utility endpoints
@app.post("/api/convert-currency")
async def convert_currency(request: CurrencyConvertRequest):
    try:
        converted_result = convert_currency_agent(
            request.amount,
            request.from_currency,
            request.to_currency
        )
        return {"data": converted_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Currency conversion failed: {e}")



app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
