"""
Project Drishti - Data Models
Pydantic models for data validation and structure
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class IncidentType(str, Enum):
    CROWD_SURGE = "crowd_surge"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    EMERGENCY_SITUATION = "emergency_situation"
    FIRE_HAZARD = "fire_hazard"
    MEDICAL_EMERGENCY = "medical_emergency"
    SECURITY_BREACH = "security_breach"
    EVACUATION_NEEDED = "evacuation_needed"
    TECHNICAL_FAILURE = "technical_failure"

class IncidentStatus(str, Enum):
    ACTIVE = "active"
    PROCESSING = "processing"
    RESPONDED = "responded"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"
    ERROR = "error"

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UnitStatus(str, Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    BUSY = "busy"
    OFFLINE = "offline"

# ===== CORE MODELS =====

class Location(BaseModel):
    """Geographic location model"""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    name: Optional[str] = None
    zone: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None

class VideoAnalysisResult(BaseModel):
    """Result from video analysis"""
    anomaly_detected: bool
    anomaly_type: Optional[IncidentType] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    description: str
    severity: SeverityLevel = SeverityLevel.MEDIUM
    detected_objects: List[Dict[str, Any]] = []
    crowd_density: Optional[float] = None
    processing_time_ms: Optional[int] = None
    frame_analysis: List[Dict[str, Any]] = []

class IncidentAlert(BaseModel):
    """Main incident alert model"""
    id: Optional[str] = None
    type: IncidentType
    status: IncidentStatus = IncidentStatus.ACTIVE
    severity: SeverityLevel
    location: Location
    description: str
    timestamp: datetime
    
    # Analysis data
    analysis_result: Optional[VideoAnalysisResult] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    
    # Media
    video_path: Optional[str] = None
    image_paths: List[str] = []
    
    # Response tracking
    commander_response: Optional[Dict[str, Any]] = None
    response_timestamp: Optional[datetime] = None
    auto_dispatch_triggered: bool = False
    
    # Metadata
    source: str = "system"  # system, manual, edge_device
    camera_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ManualCommand(BaseModel):
    """Commander's manual response to incident"""
    # incident_id has been removed. It will be taken from the URL path.
    action: str  # acknowledge, dispatch, escalate, resolve, false_alarm
    notes: Optional[str] = None
    dispatch_units: List[str] = []
    priority: SeverityLevel = SeverityLevel.MEDIUM
    estimated_response_time: Optional[int] = None  # minutes
    commander_id: Optional[str] = None

class SecurityUnit(BaseModel):
    """Security unit/personnel model"""
    id: str
    name: str
    type: str  # officer, supervisor, medical, fire, etc.
    status: UnitStatus
    location: Location
    contact_info: Dict[str, str] = {}
    skills: List[str] = []
    equipment: List[str] = []
    current_assignment: Optional[str] = None
    last_updated: datetime

class DispatchRequest(BaseModel):
    """Request to dispatch security units"""
    incident_id: str
    unit_ids: List[str]
    priority: SeverityLevel
    instructions: Optional[str] = None
    estimated_arrival: Optional[int] = None  # minutes
    requested_by: Optional[str] = None

class EdgeTriggerRequest(BaseModel):
    """Request to trigger edge device simulation"""
    video_path: str
    location: Location
    camera_id: Optional[str] = None
    detection_types: List[str] = ["crowd_density", "suspicious_activity"]
    
    @validator('video_path')
    def validate_video_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Video path cannot be empty')
        return v.strip()

class AnomalyTriggerPayload(BaseModel):
    """Payload received from edge devices when anomaly is detected"""
    anomalyId: str
    anomalyType: str
    cameraId: Optional[str] = None
    location: Optional[Location] = None  # FIX: Changed from str to Location
    sourceVideo: Optional[str] = None
    details: Optional[str] = None
    timestamp: Optional[datetime] = None
    confidence: Optional[float] = None
    
    @validator('anomalyId')
    def validate_anomaly_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Anomaly ID cannot be empty')
        return v.strip()
    
    @validator('anomalyType')
    def validate_anomaly_type(cls, v):
        if not v or not v.strip():
            raise ValueError('Anomaly type cannot be empty')
        return v.strip()

