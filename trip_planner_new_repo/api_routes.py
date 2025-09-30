import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from single_trip_agent import plan_full_trip_agent, convert_currency_agent

# Get a logger instance for this module
# The configuration is already applied in single_main.py, so we just need to get the logger.
logger = logging.getLogger(__name__)

router = APIRouter()


class TripPlanRequest(BaseModel):
    destination: str = Field(..., min_length=1)
    from_date: str
    to_date: str
    preferences: Optional[str] = None


class CurrencyConvertRequest(BaseModel):
    amount: float = Field(..., gt=0)
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)


# --- API Endpoints ---

@router.post("/plan-full-trip")
async def plan_full_trip(request: TripPlanRequest) -> Dict[str, Any]:
    logger.info(f"Received request for '/plan-full-trip' for destination: '{request.destination}'")
    try:
        # The actual work is delegated to the agent, which will have its own logging
        full_trip_info = plan_full_trip_agent(
            request.destination,
            request.from_date,
            request.to_date,
            request.preferences
        )

        # Handle errors returned from the agent
        if isinstance(full_trip_info, dict) and "error" in full_trip_info:
            error_detail = full_trip_info["error"]
            logger.error(f"Agent returned an error for destination '{request.destination}': {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)

        logger.info(f"Successfully generated trip plan for '{request.destination}'.")
        return {"data": full_trip_info}

    except Exception as e:
        # Catch any unexpected exceptions
        logger.error(f"An unexpected exception occurred in '/plan-full-trip': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@router.post("/convert-currency")
async def convert_currency(request: CurrencyConvertRequest):
    logger.info(f"Received request for '/convert-currency' from {request.from_currency} to {request.to_currency}")
    try:
        converted_result = convert_currency_agent(
            request.amount,
            request.from_currency,
            request.to_currency
        )
        logger.info(
            f"Successfully converted currency: {request.amount} {request.from_currency} -> {converted_result.get('converted_amount')} {request.to_currency}")
        return {"data": converted_result}

    except Exception as e:
        logger.error(f"An unexpected exception occurred in '/convert-currency': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Currency conversion failed: {e}")

