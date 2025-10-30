import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Backend API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

// Types that match your backend models but compatible with frontend components
export interface Location {
  latitude?: number;
  longitude?: number;
  lat?: number;
  lng?: number;
  name?: string;
}

export interface Alert {
  id: string;
  incident_id?: string;
  alert_type?: string;
  title?: string; // Added for component compatibility
  message?: string; // Added for component compatibility
  severity: 'critical' | 'high' | 'medium' | 'low';
  confidence?: number;
  description?: string;
  requires_response?: boolean;
  timestamp: Date | string; // Allow both Date and string
  status?: 'active' | 'resolved';
  location?: Location;
  acknowledged?: boolean;
}

export interface Incident {
  id: string;
  type?: string;
  title?: string; // Added for component compatibility
  source?: string;
  location: Location;
  status: 'active' | 'processing' | 'responded' | 'resolved' | 'false_alarm' | 'error' | 'investigating'; // Added investigating for compatibility
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  timestamp: Date | string; // Allow both Date and string
  video_path?: string;
  videoUrl?: string; // Added for component compatibility
  assignedAgent?: string; // Added for component compatibility
  commander_response?: any;
  gemini_summary?: string;
  gemini_action_plan?: string[];
  analysis_result?: any;
  metadata?: any;
}

export interface ChatMessage {
  id: string;
  content?: string;
  message?: string; // Added for component compatibility
  sender: 'user' | 'ai';
  timestamp: Date | string; // Allow both Date and string
  session_id?: string;
}

export interface SecurityUnit {
  id: string;
  name: string;
  status: 'available' | 'dispatched' | 'busy' | 'offline' | 'active'; // Added active for compatibility
  location: Location;
  lastSeen: Date | string; // Allow both Date and string  
  type?: string; // Made optional for compatibility
  unit_type?: string;
  capabilities?: string[];
}

export interface SystemStatus {
  overall_status: string;
  components: Record<string, string>;
  metrics: Record<string, any>;
  last_check: string;
}

export interface DispatchRequest {
  incident_id: string;
  unit_ids: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  instructions?: string;
}

export interface ManualCommand {
  command_type?: string;
  action?: string; // Added for component compatibility
  priority: 'low' | 'medium' | 'high' | 'critical';
  dispatch_units?: string[];
  instructions?: string;
  target_location?: string; // Added for component compatibility
  additional_info?: string; // Added for component compatibility
  estimated_resolution_time?: number;
}

export interface DashboardData {
  active_incidents: number;
  todays_incidents: number;
  available_units: number;
  total_units: number;
  recent_alerts: Alert[];
  system_status: string;
  last_updated: string;
}

// HTTP client utility
const apiClient = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async put<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
};
// API service functions - Real backend integration
export const systemApi = {
  getStatus: async (): Promise<SystemStatus> => {
    return apiClient.get<SystemStatus>('/system/status');
  },

  simulateAnomaly: async (anomaly_type: string, location: string): Promise<any> => {
    return apiClient.post('/system/simulate-anomaly', { anomaly_type, location });
  }
};

export const incidentsApi = {
  getIncidents: async (status?: string, limit: number = 50): Promise<Incident[]> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    
    return apiClient.get<Incident[]>(`/incidents?${params.toString()}`);
  },

  getIncident: async (incidentId: string): Promise<Incident> => {
    return apiClient.get<Incident>(`/incidents/${incidentId}`);
  },

  respondToIncident: async (incidentId: string, response: ManualCommand): Promise<any> => {
    return apiClient.post(`/incidents/${incidentId}/respond`, response);
  }
};

export const chatApi = {
  sendMessage: async (content: string, session_id?: string): Promise<{ response: string; timestamp: string }> => {
    return apiClient.post('/chat', { content, session_id });
  }
};

export const securityUnitsApi = {
  getUnits: async (): Promise<SecurityUnit[]> => {
    return apiClient.get<SecurityUnit[]>('/units');
  }
};

export const dispatchApi = {
  manualDispatch: async (request: DispatchRequest): Promise<any> => {
    return apiClient.post('/dispatch', request);
  }
};

export const analyticsApi = {
  getCrowdForecast: async (location: string, hours_ahead: number = 4): Promise<any> => {
    return apiClient.get(`/analytics/crowd-forecast?location=${location}&hours_ahead=${hours_ahead}`);
  },

  getDashboardData: async (): Promise<DashboardData> => {
    return apiClient.get<DashboardData>('/analytics/dashboard');
  }
};

export const locationsApi = {
  getVenueZones: async (): Promise<{ zones: any[]; total: number }> => {
    return apiClient.get('/locations/zones');
  },

  geocodeLocation: async (address: string): Promise<Location> => {
    return apiClient.get(`/locations/geocode?address=${encodeURIComponent(address)}`);
  },

  validateLocation: async (latitude: number, longitude: number): Promise<any> => {
    return apiClient.post('/locations/validate', { latitude, longitude });
  }
};

