"""
Project Drishti - Backend Main Entry Point
FastAPI application serving the Command Center APIs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our API routes
from api.v1.routes import router as api_v1_router

# Import all production services - no mocks for end product
from services.firebase_service import FirebaseService
from services.vision_analysis import VisionAnalysisService
from services.gemini_agent import VertexAIGeminiAgentService as GeminiAgentService
from services.dispatch_logic import DispatchService
from services.forecasting_model import ForecastingService
from services.google_maps_service import GoogleMapsService

# Create FastAPI application
app = FastAPI(
    title="Project Drishti API",
    description="AI-Powered Crowd Management System Backend",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("🚀 Starting Drishti Backend Services...")
        
        # Initialize Firebase service
        try:
            firebase_service = FirebaseService()
            app.state.firebase = firebase_service
            logger.info("✅ Firebase service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase service: {e}")
            # Continue without Firebase for now
            app.state.firebase = None
        
        # Initialize Gemini agent
        try:
            gemini_agent = GeminiAgentService()
            app.state.gemini = gemini_agent
            logger.info("✅ Gemini agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini agent: {e}")
            app.state.gemini = None
        
        # Initialize Vision Analysis
        try:
            vision_analysis = VisionAnalysisService()
            app.state.vision = vision_analysis
            logger.info("✅ Vision analysis initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Vision analysis: {e}")
            app.state.vision = None
        
        # Initialize Forecasting Model
        try:
            forecasting_model = ForecastingService()
            app.state.forecasting = forecasting_model
            logger.info("✅ Forecasting model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Forecasting model: {e}")
            app.state.forecasting = None
        
        # Initialize Dispatch Logic
        try:
            dispatch_logic = DispatchService(app.state.firebase if app.state.firebase else None)
            app.state.dispatch = dispatch_logic
            logger.info("✅ Dispatch logic initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Dispatch logic: {e}")
            app.state.dispatch = None
        
        logger.info("✅ All services initialized and ready.")
        
    except Exception as e:
        logger.error(f"Critical error during startup: {e}")
        # Don't raise exception - let the app start even with partial initialization

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Drishti Backend Services...")
    # Add any cleanup logic here if needed

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vite dev server
        "http://localhost:8081",  # Vite dev server
        "http://localhost:8082",  # Vite dev server
        "https://localhost:3000",
        "https://localhost:8080",
        "https://localhost:8081", 
        "https://localhost:8082",
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Project Drishti API",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI-Powered Crowd Management System"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple health check that doesn't require Firebase
        return {
            "status": "healthy",
            "services": {
                "api": "operational"
            },
            "message": "Drishti Backend is running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    logger.info(f"🌟 Starting Drishti Backend on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )