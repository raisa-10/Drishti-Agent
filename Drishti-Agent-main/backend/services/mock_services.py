"""
Mock services for development mode
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MockVisionAnalysisService:
    """Mock Vision Analysis Service"""
    
    async def analyze_video(self, video_path: str, detection_types: List[str]) -> Dict[str, Any]:
        """Mock video analysis"""
        return {
            "video_path": video_path,
            "detections": [
                {
                    "type": "crowd_density",
                    "confidence": 0.85,
                    "bbox": [100, 100, 200, 200],
                    "description": "High crowd density detected"
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_video_for_anomalies(self, video_path: str, detection_types: List[str]) -> Dict[str, Any]:
        """Mock video anomaly analysis"""
        import random
        
        anomaly_detected = random.choice([True, False])
        
        return {
            "video_path": video_path,
            "anomaly_detected": anomaly_detected,
            "anomaly_type": random.choice(["crowd_surge", "suspicious_activity", "emergency_situation"]) if anomaly_detected else None,
            "confidence": round(random.uniform(0.7, 0.95), 2) if anomaly_detected else 0,
            "severity": random.choice(["low", "medium", "high"]) if anomaly_detected else None,
            "description": "Anomaly detected in video analysis" if anomaly_detected else "No anomalies detected",
            "timestamp": datetime.now().isoformat(),
            "detection_types": detection_types
        }

class MockGeminiAgentService:
    """Mock Gemini Agent Service"""
    
    def __init__(self):
        # Mock model attribute for compatibility
        self.model = self
    
    def generate_content(self, prompt: str):
        """Mock direct model access"""
        class MockResponse:
            def __init__(self):
                self.candidates = [MockCandidate()]
        
        class MockCandidate:
            def __init__(self):
                self.content = MockContent()
        
        class MockContent:
            def __init__(self):
                self.parts = [MockPart()]
        
        class MockPart:
            def __init__(self):
                self.text = '{"summary": "Mock analysis complete", "action_plan": ["Take immediate action", "Monitor the situation", "Deploy additional resources"]}'
        
        return MockResponse()
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Mock message processing"""
        responses = [
            "I'm analyzing the current situation. All systems are operational.",
            "Based on the data, I recommend monitoring the main entrance area.",
            "I've processed your request. The security team has been notified.",
            "Current crowd levels are within normal parameters.",
            "I've identified potential areas of concern and dispatched appropriate units."
        ]
        
        import random
        return {
            "response": random.choice(responses),
            "confidence": 0.92,
            "suggestions": [
                "Check camera feeds for the main entrance",
                "Review recent incident reports",
                "Monitor crowd density trends"
            ]
        }
    
    async def generate_contextual_response(self, user_message: str, context_data: Dict[str, Any]) -> str:
        """Mock contextual response generation"""
        responses = [
            "I'm analyzing the current situation based on the provided context. All systems appear operational.",
            f"Based on recent incident data, I recommend monitoring high-traffic areas closely.",
            "I've reviewed the context and suggest deploying additional security units to main entrance.",
            "Current security posture looks good. I'll continue monitoring for any anomalies.",
            "Processing your request with current context. Recommendations will be provided shortly."
        ]
        
        import random
        return random.choice(responses)
    
    async def generate_json_response(self, prompt: str) -> Dict[str, Any]:
        """Mock JSON response generation"""
        return {
            "summary": "Security incident detected and analyzed. Immediate response recommended.",
            "action_plan": [
                "Deploy security personnel to affected area",
                "Monitor situation closely via camera feeds",
                "Prepare emergency response team if needed"
            ]
        }

class MockDispatchService:
    """Mock Dispatch Service"""
    
    async def dispatch_unit(self, incident_id: str, unit_type: str, priority: str) -> Dict[str, Any]:
        """Mock unit dispatch"""
        return {
            "dispatch_id": f"dispatch-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "incident_id": incident_id,
            "unit_type": unit_type,
            "priority": priority,
            "status": "dispatched",
            "eta": "5-8 minutes",
            "timestamp": datetime.now().isoformat()
        }
    
    async def dispatch_units(self, incident_id: str, unit_ids: List[str], priority: str, instructions: Optional[str] = None) -> Dict[str, Any]:
        """Mock multiple units dispatch"""
        return {
            "dispatch_id": f"dispatch-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "incident_id": incident_id,
            "units_dispatched": unit_ids,
            "priority": priority,
            "instructions": instructions,
            "status": "dispatched",
            "estimated_arrival": "5-8 minutes",
            "timestamp": datetime.now().isoformat()
        }

class MockForecastingService:
    """Mock Forecasting Service"""
    
    async def predict_crowd_density(self, location: str, time_horizon_hours: int) -> Dict[str, Any]:
        """Mock crowd density prediction"""
        import random
        
        # Generate mock forecast data
        hours = []
        predictions = []
        
        for i in range(time_horizon_hours):
            hour = (datetime.now().hour + i) % 24
            hours.append(f"{hour:02d}:00")
            predictions.append(round(random.uniform(0.2, 0.8), 2))
        
        return {
            "location": location,
            "forecast": {
                "hours": hours,
                "crowd_density": predictions,
                "confidence": 0.78
            },
            "recommendations": [
                f"Monitor {location} closely during peak hours",
                "Consider additional staff deployment",
                "Review historical patterns for validation"
            ],
            "generated_at": datetime.now().isoformat()
        }
