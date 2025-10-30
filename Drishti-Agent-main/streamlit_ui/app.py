"""
Drishti Command Center - Streamlit UI
AI-Powered Crowd Management System Interface
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh
import os
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "13.0603"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "77.4744"))
DEFAULT_ZOOM = int(os.getenv("DEFAULT_ZOOM", "15"))

# Page configuration
st.set_page_config(
    page_title="Drishti Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .incident-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .severity-high {
        border-left: 4px solid #ff4444;
    }
    .severity-medium {
        border-left: 4px solid #ffaa00;
    }
    .severity-low {
        border-left: 4px solid #00aa00;
    }
    .status-active {
        color: #ff4444;
        font-weight: bold;
    }
    .status-dispatched {
        color: #ffaa00;
        font-weight: bold;
    }
    .status-resolved {
        color: #00aa00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class DrishtiAPI:
    """API client for Drishti backend"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        
    def get_system_status(self):
        """Get system status"""
        try:
            response = requests.get(f"{self.base_url}/system/status", timeout=5)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def get_dashboard_data(self):
        """Get dashboard analytics"""
        try:
            response = requests.get(f"{self.base_url}/analytics/dashboard", timeout=10)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def get_incidents(self, status=None, limit=50):
        """Get incidents list"""
        try:
            url = f"{self.base_url}/incidents"
            params = {"limit": limit}
            if status:
                params["status"] = status
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def get_security_units(self):
        """Get security units"""
        try:
            response = requests.get(f"{self.base_url}/security-units", timeout=10)
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def trigger_anomaly(self, anomaly_type):
        """Trigger a test anomaly"""
        try:
            payload = {
                "anomaly_type": anomaly_type,
                "location": {
                    "latitude": DEFAULT_LAT,
                    "longitude": DEFAULT_LON
                },
                "confidence": 0.95,
                "video_url": f"gs://incident-videos-hackathon/anomaly_clips/{anomaly_type.lower().replace(' ', '_')}_demo.mp4"
            }
            response = requests.post(f"{self.base_url}/trigger-anomaly", json=payload, timeout=10)
            return response.status_code == 202
        except:
            return False
    
    def resolve_incident(self, incident_id):
        """Resolve an incident"""
        try:
            response = requests.post(f"{self.base_url}/incidents/{incident_id}/resolve", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def get_zone_briefing(self):
        """Get AI zone status briefing"""
        try:
            response = requests.get(f"{self.base_url}/analytics/zone-briefing", timeout=15)
            return response.json() if response.status_code == 200 else None
        except:
            return None

# Initialize API client
api = DrishtiAPI(API_BASE_URL)

def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🛡️ Drishti Command Center</h1>', unsafe_allow_html=True)
    st.markdown("**AI-Powered Crowd Management System**")
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/ffffff?text=DRISHTI", caption="AI Surveillance System")
        
        selected = option_menu(
            "Navigation",
            ["🏠 Dashboard", "📊 Analytics", "🚨 Incidents", "👮 Units", "🧠 AI Briefing", "⚙️ Controls"],
            icons=['house', 'bar-chart', 'exclamation-triangle', 'people', 'robot', 'gear'],
            menu_icon="cast",
            default_index=0,
        )
        
        # System status in sidebar
        st.divider()
        status = api.get_system_status()
        if status:
            st.success("🟢 System Online")
            st.metric("Backend", status.get("status", "Unknown"))
        else:
            st.error("🔴 System Offline")
    
    # Main content based on selection
    if selected == "🏠 Dashboard":
        show_dashboard()
    elif selected == "📊 Analytics":
        show_analytics()
    elif selected == "🚨 Incidents":
        show_incidents()
    elif selected == "👮 Units":
        show_units()
    elif selected == "🧠 AI Briefing":
        show_ai_briefing()
    elif selected == "⚙️ Controls":
        show_controls()

def show_dashboard():
    """Main dashboard view"""
    
    # Auto-refresh
    count = st_autorefresh(interval=5000, key="dashboard_refresh")
    
    st.header("📊 Live Dashboard")
    
    # Get dashboard data
    with st.spinner("Loading dashboard data..."):
        dashboard_data = api.get_dashboard_data()
    
    if not dashboard_data:
        st.error("❌ Unable to connect to backend. Please check if the backend is running.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚨 Active Incidents",
            value=dashboard_data.get("total_active_incidents", 0),
            delta=dashboard_data.get("new_incidents_last_hour", 0)
        )
    
    with col2:
        st.metric(
            label="👮 Available Units",
            value=dashboard_data.get("available_units", 0),
            delta=dashboard_data.get("units_status_change", 0)
        )
    
    with col3:
        st.metric(
            label="⚠️ High Severity",
            value=dashboard_data.get("high_severity_incidents", 0)
        )
    
    with col4:
        st.metric(
            label="📈 Response Rate",
            value=f"{dashboard_data.get('avg_response_time', 0):.1f}s"
        )
    
    st.divider()
    
    # Map and recent incidents
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Live Incident Map")
        show_incident_map()
    
    with col2:
        st.subheader("⚡ Recent Activity")
        recent_incidents = api.get_incidents(limit=5)
        
        if recent_incidents:
            for incident in recent_incidents[:5]:
                severity_class = f"severity-{incident.get('severity', 'low')}"
                with st.container():
                    st.markdown(f"""
                    <div class="incident-card {severity_class}">
                        <strong>{incident.get('incident_type', 'Unknown')}</strong><br>
                        <small>📍 {incident.get('location', {}).get('address', 'Unknown location')}</small><br>
                        <small>🕒 {incident.get('timestamp', 'Unknown time')}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No recent incidents")

def show_analytics():
    """Analytics view"""
    
    st.header("📊 Analytics & Insights")
    
    # Get data
    dashboard_data = api.get_dashboard_data()
    incidents = api.get_incidents(limit=100)
    
    if not dashboard_data:
        st.error("Unable to load analytics data")
        return
    
    # Incidents over time
    if incidents:
        df = pd.DataFrame(incidents)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Incidents by Hour")
                hourly_counts = df.groupby('hour').size()
                fig = px.bar(
                    x=hourly_counts.index,
                    y=hourly_counts.values,
                    labels={'x': 'Hour', 'y': 'Incidents'},
                    title="Incident Distribution by Hour"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🎯 Incidents by Type")
                if 'incident_type' in df.columns:
                    type_counts = df['incident_type'].value_counts()
                    fig = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        title="Incident Types Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Severity analysis
            st.subheader("⚠️ Severity Analysis")
            if 'severity' in df.columns:
                severity_counts = df['severity'].value_counts()
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🔴 High", severity_counts.get('high', 0))
                with col2:
                    st.metric("🟡 Medium", severity_counts.get('medium', 0))
                with col3:
                    st.metric("🟢 Low", severity_counts.get('low', 0))

def show_incidents():
    """Incidents management view"""
    
    # Auto-refresh
    count = st_autorefresh(interval=3000, key="incidents_refresh")
    
    st.header("🚨 Incident Management")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "active", "dispatched", "resolved"]
        )
    
    with col2:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All", "high", "medium", "low"]
        )
    
    with col3:
        limit = st.number_input("Max incidents", min_value=10, max_value=100, value=50)
    
    # Get incidents
    incidents = api.get_incidents(
        status=status_filter if status_filter != "All" else None,
        limit=limit
    )
    
    if incidents:
        for incident in incidents:
            severity = incident.get('severity', 'low')
            status = incident.get('status', 'unknown')
            
            with st.expander(f"🚨 {incident.get('incident_type', 'Unknown')} - {severity.upper()} ({status.upper()})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**ID:** {incident.get('incident_id', 'N/A')}")
                    st.write(f"**Type:** {incident.get('incident_type', 'Unknown')}")
                    st.write(f"**Location:** {incident.get('location', {}).get('address', 'Unknown')}")
                    st.write(f"**Time:** {incident.get('timestamp', 'Unknown')}")
                    st.write(f"**Confidence:** {incident.get('confidence', 0):.2%}")
                    
                    if incident.get('analysis_summary'):
                        st.write(f"**Analysis:** {incident['analysis_summary']}")
                
                with col2:
                    st.write(f"**Status:** {status.upper()}")
                    st.write(f"**Severity:** {severity.upper()}")
                    
                    if status == 'active':
                        if st.button(f"Resolve", key=f"resolve_{incident.get('incident_id')}"):
                            if api.resolve_incident(incident.get('incident_id')):
                                st.success("Incident resolved!")
                                st.rerun()
                            else:
                                st.error("Failed to resolve incident")
                    
                    if incident.get('dispatched_units'):
                        st.write("**Dispatched Units:**")
                        for unit in incident['dispatched_units']:
                            st.write(f"- {unit}")
    else:
        st.info("No incidents found")

def show_units():
    """Security units management"""
    
    # Auto-refresh
    count = st_autorefresh(interval=5000, key="units_refresh")
    
    st.header("👮 Security Units")
    
    # Get units
    units = api.get_security_units()
    
    if units:
        # Units summary
        available = sum(1 for unit in units if unit.get('status') == 'available')
        dispatched = sum(1 for unit in units if unit.get('status') == 'dispatched')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🟢 Available", available)
        with col2:
            st.metric("🟡 Dispatched", dispatched)
        with col3:
            st.metric("👮 Total Units", len(units))
        
        st.divider()
        
        # Units list
        for unit in units:
            status = unit.get('status', 'unknown')
            status_emoji = {"available": "🟢", "dispatched": "🟡", "offline": "🔴"}.get(status, "⚪")
            
            with st.expander(f"{status_emoji} {unit.get('unit_id', 'Unknown')} - {status.upper()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Unit ID:** {unit.get('unit_id', 'N/A')}")
                    st.write(f"**Name:** {unit.get('name', 'Unknown')}")
                    st.write(f"**Type:** {unit.get('unit_type', 'Unknown')}")
                    st.write(f"**Location:** {unit.get('current_location', {}).get('address', 'Unknown')}")
                
                with col2:
                    st.write(f"**Status:** {status.upper()}")
                    if unit.get('assigned_incident'):
                        st.write(f"**Assigned to:** {unit['assigned_incident']}")
                    if unit.get('eta'):
                        st.write(f"**ETA:** {unit['eta']} min")
    else:
        st.info("No security units available")

def show_ai_briefing():
    """AI Zone Briefing"""
    
    st.header("🧠 AI Zone Status Briefing")
    
    if st.button("🔄 Generate New Briefing", type="primary"):
        with st.spinner("Generating AI briefing... This may take a moment."):
            briefing = api.get_zone_briefing()
            
            if briefing:
                st.success("✅ Briefing generated successfully!")
                
                # Display briefing sections
                if briefing.get('zone_status'):
                    st.subheader("📍 Zone Status")
                    st.write(briefing['zone_status'])
                
                if briefing.get('threat_assessment'):
                    st.subheader("⚠️ Threat Assessment")
                    st.write(briefing['threat_assessment'])
                
                if briefing.get('resource_status'):
                    st.subheader("👮 Resource Status")
                    st.write(briefing['resource_status'])
                
                if briefing.get('recommendations'):
                    st.subheader("💡 Recommendations")
                    st.write(briefing['recommendations'])
                
                if briefing.get('priority_actions'):
                    st.subheader("🎯 Priority Actions")
                    for action in briefing['priority_actions']:
                        st.write(f"• {action}")
                
                # Metadata
                st.divider()
                st.caption(f"Generated at: {briefing.get('timestamp', 'Unknown')}")
                st.caption(f"Analysis period: {briefing.get('analysis_period', 'Unknown')}")
            else:
                st.error("❌ Failed to generate briefing. Please try again.")
    else:
        st.info("Click the button above to generate an AI-powered zone status briefing.")

def show_controls():
    """System controls and testing"""
    
    st.header("⚙️ System Controls")
    
    # Test anomaly triggers
    st.subheader("🧪 Test Anomaly Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 High Crowd Density", type="secondary"):
            if api.trigger_anomaly("High Crowd Density"):
                st.success("✅ High crowd density anomaly triggered!")
            else:
                st.error("❌ Failed to trigger anomaly")
        
        if st.button("👤 Suspicious Activity", type="secondary"):
            if api.trigger_anomaly("Suspicious Activity"):
                st.success("✅ Suspicious activity anomaly triggered!")
            else:
                st.error("❌ Failed to trigger anomaly")
    
    with col2:
        if st.button("🏃 Crowd Surge", type="secondary"):
            if api.trigger_anomaly("Crowd Surge"):
                st.success("✅ Crowd surge anomaly triggered!")
            else:
                st.error("❌ Failed to trigger anomaly")
        
        if st.button("🚫 Unauthorized Access", type="secondary"):
            if api.trigger_anomaly("Unauthorized Access"):
                st.success("✅ Unauthorized access anomaly triggered!")
            else:
                st.error("❌ Failed to trigger anomaly")
    
    st.divider()
    
    # System information
    st.subheader("ℹ️ System Information")
    
    status = api.get_system_status()
    if status:
        st.json(status)
    else:
        st.error("Unable to retrieve system status")

def show_incident_map():
    """Show incidents on a map"""
    
    # Create base map
    m = folium.Map(
        location=[DEFAULT_LAT, DEFAULT_LON],
        zoom_start=DEFAULT_ZOOM,
        tiles='OpenStreetMap'
    )
    
    # Get recent incidents
    incidents = api.get_incidents(limit=20)
    
    # Add incidents to map
    for incident in incidents:
        location = incident.get('location', {})
        if location.get('latitude') and location.get('longitude'):
            # Color by severity
            color_map = {
                'high': 'red',
                'medium': 'orange',
                'low': 'green'
            }
            color = color_map.get(incident.get('severity', 'low'), 'blue')
            
            # Add marker
            folium.Marker(
                location=[location['latitude'], location['longitude']],
                popup=f"""
                <b>{incident.get('incident_type', 'Unknown')}</b><br>
                Severity: {incident.get('severity', 'Unknown')}<br>
                Status: {incident.get('status', 'Unknown')}<br>
                Time: {incident.get('timestamp', 'Unknown')}
                """,
                icon=folium.Icon(color=color, icon='exclamation-sign')
            ).add_to(m)
    
    # Display map
    st_folium(m, width=700, height=400)

if __name__ == "__main__":
    main()
