"""
Project Drishti - Demo Backend
Simplified version for local development without external dependencies
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime
import json
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

# Data models for the demo
class IncidentData(BaseModel):
    type: str
    location: str
    severity: str
    description: str

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class DispatchRequest(BaseModel):
    incident_id: str
    unit_type: str
    priority: str

# In-memory storage for demo
demo_data = {
    "incidents": [],
    "chat_history": [],
    "alerts": [],
    "analytics": {
        "crowd_density": 0.6,
        "response_times": [2.1, 1.8, 3.2, 2.5],
        "incident_count": 0
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Drishti Demo Backend...")
    
    # Initialize some demo data
    demo_data["incidents"] = [
        {
            "id": "demo-001",
            "type": "crowd_surge",
            "location": "main_entrance",
            "severity": "medium",
            "status": "resolved",
            "description": "Crowd buildup detected at main entrance",
            "timestamp": datetime.now().isoformat(),
            "resolved_at": datetime.now().isoformat()
        }
    ]
    
    logger.info("✅ Demo backend initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Demo Backend...")

# Create FastAPI application
app = FastAPI(
    title="Project Drishti Demo API",
    description="AI-Powered Crowd Management System Backend (Demo Mode)",
    version="1.0.0-demo",
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

# ===== ROOT ENDPOINTS =====

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Project Drishti Demo API",
        "version": "1.0.0-demo",
        "status": "operational",
        "description": "AI-Powered Crowd Management System (Demo Mode)",
        "mode": "demo"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "mode": "demo"
        },
        "timestamp": datetime.now().isoformat()
    }

# ===== API V1 ROUTES =====

@app.get("/api/v1/system/status")
async def get_system_status():
    """Get overall system health and status"""
    return {
        "overall_status": "operational",
        "components": {
            "demo_backend": "healthy",
            "vision_ai": "simulated", 
            "chat_agent": "simulated",
            "dispatch_system": "simulated"
        },
        "metrics": {
            "uptime": "100%",
            "response_time": "0.1s",
            "active_cameras": 8,
            "processed_alerts_today": len(demo_data["incidents"])
        },
        "last_check": datetime.now().isoformat(),
        "mode": "demo"
    }

@app.post("/api/v1/system/simulate-anomaly")
async def simulate_anomaly(
    anomaly_type: str = "crowd_surge",
    location: str = "main_entrance"
):
    """Simulate an anomaly for testing purposes"""
    incident_id = f"demo-{len(demo_data['incidents']) + 1:03d}"
    
    incident_data = {
        "id": incident_id,
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
    
    demo_data["incidents"].append(incident_data)
    demo_data["analytics"]["incident_count"] += 1
    
    return {
        "status": "success",
        "incident_id": incident_id,
        "message": f"Simulated {anomaly_type} created successfully"
    }

@app.get("/api/v1/incidents")
async def get_incidents(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """Get incidents with optional filtering"""
    incidents = demo_data["incidents"]
    
    if status:
        incidents = [i for i in incidents if i["status"] == status]
    
    return {
        "incidents": incidents[-limit:],
        "total": len(incidents),
        "mode": "demo"
    }

@app.post("/api/v1/incidents")
async def create_incident(incident: IncidentData):
    """Create a new incident"""
    incident_id = f"demo-{len(demo_data['incidents']) + 1:03d}"
    
    incident_data = {
        "id": incident_id,
        "type": incident.type,
        "location": incident.location,
        "severity": incident.severity,
        "description": incident.description,
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "source": "manual_entry"
    }
    
    demo_data["incidents"].append(incident_data)
    demo_data["analytics"]["incident_count"] += 1
    
    return {
        "status": "success",
        "incident_id": incident_id,
        "incident": incident_data
    }

@app.get("/api/v1/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get specific incident by ID"""
    incident = next((i for i in demo_data["incidents"] if i["id"] == incident_id), None)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return {
        "incident": incident,
        "mode": "demo"
    }

