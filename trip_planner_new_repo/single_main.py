import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import your router from the other file (we will create this next)
from api_routes import router as api_router

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Trip Planner Backend",
    version="1.0.0",
)

# --- CORS Configuration ---
# This stays in your main app file to apply globally
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include the API Router ---
# This is the crucial change. All routes starting with /api will be handled here.
app.include_router(api_router, prefix="/api")

# --- Static Files Mount ---
# This now correctly serves as the fallback for any non-API routes.
app.mount("/", StaticFiles(directory="dist", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
