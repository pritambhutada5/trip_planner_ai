# api_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

# Import your agent functions
from single_trip_agent import plan_full_trip_agent, convert_currency_agent

# Create a router instance
router = APIRouter()

# --- Pydantic Models ---
class TripPlanRequest(BaseModel):
    destination: str = Field(..., min_length=1)
    dates: str = Field(..., min_length=1)
    preferences: Optional[str] = None

class CurrencyConvertRequest(BaseModel):
    amount: float = Field(..., gt=0)
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)

# --- API Endpoints ---
# Note: The paths are now relative to the router's prefix ("/api")
@router.post("/plan-full-trip")
async def plan_full_trip(request: TripPlanRequest) -> Dict[str, Any]:
    try:
        full_trip_info = plan_full_trip_agent(
            request.destination,
            request.dates,
            request.preferences
        )
        if isinstance(full_trip_info, dict) and "error" in full_trip_info:
            raise HTTPException(status_code=500, detail=full_trip_info["error"])
        return {"data": full_trip_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to plan full trip: {e}")

@router.post("/convert-currency")
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
