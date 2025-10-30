"""
Project Drishti - Simple Development Backend
Uses mock services to avoid external dependencies
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import mock services
from services.mock_firebase_service import MockFirebaseService
from services.mock_services import (
    MockVisionAnalysisService,
    MockGeminiAgentService,
    MockDispatchService,
    MockForecastingService
)

# Global services
firebase_service = None
vision_service = None
gemini_service = None
dispatch_service = None
forecasting_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global firebase_service, vision_service, gemini_service, dispatch_service, forecasting_service
    
    # Startup
    logger.info("🚀 Starting Drishti Development Backend with Mock Services...")
    
    # Initialize all mock services
    firebase_service = MockFirebaseService()
    vision_service = MockVisionAnalysisService()
    gemini_service = MockGeminiAgentService()
    dispatch_service = MockDispatchService()
    forecasting_service = MockForecastingService()
    
    # Store in app state
    app.state.firebase = firebase_service
    app.state.vision = vision_service
    app.state.gemini = gemini_service
    app.state.dispatch = dispatch_service
    app.state.forecasting = forecasting_service
    
    logger.info("✅ All mock services initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Development Backend...")

# Create FastAPI application
app = FastAPI(
    title="Project Drishti Development API",
    description="AI-Powered Crowd Management System Backend (Development Mode)",
    version="1.0.0-dev",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://localhost:3000",
        "http://localhost:5173",  # Vite dev server
        "https://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple data models
class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class DispatchRequest(BaseModel):
    incident_id: str
    unit_type: str
    priority: str

class IncidentData(BaseModel):
    type: str
    location: str
    severity: str
    description: str

# Dependency functions
def get_firebase():
    return app.state.firebase

def get_vision():
    return app.state.vision

def get_gemini():
    return app.state.gemini

def get_dispatch():
    return app.state.dispatch

def get_forecasting():
    return app.state.forecasting

# ===== ROOT ENDPOINTS =====

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Project Drishti Development API",
        "version": "1.0.0-dev",
        "status": "operational",
        "description": "AI-Powered Crowd Management System (Development Mode)",
        "mode": "development"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "firebase": "mock",
            "vision": "mock",
            "gemini": "mock",
            "dispatch": "mock",
            "forecasting": "mock"
        },
        "timestamp": datetime.now().isoformat(),
        "mode": "development"
    }

# ===== API V1 ROUTES =====

@app.get("/api/v1/system/status")
async def get_system_status():
    """Get overall system health and status"""
    return {
        "overall_status": "operational",
        "components": {
            "firebase": "healthy (mock)",
            "vision_ai": "healthy (mock)", 
            "gemini_agent": "healthy (mock)",
            "dispatch_system": "healthy (mock)"
        },
        "metrics": {
            "uptime": "100%",
            "response_time": "0.1s",
            "active_cameras": 8,
            "processed_alerts_today": 3
        },
        "last_check": datetime.now().isoformat(),
        "mode": "development"
    }

@app.post("/api/v1/system/simulate-anomaly")
async def simulate_anomaly(
    anomaly_type: str = "crowd_surge",
    location: str = "main_entrance",
    firebase = Depends(get_firebase)
):
    """Simulate an anomaly for testing purposes"""
    incident_id = f"dev-{len(firebase.collections.get('incidents', [])) + 1:03d}"
    
    incident_data = {
        "type": anomaly_type,
        "source": "manual_simulation",
        "location": location,
        "status": "active",
        "severity": "high",
        "description": f"Simulated {anomaly_type.replace('_', ' ')} at {location}",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "simulation": True,
            "triggered_by": "commander"
        }
    }
    
    firebase.add_document("incidents", incident_data, custom_id=incident_id)
    
    return {
        "status": "success",
        "incident_id": incident_id,
        "message": f"Simulated {anomaly_type} created successfully"
    }

@app.get("/api/v1/incidents")
async def get_incidents(
    status: Optional[str] = None,
    limit: int = 50,
    firebase = Depends(get_firebase)
):
    """Get incidents with optional filtering"""
    incidents = firebase.get_collection_with_filters(
        "incidents",
        filters={"status": status} if status else {},
        limit=limit
    )
    
    return {
        "incidents": incidents,
        "total": len(incidents),
        "mode": "development"
    }

@app.post("/api/v1/incidents")
async def create_incident(
    incident: IncidentData,
    firebase = Depends(get_firebase)
):
    """Create a new incident"""
    incident_id = f"dev-{len(firebase.collections.get('incidents', [])) + 1:03d}"
    
    incident_data = {
        "type": incident.type,
        "location": incident.location,
        "severity": incident.severity,
        "description": incident.description,
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "source": "manual_entry"
    }
    
    firebase.add_document("incidents", incident_data, custom_id=incident_id)
    
    return {
        "status": "success",
        "incident_id": incident_id,
        "incident": incident_data
    }

@app.get("/api/v1/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    firebase = Depends(get_firebase)
):
    """Get specific incident by ID"""
    incident = firebase.get_document("incidents", incident_id)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return {
        "incident": incident,
        "mode": "development"
    }

@app.post("/api/v1/chat")
async def chat_with_agent(
    message: ChatMessage,
    firebase = Depends(get_firebase),
    gemini = Depends(get_gemini)
):
    """Chat with the AI agent"""
    # Store user message
    user_msg = {
        "role": "user",
        "content": message.message,
        "timestamp": datetime.now().isoformat()
    }
    firebase.add_document("chat_history", user_msg)
    
    # Generate response
    response = await gemini.generate_contextual_response(
        user_message=message.message,
        context_data={}
    )
    
    # Store agent response
    agent_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.95
    }
    firebase.add_document("chat_history", agent_msg)
    
    return {
        "response": response,
        "confidence": 0.95,
        "suggestions": [
            "Check camera feeds",
            "Review incident reports",
            "Monitor crowd density"
        ],
        "mode": "development"
    }

@app.get("/api/v1/chat/history")
async def get_chat_history(
    limit: int = 50,
    firebase = Depends(get_firebase)
):
    """Get chat history"""
    messages = firebase.get_collection("chat_history", limit=limit)
    
    return {
        "messages": messages,
        "total": len(messages),
        "mode": "development"
    }

@app.get("/api/v1/units")
async def get_security_units(
    firebase = Depends(get_firebase)
):
    """Get all security units and their status"""
    units = firebase.get_collection("security_units")
    
    return {
        "units": units,
        "total": len(units),
        "mode": "development"
    }

@app.post("/api/v1/dispatch")
async def dispatch_units(
    request: DispatchRequest,
    dispatch = Depends(get_dispatch)
):
    """Dispatch security units"""
    result = await dispatch.dispatch_units(
        incident_id=request.incident_id,
        unit_ids=[request.unit_type],  # Convert unit_type to list
        priority=request.priority
    )
    
    return result

@app.get("/api/v1/analytics/crowd-forecast")
async def get_crowd_forecast(
    location: str,
    hours_ahead: int = 4,
    forecasting = Depends(get_forecasting)
):
    """Get crowd density forecast"""
    forecast = await forecasting.predict_crowd_density(
        location=location,
        time_horizon_hours=hours_ahead
    )
    
    return forecast

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_data(
    firebase = Depends(get_firebase)
):
    """Get dashboard analytics data"""
    active_incidents = firebase.get_collection_with_filters(
        "incidents",
        filters={"status": "active"}
    )
    
    all_incidents = firebase.get_collection("incidents")
    units = firebase.get_collection("security_units")
    recent_alerts = firebase.get_collection("alerts", limit=10)
    
    return {
        "active_incidents": len(active_incidents),
        "todays_incidents": len(all_incidents),
        "available_units": 2,
        "total_units": len(units),
        "recent_alerts": recent_alerts,
        "system_status": "operational",
        "last_updated": datetime.now().isoformat(),
        "mode": "development"
    }

# New edge device trigger endpoint
@app.post("/api/v1/trigger-anomaly", status_code=202)
async def receive_edge_anomaly_trigger(
    payload: dict,
    background_tasks: BackgroundTasks,
    firebase = Depends(get_firebase),
    vision = Depends(get_vision),
    gemini = Depends(get_gemini)
):
    """Receives an initial anomaly trigger from an edge device"""
    anomaly_id = payload.get("anomalyId", "unknown")
    anomaly_type = payload.get("anomalyType", "unknown")
    
    logger.info(f"API CALL RECEIVED: Anomaly '{anomaly_type}' (ID: {anomaly_id})")
    
    # Create initial incident
    incident_data = {
        "type": anomaly_type,
        "source": "edge_device",
        "status": "processing",
        "severity": "medium",
        "description": f"Edge trigger: {payload.get('details', 'Unknown anomaly')}",
        "timestamp": datetime.now().isoformat(),
        "edge_trigger_payload": payload,
        "metadata": {
            "camera_id": payload.get("cameraId", "Unknown Camera"),
            "video_path": payload.get("sourceVideo")
        }
    }
    
    firebase.add_document("incidents", incident_data, custom_id=anomaly_id)
    
    return {
        "status": "accepted",
        "message": "Anomaly trigger received and queued for analysis.",
        "incident_id": anomaly_id
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    
    logger.info(f"🌟 Starting Drishti Development Backend on port {port}")
    
    uvicorn.run(
        "main_dev:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