@app.post("/api/v1/chat")
async def chat_with_agent(message: ChatMessage):
    """Chat with the AI agent"""
    # Store user message
    user_msg = {
        "id": f"msg-{len(demo_data['chat_history']) + 1}",
        "role": "user",
        "content": message.message,
        "timestamp": datetime.now().isoformat()
    }
    demo_data["chat_history"].append(user_msg)
    
    # Generate demo response
    demo_responses = [
        "I'm analyzing the current situation. All systems are operational.",
        "Based on crowd density data, I recommend deploying additional security at the main entrance.",
        "The incident has been logged. I'm coordinating with emergency response teams.",
        "Current crowd levels are within normal parameters. Continuing monitoring.",
        "I've identified a potential bottleneck at checkpoint 3. Dispatching personnel."
    ]
    
    import random
    response_content = random.choice(demo_responses)
    
    # Store agent response
    agent_msg = {
        "id": f"msg-{len(demo_data['chat_history']) + 1}",
        "role": "assistant",
        "content": response_content,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.95
    }
    demo_data["chat_history"].append(agent_msg)
    
    return {
        "response": response_content,
        "confidence": 0.95,
        "suggestions": [
            "Check camera feeds",
            "Review incident reports",
            "Monitor crowd density"
        ],
        "mode": "demo"
    }

@app.get("/api/v1/chat/history")
async def get_chat_history(limit: int = Query(default=50, le=100)):
    """Get chat history"""
    return {
        "messages": demo_data["chat_history"][-limit:],
        "total": len(demo_data["chat_history"]),
        "mode": "demo"
    }

@app.post("/api/v1/dispatch")
async def dispatch_units(request: DispatchRequest):
    """Dispatch emergency units"""
    dispatch_id = f"dispatch-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    dispatch_data = {
        "id": dispatch_id,
        "incident_id": request.incident_id,
        "unit_type": request.unit_type,
        "priority": request.priority,
        "status": "dispatched",
        "eta": "5-8 minutes",
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "status": "success",
        "dispatch_id": dispatch_id,
        "dispatch": dispatch_data,
        "message": f"{request.unit_type} unit dispatched with {request.priority} priority"
    }

@app.get("/api/v1/analytics/crowd-density")
async def get_crowd_density():
    """Get current crowd density analytics"""
    import random
    
    # Simulate crowd density data
    density_data = {
        "overall_density": round(random.uniform(0.3, 0.8), 2),
        "zones": {
            "main_entrance": round(random.uniform(0.4, 0.9), 2),
            "food_court": round(random.uniform(0.2, 0.7), 2),
            "exhibition_hall": round(random.uniform(0.3, 0.8), 2),
            "parking_area": round(random.uniform(0.1, 0.5), 2)
        },
        "trend": "stable",
        "last_updated": datetime.now().isoformat(),
        "mode": "demo"
    }
    
    return density_data

@app.get("/api/v1/analytics/forecasting")
async def get_forecasting_data():
    """Get crowd forecasting predictions"""
    import random
    
    # Generate demo forecasting data
    hours = []
    predictions = []
    
    for i in range(12):  # Next 12 hours
        hour = (datetime.now().hour + i) % 24
        hours.append(f"{hour:02d}:00")
        predictions.append(round(random.uniform(0.2, 0.8), 2))
    
    return {
        "predictions": {
            "hours": hours,
            "crowd_density": predictions,
            "confidence": 0.85
        },
        "recommendations": [
            "Deploy extra staff during peak hours (18:00-20:00)",
            "Monitor main entrance closely at 19:00",
            "Consider opening additional entry points if needed"
        ],
        "last_updated": datetime.now().isoformat(),
        "mode": "demo"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    
    logger.info(f"🌟 Starting Drishti Demo Backend on port {port}")
    
    uvicorn.run(
        "main_demo:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
