"""
Drishti API Client
Handle all API communication with the backend
"""

import requests
import streamlit as st
from typing import Dict, List, Optional, Any
import logging
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DrishtiAPIClient:
    """API client for Drishti backend communication"""
    
    def __init__(self, base_url: str = None, timeout: int = 10):
        self.base_url = base_url or config.API_BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Drishti-Streamlit-UI/1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            # Log request details
            logger.info(f"{method} {url} - Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 202:
                return {"status": "accepted", "message": "Request accepted"}
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {method} {url}")
            st.error("⏱️ Request timed out. Please try again.")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {method} {url}")
            st.error("🔌 Cannot connect to backend. Please check if the backend is running.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {method} {url}: {str(e)}")
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            return None
    
    def get_system_status(self) -> Optional[Dict]:
        """Get system status"""
        return self._make_request('GET', 'system/status')
    
    def get_health_check(self) -> Optional[Dict]:
        """Perform health check"""
        return self._make_request('GET', '../health')
    
    def get_dashboard_data(self) -> Optional[Dict]:
        """Get dashboard analytics data"""
        return self._make_request('GET', 'analytics/dashboard')
    
    def get_incidents(self, status: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get incidents list with optional filtering"""
        params = {'limit': limit, 'offset': offset}
        if status and status != 'All':
            params['status'] = status
        
        result = self._make_request('GET', 'incidents', params=params)
        return result if isinstance(result, list) else []
    
    def get_incident_by_id(self, incident_id: str) -> Optional[Dict]:
        """Get specific incident by ID"""
        return self._make_request('GET', f'incidents/{incident_id}')
    
    def resolve_incident(self, incident_id: str) -> bool:
        """Resolve an incident"""
        result = self._make_request('POST', f'incidents/{incident_id}/resolve')
        return result is not None
    
    def get_security_units(self, status: str = None) -> List[Dict]:
        """Get security units list"""
        params = {}
        if status and status != 'All':
            params['status'] = status
        
        result = self._make_request('GET', 'security-units', params=params)
        return result if isinstance(result, list) else []
    
    def get_unit_by_id(self, unit_id: str) -> Optional[Dict]:
        """Get specific unit by ID"""
        return self._make_request('GET', f'security-units/{unit_id}')
    
    def dispatch_unit(self, unit_id: str, incident_id: str) -> bool:
        """Dispatch a unit to an incident"""
        payload = {'incident_id': incident_id}
        result = self._make_request('POST', f'security-units/{unit_id}/dispatch', json=payload)
        return result is not None
    
    def trigger_anomaly(self, anomaly_data: Dict) -> bool:
        """Trigger a test anomaly"""
        result = self._make_request('POST', 'trigger-anomaly', json=anomaly_data)
        return result is not None
    
    def simulate_anomaly(self, anomaly_type: str) -> bool:
        """Simulate a specific type of anomaly for testing"""
        payload = {
            "anomaly_type": anomaly_type,
            "location": {
                "latitude": config.DEFAULT_LAT,
                "longitude": config.DEFAULT_LON,
                "address": "Test Location - Bangalore"
            },
            "confidence": 0.95,
            "video_url": f"gs://incident-videos-hackathon/anomaly_clips/{anomaly_type.lower().replace(' ', '_')}_demo.mp4",
            "metadata": {
                "source": "streamlit_ui_test",
                "test_mode": True
            }
        }
        return self.trigger_anomaly(payload)
    
    def get_zone_briefing(self) -> Optional[Dict]:
        """Get AI-generated zone status briefing"""
        return self._make_request('GET', 'analytics/zone-briefing')
    
    def get_analytics_summary(self, period: str = '24h') -> Optional[Dict]:
        """Get analytics summary for a specific period"""
        params = {'period': period}
        return self._make_request('GET', 'analytics/summary', params=params)
    
    def get_dispatches(self, limit: int = 50) -> List[Dict]:
        """Get dispatch history"""
        params = {'limit': limit}
        result = self._make_request('GET', 'dispatches', params=params)
        return result if isinstance(result, list) else []
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get system alerts"""
        params = {'limit': limit}
        result = self._make_request('GET', 'alerts', params=params)
        return result if isinstance(result, list) else []
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        result = self._make_request('POST', f'alerts/{alert_id}/acknowledge')
        return result is not None
    
    def get_performance_metrics(self) -> Optional[Dict]:
        """Get system performance metrics"""
        return self._make_request('GET', 'analytics/performance')
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            result = self.get_health_check()
            return result is not None
        except Exception:
            return False

# Create a global API client instance
@st.cache_resource
def get_api_client():
    """Get cached API client instance"""
    return DrishtiAPIClient()

# Helper functions for common operations
def check_backend_connection():
    """Check if backend is accessible"""
    client = get_api_client()
    return client.test_connection()

def get_system_health():
    """Get comprehensive system health information"""
    client = get_api_client()
    
    health_data = {
        'backend_connected': False,
        'system_status': None,
        'health_check': None,
        'last_check': None
    }
    
    try:
        # Test connection
        health_data['backend_connected'] = client.test_connection()
        
        if health_data['backend_connected']:
            # Get system status
            health_data['system_status'] = client.get_system_status()
            health_data['health_check'] = client.get_health_check()
        
        from datetime import datetime
        health_data['last_check'] = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    return health_data
