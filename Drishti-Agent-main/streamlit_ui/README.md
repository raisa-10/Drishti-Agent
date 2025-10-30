# Drishti Streamlit UI

A comprehensive web interface for the Drishti AI-Powered Crowd Management System.

## Features

### 🏠 Dashboard
- **Real-time System Overview**: Live metrics for incidents, units, and system status
- **Interactive Map**: Visual representation of incidents and security units
- **Key Performance Indicators**: Response times, active incidents, and resource availability
- **Auto-refresh**: Automatically updates every 5 seconds

### 📊 Analytics
- **Incident Analytics**: Trends, patterns, and distribution analysis
- **Performance Metrics**: Response time analysis and system efficiency
- **Historical Data**: Time-series analysis of incidents and responses
- **Visual Charts**: Interactive plots using Plotly

### 🚨 Incident Management
- **Live Incident Feed**: Real-time list of all incidents with auto-refresh
- **Status Filtering**: Filter by incident status (active, dispatched, resolved)
- **Severity Analysis**: Color-coded severity levels (high, medium, low)
- **Quick Actions**: Resolve incidents directly from the interface
- **Detailed Views**: Expandable cards with full incident information

### 👮 Security Units
- **Unit Status Monitoring**: Real-time status of all security units
- **Location Tracking**: Current position and assignment status
- **Availability Overview**: Available, dispatched, and offline units
- **Assignment Details**: Which units are assigned to which incidents

### 🧠 AI Zone Briefing
- **AI-Powered Analysis**: Comprehensive zone status analysis using Gemini AI
- **Threat Assessment**: Current threat levels and risk analysis
- **Resource Recommendations**: AI suggestions for optimal resource allocation
- **Strategic Insights**: Professional briefings for command decision-making

### ⚙️ System Controls
- **Test Anomaly Triggers**: Simulate different types of incidents for testing
- **System Information**: Backend status and configuration details
- **Emergency Controls**: Quick access to critical system functions

## Installation

### Prerequisites
- Python 3.8+
- pip
- Access to Drishti backend API

### Quick Start

1. **Navigate to the UI directory**:
   ```bash
   cd streamlit_ui
   ```

2. **Run the startup script**:
   ```bash
   ./run.sh
   ```

3. **Access the application**:
   Open your browser and go to `http://localhost:8501`

### Manual Installation

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Backend API Configuration
BACKEND_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000/api/v1

# Streamlit Configuration
STREAMLIT_PORT=8501

# Map Configuration
DEFAULT_LAT=13.0603
DEFAULT_LON=77.4744
DEFAULT_ZOOM=15

# Auto-refresh intervals (seconds)
DASHBOARD_REFRESH=5
INCIDENTS_REFRESH=3
UNITS_REFRESH=5
```

### Backend Integration

The Streamlit UI connects to the Drishti backend API. Ensure the backend is running before starting the UI.

**Default backend URL**: `http://localhost:8000`

## Usage

### Navigation

Use the sidebar menu to navigate between different sections:

- **🏠 Dashboard**: Main overview and live map
- **📊 Analytics**: Charts and performance metrics
- **🚨 Incidents**: Incident management and resolution
- **👮 Units**: Security unit monitoring
- **🧠 AI Briefing**: AI-powered zone analysis
- **⚙️ Controls**: System controls and testing

### Auto-refresh

Most sections automatically refresh to show real-time data:
- Dashboard: Every 5 seconds
- Incidents: Every 3 seconds
- Units: Every 5 seconds

### Testing

Use the **Controls** section to trigger test anomalies:
- High Crowd Density
- Suspicious Activity
- Crowd Surge
- Unauthorized Access

## Architecture

### Components

- **`app.py`**: Main Streamlit application
- **`api_client.py`**: Backend API communication
- **`components.py`**: Reusable UI components
- **`config.py`**: Configuration management

### Dependencies

- **Streamlit**: Web framework
- **Requests**: HTTP client for API calls
- **Pandas**: Data manipulation
- **Plotly**: Interactive charts
- **Folium**: Interactive maps
- **Streamlit-Folium**: Folium integration

## Features in Detail

### Real-time Dashboard
- Live incident count and severity breakdown
- Available security units status
- Response time metrics
- Interactive map with incident markers

### Incident Analytics
- Time series analysis of incident patterns
- Severity distribution charts
- Incident type breakdown
- Response time analysis

### AI Integration
- Gemini AI-powered zone briefings
- Threat assessment analysis
- Resource allocation recommendations
- Strategic decision support

### Interactive Map
- Real-time incident locations
- Security unit positions
- Color-coded severity indicators
- Detailed popup information

## Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Ensure the Drishti backend is running
   - Check the `BACKEND_URL` in your `.env` file
   - Verify network connectivity

2. **Map Not Loading**
   - Check internet connection (required for map tiles)
   - Verify latitude/longitude coordinates

3. **Data Not Refreshing**
   - Check auto-refresh settings
   - Ensure backend API is responding
   - Check browser console for errors

### Logs

The application logs API requests and errors. Check the terminal output for debugging information.

## Development

### Adding New Features

1. **Create new components** in `components.py`
2. **Add API methods** in `api_client.py`
3. **Update main app** in `app.py`
4. **Configure settings** in `config.py`

### Testing

Use the built-in testing features in the Controls section to simulate various scenarios without affecting real data.

## Security

- The UI connects to the backend API over HTTP/HTTPS
- No sensitive data is stored in the browser
- All API calls include proper error handling
- Environment variables protect configuration secrets

## Support

For issues and feature requests, please refer to the main Drishti project documentation.

---

**Drishti Command Center** - AI-Powered Crowd Management System UI
Version 1.0.0
