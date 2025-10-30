"""
Drishti Configuration Management
Handle environment variables and configuration settings
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Drishti Streamlit UI"""
    
    # Backend API Configuration
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    
    # Streamlit Configuration
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # Map Configuration
    DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "13.0603"))
    DEFAULT_LON = float(os.getenv("DEFAULT_LON", "77.4744"))
    DEFAULT_ZOOM = int(os.getenv("DEFAULT_ZOOM", "15"))
    
    # Auto-refresh intervals (milliseconds)
    DASHBOARD_REFRESH = int(os.getenv("DASHBOARD_REFRESH", "5")) * 1000
    INCIDENTS_REFRESH = int(os.getenv("INCIDENTS_REFRESH", "3")) * 1000
    UNITS_REFRESH = int(os.getenv("UNITS_REFRESH", "5")) * 1000
    
    # UI Settings
    PAGE_TITLE = "Drishti Command Center"
    PAGE_ICON = "🛡️"
    LAYOUT = "wide"
    
    # Color scheme
    COLORS = {
        'primary': '#1f77b4',
        'success': '#00aa00',
        'warning': '#ffaa00',
        'danger': '#ff4444',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40'
    }
    
    # Severity colors
    SEVERITY_COLORS = {
        'high': '#ff4444',
        'medium': '#ffaa00',
        'low': '#00aa00'
    }
    
    # Status colors
    STATUS_COLORS = {
        'active': '#ff4444',
        'dispatched': '#ffaa00',
        'resolved': '#00aa00',
        'available': '#00aa00',
        'offline': '#ff4444'
    }
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Get full API URL for an endpoint"""
        return f"{cls.API_BASE_URL}/{endpoint.lstrip('/')}"
    
    @classmethod
    def get_color(cls, color_type: str, fallback: str = '#cccccc') -> str:
        """Get color from color scheme"""
        return cls.COLORS.get(color_type, fallback)
    
    @classmethod
    def get_severity_color(cls, severity: str) -> str:
        """Get color for incident severity"""
        return cls.SEVERITY_COLORS.get(severity.lower(), '#cccccc')
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        """Get color for status"""
        return cls.STATUS_COLORS.get(status.lower(), '#cccccc')
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'backend_url': cls.BACKEND_URL,
            'api_base_url': cls.API_BASE_URL,
            'streamlit_port': cls.STREAMLIT_PORT,
            'default_location': {
                'lat': cls.DEFAULT_LAT,
                'lon': cls.DEFAULT_LON,
                'zoom': cls.DEFAULT_ZOOM
            },
            'refresh_intervals': {
                'dashboard': cls.DASHBOARD_REFRESH,
                'incidents': cls.INCIDENTS_REFRESH,
                'units': cls.UNITS_REFRESH
            }
        }

# Export configuration instance
config = Config()
