"""
Project Drishti - API Routes
Defines all REST endpoints for the Command Center
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import logging
import json
import asyncio
from datetime import datetime, timedelta

from utils.data_models import (
    # Core Models
    IncidentAlert,
    ManualCommand,
    DispatchRequest,
    EdgeTriggerRequest,
    ChatMessage,
    SystemStatus,
    Location,
    VideoAnalysisResult,
    SeverityLevel,
    # Edge Trigger Payload
    AnomalyTriggerPayload,
    # Helper Functions
    create_incident_from_analysis
)
# Import production services only - no mocks for end product
from services.firebase_service import FirebaseService
from services.vision_analysis import VisionAnalysisService
from services.gemini_agent import VertexAIGeminiAgentService as GeminiAgentService
from services.dispatch_logic import DispatchService
from services.forecasting_model import ForecastingService
from services.google_maps_service import GoogleMapsService

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== DEPENDENCY INJECTION =====
def get_firebase_service() -> FirebaseService:
    """Get Firebase service instance"""
    from main import app
    return app.state.firebase

def get_vision_service() -> VisionAnalysisService:
    """Get Vision Analysis service instance"""
    from main import app
    return app.state.vision

def get_gemini_service() -> GeminiAgentService:
    """Get Gemini Agent service instance"""
    from main import app
    return app.state.gemini

def get_dispatch_service() -> DispatchService:
    """Get Dispatch service instance"""
    from main import app
    return app.state.dispatch

def get_forecasting_service() -> ForecastingService:
    """Get Forecasting service instance"""
    from main import app
    return app.state.forecasting

def get_maps_service() -> GoogleMapsService:
    """Get Google Maps service instance"""
    from main import app
    return app.state.maps

# ===== AUTO-DISPATCH MONITORING =====

async def monitor_for_auto_dispatch(
    incident_id: str,
    incident_data: dict,
    firebase: FirebaseService,
    dispatch: DispatchService,
    gemini: GeminiAgentService,
    timeout_seconds: int = 120 # Default to 2 minutes
):
    """
    A background timer that waits for a commander response. If none is received,
    it triggers an automatic, AI-selected dispatch.
    """
    logger.info(f"AUTO-DISPATCH MONITOR: Activated for incident {incident_id}. Timeout: {timeout_seconds} seconds.")
    await asyncio.sleep(timeout_seconds)

    try:
        # After waiting, check the incident's current status in Firebase
        current_incident = firebase.get_document("incidents", incident_id) # CORRECT: uses get_document
        
        # If the incident still exists and is still 'active'
        if current_incident and current_incident.get("status") == "active":
            logger.warning(f"AUTO-DISPATCH: Timeout for {incident_id}. No commander response. Triggering automatic dispatch.")
            
            # Use the dispatch service's intelligence to select and dispatch units
            dispatch_response = await dispatch.dispatch_units(
                incident_id=incident_id,
                priority=SeverityLevel(current_incident.get("severity", "high")),
                instructions=f"AUTOMATIC DISPATCH: AI-initiated response due to timeout.",
                auto_select=True # CRITICAL: tells service to choose best units
            )
            
            if dispatch_response.status in ["dispatched", "partial"]:
                firebase.update_document("incidents", incident_id, {
                    "auto_dispatch_triggered": True,
                    "status": "responded",
                    "commander_response": {
                        "action": "auto_dispatch",
                        "notes": f"AI dispatched units {dispatch_response.units_dispatched} due to response timeout."
                    }
                })
                logger.info(f"AUTO-DISPATCH: Successfully dispatched units {dispatch_response.units_dispatched} to incident {incident_id}.")
            else:
                # ESCALATION LOGIC
                logger.error(f"AUTO-DISPATCH ESCALATION: No units could be dispatched. Errors: {dispatch_response.errors}")
                # Update the incident to reflect the critical resource shortage
                firebase.update_document("incidents", incident_id, {
                    "status": "active",  # Keep it active because it's not handled
                    "severity": "critical",  # Escalate severity to CRITICAL
                    "requires_manual_intervention": True,
                    "system_notes": f"CRITICAL ALERT: Automatic dispatch failed. No available units found. Immediate manual intervention required."
                })
        else:
            logger.info(f"AUTO-DISPATCH MONITOR: Incident {incident_id} was already handled. Cancelling.")
    except Exception as e:
        logger.error(f"AUTO-DISPATCH MONITOR: Critical error for incident {incident_id}: {e}", exc_info=True)

# ===== SYSTEM STATUS =====

@router.get("/system/status")
async def get_system_status(
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Get overall system health and status"""
    try:
        # Check various system components
        status_checks = {
            "firebase": "healthy",
            "vision_ai": "healthy", 
            "gemini_agent": "healthy",
            "dispatch_system": "healthy"
        }
        
        # Get system metrics
        metrics = {
            "uptime": "99.9%",
            "response_time": "1.2s",
            "active_cameras": 12,
            "processed_alerts_today": 15
        }
        
        return {
            "overall_status": "operational",
            "components": status_checks,
            "metrics": metrics,
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/simulate-anomaly")
async def simulate_anomaly(
    anomaly_type: str = "crowd_surge",
    location: str = "main_entrance",
    firebase: FirebaseService = Depends(get_firebase_service),
    maps: GoogleMapsService = Depends(get_maps_service)
):
    """Simulate an anomaly for testing purposes with real location data"""
    try:
        # Get actual location data from Google Maps
        location_data = maps.get_location_by_zone(location)
        
        if not location_data:
            # If zone not found, try geocoding as address
            location_data = maps.geocode_address(location)
            
        if not location_data:
            # Fallback to center location
            location_data = {
                "latitude": 34.0522,
                "longitude": -118.2437,
                "name": f"Unknown location: {location}",
                "address": "Address not found"
            }
        
        # Create simulated incident with proper Location object
        incident_data = {
            "type": anomaly_type,
            "source": "manual_simulation",
            "location": {
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"],
                "name": location_data["name"]
            },
            "status": "active",
            "severity": "high",
            "description": f"Simulated {anomaly_type.replace('_', ' ')} at {location_data['name']}",
            "timestamp": firebase.get_server_timestamp(),
            "metadata": {
                "simulation": True,
                "triggered_by": "commander",
                "address": location_data.get("address", ""),
                "zone_id": location_data.get("zone_id", "")
            }
        }
        
        incident_id = firebase.add_document("incidents", incident_data)
        
        # Create corresponding alert
        alert_data = {
            "incident_id": incident_id,
            "alert_type": anomaly_type,
            "severity": "high",
            "confidence": 0.95,
            "description": f"🚨 Simulated {anomaly_type.replace('_', ' ')} detected at {location_data['name']}",
            "requires_response": True,
            "timestamp": firebase.get_server_timestamp(),
            "status": "active",
            "location": incident_data["location"]
        }
        
        alert_id = firebase.add_document("alerts", alert_data)
        
        return {
            "status": "success",
            "incident_id": incident_id,
            "alert_id": alert_id,
            "location": location_data,
            "message": f"Simulated {anomaly_type} created successfully at {location_data['name']}"
        }
        
    except Exception as e:
        logger.error(f"Anomaly simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== EDGE DEVICE INTEGRATION =====

# ===== INCIDENT MANAGEMENT =====

@router.get("/incidents", response_model=List[IncidentAlert])
async def get_incidents(
    status: Optional[str] = None,
    limit: int = 50,
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Get list of incidents with optional filtering"""
    try:
        query_filters = {}
        if status:
            query_filters["status"] = status
            
        incidents = firebase.get_collection_with_filters(
            "incidents",
            filters=query_filters,
            limit=limit,
            order_by=("timestamp", "desc")
        )
        
        return [IncidentAlert(**incident) for incident in incidents]
        
    except Exception as e:
        logger.error(f"Failed to fetch incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Get specific incident details"""
    try:
        incident = firebase.get_document("incidents", incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
            
        return incident
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/incidents/{incident_id}/respond")
async def respond_to_incident(
    incident_id: str,
    response: ManualCommand,
    firebase: FirebaseService = Depends(get_firebase_service),
    dispatch: DispatchService = Depends(get_dispatch_service)
):
    """Commander response to an incident"""
    try:
        # Update incident with commander response
        update_data = {
            "commander_response": response.dict(),
            "status": "responded",
            "response_timestamp": firebase.get_server_timestamp()
        }
        
        firebase.update_document("incidents", incident_id, update_data)
        
        # Execute dispatch if requested
        if response.dispatch_units:
            dispatch_result = await dispatch.dispatch_units(
                incident_id=incident_id,
                unit_ids=response.dispatch_units,
                priority=response.priority
            )
            
            # Log dispatch action
            firebase.add_document("dispatch_logs", {
                "incident_id": incident_id,
                "units_dispatched": response.dispatch_units,
                "dispatch_result": dispatch_result,
                "timestamp": firebase.get_server_timestamp()
            })
        
        return {"status": "success", "message": "Response recorded"}
        
    except Exception as e:
        logger.error(f"Failed to respond to incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    payload: dict = Body(...),  # Expects {"resolution_notes": "Situation clear."}
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """
    Marks an incident as resolved and returns dispatched units to 'available' status.
    """
    try:
        resolution_notes = payload.get("resolution_notes", "Incident resolved by commander.")
        logger.info(f"Resolving incident {incident_id}...")

        # Find the original incident to see which units were on scene
        incident = firebase.get_document("incidents", incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found.")

        # Find all units that were dispatched to this incident
        # This can be from manual dispatch or auto-dispatch
        units_to_release = []
        if incident.get("commander_response", {}).get("action") == "dispatch":
            units_to_release.extend(incident["commander_response"].get("dispatch_units", []))
        
        if incident.get("auto_dispatch_triggered"):
            # We need to find the dispatch record to see which units were sent
            dispatches = firebase.get_collection_with_filters(
                "dispatches",
                filters={"incident_id": incident_id},
                limit=1,
                order_by=("timestamp", "desc")
            )
            if dispatches:
                units_to_release.extend(dispatches[0].get("units_dispatched", []))

        # Make the list of units unique
        units_to_release = list(set(units_to_release))
        
        # Update the status of each released unit back to 'available'
        if units_to_release:
            for unit_id in units_to_release:
                firebase.update_document("security_units", unit_id, {
                    "status": "available",
                    "current_assignment": None,
                    "dispatch_id": None
                })
            logger.info(f"Released units {units_to_release} back to 'available' status.")

        # Finally, update the incident status to 'resolved'
        firebase.update_document("incidents", incident_id, {
            "status": "resolved",
            "resolution_notes": resolution_notes,
            "resolved_timestamp": firebase.get_server_timestamp()
        })

        return {"status": "success", "message": f"Incident {incident_id} has been resolved.", "units_released": units_to_release}

    except Exception as e:
        logger.error(f"Failed to resolve incident {incident_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ===== EDGE SIMULATION =====

@router.post("/simulate/edge-trigger")
async def trigger_edge_simulation(
    request: EdgeTriggerRequest,
    background_tasks: BackgroundTasks,
    firebase: FirebaseService = Depends(get_firebase_service),
    vision: VisionAnalysisService = Depends(get_vision_service)
):
    """Trigger simulated edge processing for demo"""
    try:
        logger.info(f"Starting edge simulation for video: {request.video_path}")
        
        # Create initial incident record
        incident_data = {
            "type": "simulated_detection",
            "source": "edge_device",
            "video_path": request.video_path,
            "location": request.location,
            "status": "processing",
            "timestamp": firebase.get_server_timestamp(),
            "metadata": {
                "simulation": True,
                "camera_id": request.camera_id or "demo_camera_01"
            }
        }
        
        incident_id = firebase.add_document("incidents", incident_data)
        
        # Process video analysis in background
        background_tasks.add_task(
            process_edge_simulation,
            incident_id,
            request,
            firebase,
            vision
        )
        
        return {
            "status": "started",
            "incident_id": incident_id,
            "message": "Edge simulation initiated"
        }
        
    except Exception as e:
        logger.error(f"Failed to start edge simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_edge_simulation(
    incident_id: str,
    request: EdgeTriggerRequest,
    firebase: FirebaseService,
    vision: VisionAnalysisService
):
    """Background task to process simulated edge detection"""
    try:
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(2)
        
        # Analyze video with Vision AI
        analysis_result = await vision.analyze_video_for_anomalies(
            video_path=request.video_path,
            detection_types=["crowd_density", "suspicious_activity", "emergency_situations"]
        )
        
        # Update incident with analysis
        update_data = {
            "analysis_result": analysis_result,
            "status": "detected" if analysis_result.get("anomaly_detected") else "normal",
            "processed_timestamp": firebase.get_server_timestamp()
        }
        
        firebase.update_document("incidents", incident_id, update_data)
        
        # If anomaly detected, trigger alert workflow
        if analysis_result.get("anomaly_detected"):
            await trigger_alert_workflow(incident_id, analysis_result, firebase)
            
        logger.info(f"Edge simulation completed for incident {incident_id}")
        
    except Exception as e:
        logger.error(f"Edge simulation failed for {incident_id}: {e}")
        # Update incident with error status
        firebase.update_document("incidents", incident_id, {
            "status": "error",
            "error_message": str(e),
            "error_timestamp": firebase.get_server_timestamp()
        })

async def trigger_alert_workflow(
    incident_id: str,
    analysis_result: Dict,
    firebase: FirebaseService
):
    """Trigger the alert workflow for detected anomalies"""
    try:
        # Create alert data
        alert_data = {
            "incident_id": incident_id,
            "alert_type": analysis_result.get("anomaly_type", "unknown"),
            "severity": analysis_result.get("severity", "medium"),
            "confidence": analysis_result.get("confidence", 0.0),
            "description": analysis_result.get("description", "Anomaly detected"),
            "requires_response": True,
            "timestamp": firebase.get_server_timestamp(),
            "status": "active"
        }
        
        # Store alert
        alert_id = firebase.add_document("alerts", alert_data)
        
        # Send notification (this would typically trigger Cloud Function)
        await send_alert_notification(alert_id, alert_data, firebase)
        
        logger.info(f"Alert workflow triggered for incident {incident_id}")
        
    except Exception as e:
        logger.error(f"Failed to trigger alert workflow: {e}")

async def send_alert_notification(
    alert_id: str,
    alert_data: Dict,
    firebase: FirebaseService
):
    """Send alert notification to command center"""
    try:
        # In real implementation, this would send FCM notification
        # For demo, we'll just log and update Firestore
        
        notification_data = {
            "alert_id": alert_id,
            "type": "incident_alert",
            "title": f"🚨 {alert_data['alert_type'].replace('_', ' ').title()} Detected",
            "body": alert_data["description"],
            "data": alert_data,
            "sent_timestamp": firebase.get_server_timestamp()
        }
        
        firebase.add_document("notifications", notification_data)
        logger.info(f"Alert notification sent for {alert_id}")
        
    except Exception as e:
        logger.error(f"Failed to send alert notification: {e}")

# ====================================================================
#               UPDATED: EDGE DEVICE INTEGRATION
# ====================================================================

# ... (all your imports and other routes remain the same) ...

async def process_anomaly_in_background(
    payload: dict,
    firebase: FirebaseService,
    vision: VisionAnalysisService,
    gemini: GeminiAgentService,
    dispatch: DispatchService,
    background_tasks: BackgroundTasks
):
    """
    This is the background task that orchestrates the full analysis pipeline
    after an initial trigger from an edge device.
    """
    anomaly_id = payload.get("anomalyId", "unknown_id")
    logger.info(f"BACKGROUND: Starting full analysis for anomaly ID {anomaly_id}")
    try:
        # Step 1: Create an initial 'processing' incident record in Firestore.
        initial_incident_data = {
            "type": payload.get("anomalyType", "suspicious_activity"),
            "source": "edge_device", "status": "processing", "severity": "low",
            "description": f"Initial trigger: {payload.get('details')}",
            "timestamp": firebase.get_server_timestamp(),
            "edge_trigger_payload": payload,
            "metadata": { "camera_id": payload.get("cameraId"), "video_path": payload.get("sourceVideo") },
            "location": { "name": payload.get("location", "Unknown Zone") }
        }
        incident_id = firebase.add_document("incidents", initial_incident_data, custom_id=anomaly_id)
        logger.info(f"BACKGROUND: Created initial incident {incident_id} in Firestore.")

        # Step 2: Trigger deep analysis with VisionAnalysisService
        analysis_result_dict = await vision.analyze_video_for_anomalies(
            video_path=payload.get("sourceVideo"),
            detection_types=[payload.get("anomalyType")]
        )
        logger.info(f"BACKGROUND: Vision analysis complete for {incident_id}.")

        # Step 3: Handle false alarms
        if not analysis_result_dict.get("anomaly_detected"):
            logger.info(f"BACKGROUND: Analysis for {incident_id} is a false alarm. Resolving.")
            firebase.update_document(
                "incidents", incident_id, {"status": "false_alarm", "description": "AI analysis confirmed no anomaly."}
            )
            return

        # Step 4: Structure the confirmed anomaly data using Pydantic models
        analysis_result = VideoAnalysisResult(**analysis_result_dict)
        # New dynamic location
        location_payload = payload.get("location")
        if isinstance(location_payload, dict):
            incident_location = Location(**location_payload)
        else: # Fallback for safety
            incident_location = Location(name="Unknown Location")
        full_incident = create_incident_from_analysis(
            analysis_result=analysis_result,
            location=incident_location,
            video_path=payload.get("sourceVideo"),
            camera_id=payload.get("cameraId")
        )

        # Step 5: Generate a summary and action plan with Gemini.
        # This is the updated part to match your Gemini service.
        prompt = f"""
You are 'Aegis', a senior AI security analyst for the Drishti Command Center. Your role is to provide calm, authoritative, and detailed situational analysis for security commanders.

An anomaly has been detected and confirmed by our visual AI systems. Your task is to generate a comprehensive incident briefing.

**CONTEXT:**
- **Initial Anomaly Type (from Edge Device):** {payload.get('anomalyType')}
- **Initial Details (from Edge Device):** {payload.get('details')}
- **Camera ID:** {payload.get('cameraId')}
- **Location:** {payload.get('location', {}).get('name')}

**CONFIRMED VISUAL ANALYSIS (from Vertex AI Vision):**
- **Confirmed Anomaly Type:** {analysis_result.anomaly_type.value if analysis_result.anomaly_type else 'N/A'}
- **Analysis Description:** {analysis_result.description}
- **Assessed Severity:** {analysis_result.severity.value}
- **Confidence Score:** {analysis_result.confidence:.2%}

**YOUR TASK:**
Generate a briefing for the commander. The response MUST be a valid JSON object with ONLY two keys: "summary" and "action_plan".

1.  **"summary"**: Write a detailed executive summary (2-3 sentences). Explain what is happening, where it is happening, and the immediate implications.
2.  **"action_plan"**: Provide a list of at least three specific, multi-step strategic actions. Do not just say "Dispatch units." Explain *why* and *what they should do*. For example: "1. Immediate Response: Dispatch two patrol units (e.g., Unit A3, B2) to establish a perimeter and assess the situation from a safe distance. Instruct them not to engage directly but to report back on crowd mood and movement.", "2. Communication Protocol: Make a calm, pre-recorded announcement over the PA system advising visitors to avoid the area due to a 'temporary operational issue'. Avoid causing panic.", "3. Contingency Planning: Alert medical teams to be on standby and review evacuation routes for the affected zone in case of escalation."

Example of the required JSON output format:
{{
    "summary": "A high-density crowd is forming at the Main Concourse near Camera 04. The situation is currently assessed as HIGH severity due to the potential for a crowd surge, which could lead to injuries.",
    "action_plan": [
        "1. Immediate Containment & Assessment: Dispatch two patrol units to the perimeter of the Main Concourse. Their primary goal is to observe, report on crowd behavior, and prevent further entry into the area.",
        "2. Public Communication: Utilize the PA system to make a calm announcement, redirecting foot traffic to alternative routes due to a 'technical fault' to manage crowd flow without inducing panic.",
        "3. Prepare for Escalation: Place the on-site medical team on standby and have command review the evacuation protocols for the Main Concourse. Prepare to open emergency exits if density continues to increase."
    ]
}}
"""
        # Call the base model directly.
        response = gemini.model.generate_content(prompt)
        
        # Extract and parse the JSON text
        raw_text = response.candidates[0].content.parts[0].text
        # Clean up the response to ensure it's valid JSON
        json_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
        gemini_response = json.loads(json_text)
        
        logger.info(f"BACKGROUND: Gemini summary generated for {incident_id}.")

        # Step 6: Update the incident in Firestore with the full, rich data
        final_update = full_incident.dict()
        final_update["gemini_summary"] = gemini_response.get("summary")
        final_update["gemini_action_plan"] = gemini_response.get("action_plan")
        final_update["status"] = "active" # Ready for commander review
        
        if 'id' in final_update:
            del final_update['id']

        firebase.update_document("incidents", incident_id, final_update)
        logger.info(f"BACKGROUND: Incident {incident_id} updated with full analysis. Workflow complete.")

        # Step 7: Start auto-dispatch monitoring timer with dynamic timeout based on severity
        # Determine the timeout based on the confirmed severity
        incident_severity = final_update.get("severity", "medium")
        timeout_seconds = 30 if incident_severity in ["high", "critical"] else 120
        
        logger.info(f"AUTO-DISPATCH: Severity is '{incident_severity}'. Setting response timeout to {timeout_seconds} seconds.")

        # Start the auto-dispatch monitor with the correct timeout
        full_incident_data = {**initial_incident_data, **final_update}  # Combine data for context
        background_tasks.add_task(
            monitor_for_auto_dispatch,
            incident_id=incident_id,
            incident_data=full_incident_data,  # Pass incident data for context
            firebase=firebase,
            dispatch=dispatch,
            gemini=gemini,
            timeout_seconds=timeout_seconds  # Pass the dynamic timeout
        )
        logger.info(f"BACKGROUND: Auto-dispatch monitor started for incident {incident_id} with {timeout_seconds}s timeout")

    except Exception as e:
        logger.error(f"BACKGROUND: Error processing anomaly {anomaly_id}: {e}", exc_info=True)
        firebase.update_document("incidents", anomaly_id, { "status": "error", "error_message": str(e) })

@router.post("/trigger-anomaly", status_code=202)
async def receive_edge_anomaly_trigger(
    # The payload from edge is simple, so a raw dict is fine.
    # We will validate it inside the background task using your more complex models.
    payload: dict, 
    background_tasks: BackgroundTasks,
    firebase: FirebaseService = Depends(get_firebase_service),
    vision: VisionAnalysisService = Depends(get_vision_service),
    gemini: GeminiAgentService = Depends(get_gemini_service),
    dispatch: DispatchService = Depends(get_dispatch_service)
):
    """
    Receives an initial anomaly trigger from an edge device.
    """
    anomaly_id = payload.get("anomalyId", "unknown")
    anomaly_type = payload.get("anomalyType", "unknown")
    logger.info(f"API CALL RECEIVED: Anomaly '{anomaly_type}' (ID: {anomaly_id}).")
    
    # Add the heavy processing to a background task
    background_tasks.add_task(
        process_anomaly_in_background, payload, firebase, vision, gemini, dispatch, background_tasks
    )
    
    # Immediately return a response to the edge device
    return {
        "status": "accepted",
        "message": "Anomaly trigger received and queued for full analysis.",
        "incident_id": anomaly_id
    }

# ===== GEMINI CHAT AGENT =====

@router.post("/chat")
async def chat_with_agent(
    message: ChatMessage,
    firebase: FirebaseService = Depends(get_firebase_service),
    gemini: GeminiAgentService = Depends(get_gemini_service)
):
    """Chat with Gemini AI agent"""
    try:
        # Get current context from recent incidents
        recent_incidents = firebase.get_collection_with_filters(
            "incidents",
            limit=10,
            order_by=("timestamp", "desc")
        )
        
        # Generate response with context
        response = await gemini.generate_contextual_response(
            user_message=message.content,
            context_data={
                "recent_incidents": recent_incidents,
                "system_status": "operational",  # Could fetch from system status
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Store conversation
        conversation_data = {
            "user_message": message.content,
            "agent_response": response,
            "timestamp": firebase.get_server_timestamp(),
            "session_id": message.session_id
        }
        
        firebase.add_document("chat_history", conversation_data)
        
        return {"response": response, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== DISPATCH MANAGEMENT =====

@router.get("/units")
async def get_security_units(
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Get all security units and their status"""
    try:
        units = firebase.get_collection("security_units")
        return units
        
    except Exception as e:
        logger.error(f"Failed to fetch security units: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dispatch")
async def manual_dispatch(
    request: DispatchRequest,
    firebase: FirebaseService = Depends(get_firebase_service),
    dispatch: DispatchService = Depends(get_dispatch_service)
):
    """Manual dispatch of security units"""
    try:
        result = await dispatch.dispatch_units(
            incident_id=request.incident_id,
            unit_ids=request.unit_ids,
            priority=request.priority,
            instructions=request.instructions
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Manual dispatch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ANALYTICS & FORECASTING =====

@router.get("/analytics/crowd-forecast")
async def get_crowd_forecast(
    location: str,
    hours_ahead: int = 4,
    forecasting: ForecastingService = Depends(get_forecasting_service)
):
    """Get crowd density forecast"""
    try:
        forecast = await forecasting.predict_crowd_density(
            location=location,
            time_horizon_hours=hours_ahead
        )
        
        return forecast
        
    except Exception as e:
        logger.error(f"Crowd forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/dashboard")
async def get_dashboard_data(
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Get dashboard analytics data"""
    try:
        # Get counts for dashboard widgets
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Active incidents
        active_incidents = firebase.get_collection_with_filters(
            "incidents",
            filters={"status": "active"},
            limit=100
        )
        
        # Today's incidents
        todays_incidents = firebase.get_collection_with_filters(
            "incidents",
            filters={"timestamp": (">=", today_start)},
            limit=100
        )
        
        # Security units status
        units = firebase.get_collection("security_units")
        available_units = [u for u in units if u.get("status") == "available"]
        
        # Recent alerts
        recent_alerts = firebase.get_collection_with_filters(
            "alerts",
            limit=10,
            order_by=("timestamp", "desc")
        )
        
        return {
            "active_incidents": len(active_incidents),
            "todays_incidents": len(todays_incidents),
            "available_units": len(available_units),
            "total_units": len(units),
            "recent_alerts": recent_alerts,
            "system_status": "operational",
            "last_updated": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard data fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== LOCATION MANAGEMENT =====

@router.get("/locations/zones")
async def get_venue_zones(
    maps: GoogleMapsService = Depends(get_maps_service)
):
    """Get all predefined venue zones"""
    try:
        zones = maps.get_all_zones()
        return {"zones": zones, "total": len(zones)}
    except Exception as e:
        logger.error(f"Failed to fetch venue zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zones/{zone_name}/status")
async def get_zone_status(
    zone_name: str,
    firebase: FirebaseService = Depends(get_firebase_service),
    gemini: GeminiAgentService = Depends(get_gemini_service)
):
    """
    Gets a real-time summary and recommended actions for a specific zone.
    """
    try:
        # 1. Get all active incidents in the specified zone
        # Note: This requires your 'incidents' documents to have a 'location.zone' field.
        # If not, you might filter on 'location.name' or another relevant field.
        active_incidents_in_zone = firebase.get_collection_with_filters(
            "incidents",
            filters={"location.name": zone_name, "status": "active"}
        )

        # 2. Get all security units currently in that zone
        # This is a simplified query. A real system might use Geo-queries.
        all_units = firebase.get_collection("security_units")
        units_in_zone = [
            unit for unit in all_units 
            if unit.get("location", {}).get("name") and zone_name.lower() in unit["location"]["name"].lower()
        ]

        # 3. Call Gemini to generate the intelligent summary
        summary = await gemini.generate_zone_status_briefing(zone_name, active_incidents_in_zone, units_in_zone)

        return {
            "zone_name": zone_name,
            "summary_briefing": summary,
            "raw_data": {
                "active_incidents": active_incidents_in_zone,
                "units_in_zone": units_in_zone
            }
        }
    except Exception as e:
        logger.error(f"Failed to get status for zone {zone_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations/geocode")
async def geocode_location(
    address: str,
    maps: GoogleMapsService = Depends(get_maps_service)
):
    """Convert address to coordinates"""
    try:
        location_data = maps.geocode_address(address)
        if not location_data:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return location_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/locations/validate")
async def validate_location(
    latitude: float,
    longitude: float,
    maps: GoogleMapsService = Depends(get_maps_service)
):
    """Validate if coordinates are within venue boundaries"""
    try:
        is_valid = maps.validate_location_within_venue(latitude, longitude)
        nearest_zone = maps.get_nearest_zone(latitude, longitude)
        address = maps.reverse_geocode(latitude, longitude)
        
        return {
            "is_within_venue": is_valid,
            "nearest_zone": nearest_zone,
            "address": address,
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }
    except Exception as e:
        logger.error(f"Location validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#