// React Query hooks for real-time data
export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system-status'],
    queryFn: systemApi.getStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useIncidents = (status?: string, limit: number = 50) => {
  return useQuery({
    queryKey: ['incidents', status, limit],
    queryFn: () => incidentsApi.getIncidents(status, limit),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
};

export const useIncident = (incidentId: string) => {
  return useQuery({
    queryKey: ['incidents', incidentId],
    queryFn: () => incidentsApi.getIncident(incidentId),
    enabled: !!incidentId,
    refetchInterval: 5000, // Refetch every 5 seconds for active incident
  });
};

export const useSecurityUnits = () => {
  return useQuery({
    queryKey: ['security-units'],
    queryFn: securityUnitsApi.getUnits,
    refetchInterval: 15000, // Refetch every 15 seconds
  });
};

export const useDashboardData = () => {
  return useQuery({
    queryKey: ['dashboard-data'],
    queryFn: analyticsApi.getDashboardData,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useVenueZones = () => {
  return useQuery({
    queryKey: ['venue-zones'],
    queryFn: locationsApi.getVenueZones,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });
};

// Mutation hooks for actions
export const useSendMessage = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (message: string | { content: string; session_id?: string }) => {
      const params = typeof message === 'string' ? { content: message } : message;
      return chatApi.sendMessage(params.content, params.session_id);
    },
    onSuccess: (aiResponse, userMessage) => {
      // Invalidate chat messages to refetch
      queryClient.invalidateQueries({ queryKey: ['chat-messages'] });
    },
  });
};

export const useRespondToIncident = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ incidentId, response }: { incidentId: string; response: ManualCommand }) =>
      incidentsApi.respondToIncident(incidentId, response),
    onSuccess: (_, variables) => {
      // Invalidate and refetch incidents
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['incidents', variables.incidentId] });
    },
  });
};

export const useManualDispatch = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: dispatchApi.manualDispatch,
    onSuccess: () => {
      // Invalidate security units to get updated status
      queryClient.invalidateQueries({ queryKey: ['security-units'] });
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
    },
  });
};

export const useSimulateAnomaly = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ anomaly_type, location }: { anomaly_type: string; location: string }) =>
      systemApi.simulateAnomaly(anomaly_type, location),
    onSuccess: () => {
      // Refresh incidents and dashboard after simulation
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-data'] });
    },
  });
};

export const useGeocodeLocation = () => {
  return useMutation({
    mutationFn: locationsApi.geocodeLocation,
  });
};

export const useValidateLocation = () => {
  return useMutation({
    mutationFn: ({ latitude, longitude }: { latitude: number; longitude: number }) =>
      locationsApi.validateLocation(latitude, longitude),
  });
};

export const useCrowdForecast = (location: string, hours_ahead: number = 4) => {
  return useQuery({
    queryKey: ['crowd-forecast', location, hours_ahead],
    queryFn: () => analyticsApi.getCrowdForecast(location, hours_ahead),
    enabled: !!location,
    staleTime: 10 * 60 * 1000, // Consider data fresh for 10 minutes
  });
};

// Legacy compatibility for existing components that might use these names
export const useAlerts = () => {
  const { data: dashboardData, ...rest } = useDashboardData();
  return {
    ...rest,
    data: dashboardData?.recent_alerts || [],
  };
};

export const useAgents = () => {
  return useSecurityUnits();
};

// Add missing legacy functions for compatibility
export const useChatMessages = () => {
  return useQuery({
    queryKey: ['chat-messages'],
    queryFn: async () => [] as ChatMessage[], // Empty array for now, will be replaced with real chat history
    staleTime: 1000, // Very short stale time since messages change frequently
  });
};

export const useAcknowledgeAlert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (alertId: string) => {
      // For now, just a placeholder - would need backend endpoint for alert acknowledgment
      await new Promise(resolve => setTimeout(resolve, 300));
      console.log(`Alert ${alertId} acknowledged`);
    },
    onSuccess: (_, alertId) => {
      // Update the alerts in cache to mark as acknowledged
      queryClient.setQueryData(['dashboard-data'], (old: DashboardData) => {
        if (!old) return old;
        return {
          ...old,
          recent_alerts: old.recent_alerts.map(alert =>
            alert.id === alertId ? { ...alert, acknowledged: true } : alert
          )
        };
      });
    },
  });
};

// Export backward-compatible types
export type Agent = SecurityUnit;

// Utility functions for date/time handling and location display
export const formatTime = (timestamp: Date | string): string => {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString();
};

export const formatLocationString = (location: Location): string => {
  if (location.name) return location.name;
  const lat = location.lat || location.latitude || 0;
  const lng = location.lng || location.longitude || 0;
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
};

export const ensureDate = (timestamp: Date | string): Date => {
  return typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
};

export const getLocationCoords = (location: Location): { lat: number; lng: number } => {
  return {
    lat: location.lat || location.latitude || 0,
    lng: location.lng || location.longitude || 0,
  };
};
