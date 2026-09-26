from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from app.api.routes import (
    auth,
    reports,
    ocr,
    soil,
    recommendations,
    history,
    assistant,
)



# Create FastAPI Application

app = FastAPI(
    title="Smart Soil Health API",
    description="Backend API for Smart Soil Health Detection and Decision Support System",
    version="1.0.0",
)



# CORS Configuration


origins = [
    "http://localhost:5173",      # Vite frontend
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Register API Routers


app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"],
)

app.include_router(
    reports.router,
    prefix="/api/reports",
    tags=["Reports"],
)

app.include_router(
    ocr.router,
    prefix="/api/ocr",
    tags=["OCR"],
)

app.include_router(
    soil.router,
    prefix="/api/soil",
    tags=["Soil"],
)

app.include_router(
    recommendations.router,
    prefix="/api/recommendations",
    tags=["Recommendations"],
)

app.include_router(
    history.router,
    prefix="/api/history",
    tags=["History"],
)

app.include_router(
    assistant.router,
    prefix="/api/assistant",
    tags=["AI Assistant"],
)

# Root Endpoint
@app.get("/")
async def root():
    return {
        "message": "Smart Soil Health API is running",
        "version": "1.0.0",
        "status": "success",
    }



# Health Check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Smart Soil Health API",
    }