class ChatMessage(BaseModel):
    """Chat message with Gemini agent"""
    content: str
    session_id: Optional[str] = "default"
    user_id: Optional[str] = None
    context: Dict[str, Any] = {}
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        if len(v.strip()) > 1000:
            raise ValueError('Message too long (max 1000 characters)')
        return v.strip()

class SystemStatus(BaseModel):
    """Overall system status"""
    overall_status: str  # operational, degraded, down
    components: Dict[str, str]  # component_name: status
    metrics: Dict[str, Any]
    last_check: datetime
    alerts: List[str] = []

class NotificationData(BaseModel):
    """Push notification data"""
    title: str
    body: str
    type: str  # alert, update, system
    data: Dict[str, Any] = {}
    target_users: List[str] = []  # empty means broadcast
    priority: str = "normal"  # normal, high

# ===== ANALYTICS MODELS =====

class CrowdForecast(BaseModel):
    """Crowd density forecast"""
    location: str
    predictions: List[Dict[str, Any]]  # time_slot, predicted_density, confidence
    forecast_horizon_hours: int
    generated_at: datetime
    forecast_model_version: str = "v1.0"  # Changed from model_version to avoid conflict

class DashboardMetrics(BaseModel):
    """Dashboard analytics data"""
    active_incidents: int
    total_incidents_today: int
    available_units: int
    total_units: int
    average_response_time: float  # minutes
    system_uptime: float  # percentage
    recent_alerts: List[Dict[str, Any]]
    last_updated: datetime

class IncidentTrend(BaseModel):
    """Incident trend analysis"""
    time_period: str  # hourly, daily, weekly
    incident_counts: Dict[str, int]  # time_slot: count
    incident_types: Dict[IncidentType, int]
    severity_distribution: Dict[SeverityLevel, int]
    peak_hours: List[int]
    trend_direction: str  # increasing, decreasing, stable

# ===== RESPONSE MODELS =====

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    status: str  # success, error
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class DispatchResponse(BaseModel):
    """Response from dispatch operation"""
    dispatch_id: str
    units_dispatched: List[str]
    estimated_arrival_times: Dict[str, int]  # unit_id: minutes
    total_response_time: int  # minutes
    status: str  # dispatched, failed, partial
    errors: List[str] = []

class AnalysisResponse(BaseModel):
    """Response from video analysis"""
    analysis_id: str
    video_path: str
    result: VideoAnalysisResult
    processing_time_seconds: float
    status: str  # completed, failed, processing

# ===== CONFIGURATION MODELS =====

class SystemConfig(BaseModel):
    """System configuration settings"""
    auto_dispatch_timeout: int = 180  # seconds
    confidence_threshold: float = 0.7
    max_concurrent_analyses: int = 5
    alert_cooldown_period: int = 300  # seconds
    enabled_detection_types: List[IncidentType] = []
    notification_settings: Dict[str, Any] = {}
    
class CameraConfig(BaseModel):
    """Camera configuration"""
    camera_id: str
    name: str
    location: Location
    rtmp_url: Optional[str] = None
    detection_zones: List[Dict[str, Any]] = []
    sensitivity: float = Field(0.5, ge=0.0, le=1.0)
    enabled: bool = True
    last_maintenance: Optional[datetime] = None

# ===== VALIDATION HELPERS =====

def validate_location_dict(location_data: Dict) -> Location:
    """Validate and convert dict to Location model"""
    return Location(**location_data)

def validate_severity(severity: str) -> SeverityLevel:
    """Validate severity string"""
    try:
        return SeverityLevel(severity.lower())
    except ValueError:
        return SeverityLevel.MEDIUM

def create_incident_from_analysis(
    analysis_result: VideoAnalysisResult,
    location: Location,
    video_path: str,
    camera_id: Optional[str] = None
) -> IncidentAlert:
    """Create incident alert from analysis result"""
    return IncidentAlert(
        type=analysis_result.anomaly_type or IncidentType.SUSPICIOUS_ACTIVITY,
        severity=analysis_result.severity,
        location=location,
        description=analysis_result.description,
        timestamp=datetime.now(),
        analysis_result=analysis_result,
        confidence=analysis_result.confidence,
        video_path=video_path,
        camera_id=camera_id,
        source="edge_device"
    )   