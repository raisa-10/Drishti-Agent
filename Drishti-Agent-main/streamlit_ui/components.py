"""
Drishti Streamlit UI Components
Reusable components for the Streamlit interface
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

def incident_card(incident):
    """Render an incident card"""
    severity = incident.get('severity', 'low')
    status = incident.get('status', 'unknown')
    
    # Severity colors
    severity_colors = {
        'high': '#ff4444',
        'medium': '#ffaa00',
        'low': '#00aa00'
    }
    
    # Status colors
    status_colors = {
        'active': '#ff4444',
        'dispatched': '#ffaa00',
        'resolved': '#00aa00'
    }
    
    with st.container():
        st.markdown(f"""
        <div style="
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid {severity_colors.get(severity, '#cccccc')};
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #333;">{incident.get('incident_type', 'Unknown Incident')}</h4>
                <span style="
                    background-color: {status_colors.get(status, '#cccccc')};
                    color: white;
                    padding: 0.2rem 0.5rem;
                    border-radius: 0.3rem;
                    font-size: 0.8rem;
                    font-weight: bold;
                ">{status.upper()}</span>
            </div>
            <p style="margin: 0.5rem 0; color: #666;">
                📍 {incident.get('location', {}).get('address', 'Unknown location')}
            </p>
            <p style="margin: 0.5rem 0; color: #666;">
                🕒 {incident.get('timestamp', 'Unknown time')}
            </p>
            <p style="margin: 0; color: #666;">
                ⚠️ Severity: <strong style="color: {severity_colors.get(severity, '#cccccc')};">{severity.upper()}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

def unit_status_card(unit):
    """Render a security unit status card"""
    status = unit.get('status', 'unknown')
    
    # Status colors and icons
    status_config = {
        'available': {'color': '#00aa00', 'icon': '🟢'},
        'dispatched': {'color': '#ffaa00', 'icon': '🟡'},
        'offline': {'color': '#ff4444', 'icon': '🔴'}
    }
    
    config = status_config.get(status, {'color': '#cccccc', 'icon': '⚪'})
    
    with st.container():
        st.markdown(f"""
        <div style="
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid {config['color']};
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #333;">{config['icon']} {unit.get('name', 'Unknown Unit')}</h4>
                <span style="
                    background-color: {config['color']};
                    color: white;
                    padding: 0.2rem 0.5rem;
                    border-radius: 0.3rem;
                    font-size: 0.8rem;
                    font-weight: bold;
                ">{status.upper()}</span>
            </div>
            <p style="margin: 0.5rem 0; color: #666;">
                🆔 {unit.get('unit_id', 'Unknown ID')}
            </p>
            <p style="margin: 0.5rem 0; color: #666;">
                📍 {unit.get('current_location', {}).get('address', 'Unknown location')}
            </p>
            {f'<p style="margin: 0; color: #666;">🚨 Assigned: {unit["assigned_incident"]}</p>' if unit.get('assigned_incident') else ''}
        </div>
        """, unsafe_allow_html=True)

def metrics_row(metrics_data):
    """Render a row of metrics"""
    cols = st.columns(len(metrics_data))
    
    for i, (label, value, delta, icon) in enumerate(metrics_data):
        with cols[i]:
            st.metric(
                label=f"{icon} {label}",
                value=value,
                delta=delta if delta is not None else None
            )

def incident_timeline_chart(incidents):
    """Create an incident timeline chart"""
    if not incidents:
        return None
    
    df = pd.DataFrame(incidents)
    if 'timestamp' not in df.columns:
        return None
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Group by date and count incidents
    daily_counts = df.groupby('date').size().reset_index(name='count')
    
    fig = px.line(
        daily_counts,
        x='date',
        y='count',
        title='Incidents Over Time',
        labels={'date': 'Date', 'count': 'Number of Incidents'}
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Incidents",
        hovermode='x unified'
    )
    
    return fig

def severity_distribution_chart(incidents):
    """Create a severity distribution pie chart"""
    if not incidents:
        return None
    
    df = pd.DataFrame(incidents)
    if 'severity' not in df.columns:
        return None
    
    severity_counts = df['severity'].value_counts()
    
    colors = {
        'high': '#ff4444',
        'medium': '#ffaa00',
        'low': '#00aa00'
    }
    
    fig = px.pie(
        values=severity_counts.values,
        names=severity_counts.index,
        title='Incident Severity Distribution',
        color=severity_counts.index,
        color_discrete_map=colors
    )
    
    return fig

