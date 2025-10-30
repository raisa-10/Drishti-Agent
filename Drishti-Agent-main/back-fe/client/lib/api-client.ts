// Project Drishti - API Client Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class DrishtiAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // System endpoints
  async getSystemStatus() {
    const response = await fetch(`${this.baseURL}/api/v1/system/status`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async simulateAnomaly(anomaly_type: string, location: string) {
    const response = await fetch(`${this.baseURL}/api/v1/system/simulate-anomaly?anomaly_type=${encodeURIComponent(anomaly_type)}&location=${encodeURIComponent(location)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // Incident endpoints
  async getIncidents() {
    const response = await fetch(`${this.baseURL}/api/v1/incidents`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async getIncident(incidentId: string) {
    const response = await fetch(`${this.baseURL}/api/v1/incidents/${incidentId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async respondToIncident(incidentId: string, action: string, notes?: string, dispatchUnits?: string[]) {
    const response = await fetch(`${this.baseURL}/api/v1/incidents/${incidentId}/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        action, 
        notes: notes || '',
        dispatch_units: dispatchUnits || [],
        priority: 'medium',
        commander_id: 'demo_commander'
      })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // Simulation endpoints
  async triggerEdgeSimulation(videoPath: string, location: any) {
    const response = await fetch(`${this.baseURL}/api/v1/simulate/edge-trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        video_path: videoPath, 
        location,
        detection_types: ['crowd_density', 'suspicious_activity']
      })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // Chat endpoints
  async sendMessage(message: string, sessionId: string = 'default') {
    const response = await fetch(`${this.baseURL}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        content: message, 
        session_id: sessionId,
        context: {}
      })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // Security Unit endpoints
  async getSecurityUnits() {
    const response = await fetch(`${this.baseURL}/api/v1/units`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // Dispatch endpoints
  async dispatchUnits(incidentId: string, unitIds: string[], priority: string = 'medium', instructions?: string) {
    const response = await fetch(`${this.baseURL}/api/v1/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        incident_id: incidentId, 
        unit_ids: unitIds, 
        priority,
        instructions: instructions || '',
        requested_by: 'demo_commander'
      })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // Analytics & Forecasting endpoints
  async getCrowdForecast(location: string = 'main_entrance', hours: number = 4) {
    const response = await fetch(
      `${this.baseURL}/api/v1/analytics/crowd-forecast?location=${encodeURIComponent(location)}&hours=${hours}`
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async getDashboardData() {
    const response = await fetch(`${this.baseURL}/api/v1/analytics/dashboard`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
}

export const api = new DrishtiAPI();