def incident_type_chart(incidents):
    """Create an incident type bar chart"""
    if not incidents:
        return None
    
    df = pd.DataFrame(incidents)
    if 'incident_type' not in df.columns:
        return None
    
    type_counts = df['incident_type'].value_counts()
    
    fig = px.bar(
        x=type_counts.values,
        y=type_counts.index,
        orientation='h',
        title='Incidents by Type',
        labels={'x': 'Count', 'y': 'Incident Type'}
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def response_time_chart(incidents):
    """Create a response time analysis chart"""
    if not incidents:
        return None
    
    # This would need response time data from the backend
    # For now, simulate some data
    df = pd.DataFrame(incidents)
    if len(df) < 2:
        return None
    
    # Simulate response times
    import random
    df['response_time'] = [random.randint(60, 600) for _ in range(len(df))]
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = px.scatter(
        df,
        x='timestamp',
        y='response_time',
        color='severity',
        title='Response Time Analysis',
        labels={'response_time': 'Response Time (seconds)', 'timestamp': 'Time'}
    )
    
    return fig

def interactive_map(incidents=None, units=None, center_lat=13.0603, center_lon=77.4744):
    """Create an interactive map with incidents and units"""
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles='OpenStreetMap'
    )
    
    # Add incidents
    if incidents:
        for incident in incidents:
            location = incident.get('location', {})
            if location.get('latitude') and location.get('longitude'):
                severity = incident.get('severity', 'low')
                
                color_map = {
                    'high': 'red',
                    'medium': 'orange',
                    'low': 'green'
                }
                
                folium.Marker(
                    location=[location['latitude'], location['longitude']],
                    popup=folium.Popup(f"""
                        <div style="width: 200px;">
                            <h4>{incident.get('incident_type', 'Unknown')}</h4>
                            <p><strong>Severity:</strong> {severity}</p>
                            <p><strong>Status:</strong> {incident.get('status', 'Unknown')}</p>
                            <p><strong>Time:</strong> {incident.get('timestamp', 'Unknown')}</p>
                            <p><strong>Location:</strong> {location.get('address', 'Unknown')}</p>
                        </div>
                    """, max_width=250),
                    icon=folium.Icon(
                        color=color_map.get(severity, 'blue'),
                        icon='exclamation-sign'
                    )
                ).add_to(m)
    
    # Add security units
    if units:
        for unit in units:
            location = unit.get('current_location', {})
            if location.get('latitude') and location.get('longitude'):
                status = unit.get('status', 'unknown')
                
                color_map = {
                    'available': 'green',
                    'dispatched': 'orange',
                    'offline': 'red'
                }
                
                folium.Marker(
                    location=[location['latitude'], location['longitude']],
                    popup=folium.Popup(f"""
                        <div style="width: 200px;">
                            <h4>{unit.get('name', 'Unknown Unit')}</h4>
                            <p><strong>ID:</strong> {unit.get('unit_id', 'Unknown')}</p>
                            <p><strong>Status:</strong> {status}</p>
                            <p><strong>Type:</strong> {unit.get('unit_type', 'Unknown')}</p>
                            <p><strong>Location:</strong> {location.get('address', 'Unknown')}</p>
                        </div>
                    """, max_width=250),
                    icon=folium.Icon(
                        color=color_map.get(status, 'gray'),
                        icon='user'
                    )
                ).add_to(m)
    
    return m

def create_alert_banner(message, alert_type="info"):
    """Create a custom alert banner"""
    colors = {
        "success": "#d4edda",
        "info": "#d1ecf1",
        "warning": "#fff3cd",
        "error": "#f8d7da"
    }
    
    icons = {
        "success": "✅",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌"
    }
    
    st.markdown(f"""
    <div style="
        background-color: {colors.get(alert_type, colors['info'])};
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    ">
        <strong>{icons.get(alert_type, '•')} {message}</strong>
    </div>
    """, unsafe_allow_html=True)
