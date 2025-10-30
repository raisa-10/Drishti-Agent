// Project Drishti - Data Store for Firebase Integration
// This file contains dummy data and structures for Firebase Firestore integration

export interface Alert {
  id: string;
  zone: string;
  eventType: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  status: 'active' | 'investigating' | 'resolved';
  coordinates?: { lat: number; lng: number };
  responderAssigned?: string;
}

export interface Zone {
  id: string;
  name: string;
  status: 'normal' | 'watch' | 'critical';
  coordinates: { lat: number; lng: number; radius: number };
  activeIncidents: number;
  responders: ResponderUnit[];
  lastUpdate: Date;
}

export interface ResponderUnit {
  id: string;
  type: 'security' | 'medical' | 'fire' | 'emergency';
  callSign: string;
  status: 'available' | 'responding' | 'busy' | 'offline';
  location: { lat: number; lng: number };
  assignedZone?: string;
  equipment: string[];
}

export interface VideoFeed {
  id: string;
  name: string;
  zone: string;
  type: 'live' | 'recorded';
  url?: string;
  status: 'online' | 'offline' | 'maintenance';
  quality: '720p' | '1080p' | '4K';
  lastActive: Date;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  metadata?: {
    confidence?: number;
    relatedAlerts?: string[];
    suggestedActions?: string[];
  };
}

// Mock Data for Development
export const mockZones: Zone[] = [
  {
    id: 'alpha-1',
    name: 'Zone Alpha-1',
    status: 'normal',
    coordinates: { lat: 40.7128, lng: -74.0060, radius: 100 },
    activeIncidents: 0,
    responders: [],
    lastUpdate: new Date()
  },
  {
    id: 'alpha-2',
    name: 'Zone Alpha-2',
    status: 'watch',
    coordinates: { lat: 40.7589, lng: -73.9851, radius: 150 },
    activeIncidents: 1,
    responders: [],
    lastUpdate: new Date()
  },
  {
    id: 'alpha-3',
    name: 'Zone Alpha-3',
    status: 'critical',
    coordinates: { lat: 40.7505, lng: -73.9934, radius: 120 },
    activeIncidents: 2,
    responders: [],
    lastUpdate: new Date()
  }
];

export const mockResponders: ResponderUnit[] = [
  {
    id: 'sec-001',
    type: 'security',
    callSign: 'Security-1',
    status: 'responding',
    location: { lat: 40.7128, lng: -74.0060 },
    assignedZone: 'alpha-3',
    equipment: ['Radio', 'Taser', 'Body Camera']
  },
  {
    id: 'med-001',
    type: 'medical',
    callSign: 'Medical-1',
    status: 'available',
    location: { lat: 40.7589, lng: -73.9851 },
    equipment: ['Medical Kit', 'Defibrillator', 'Oxygen Tank']
  },
  {
    id: 'fire-001',
    type: 'fire',
    callSign: 'Fire-1',
    status: 'busy',
    location: { lat: 40.7505, lng: -73.9934 },
    assignedZone: 'beta-1',
    equipment: ['Fire Extinguisher', 'Breathing Apparatus', 'Axe']
  }
];

// Firebase Integration Helpers (Mock Implementation)
export class DrishtiDataStore {
  // Simulate Firestore real-time listeners
  static subscribeToAlerts(callback: (alerts: Alert[]) => void) {
    // Mock implementation - in real app, this would be:
    // return db.collection('alerts').onSnapshot(callback);
    
    const interval = setInterval(() => {
      // Generate random new alert occasionally
      if (Math.random() > 0.9) {
        const newAlert: Alert = {
          id: Date.now().toString(),
          zone: mockZones[Math.floor(Math.random() * mockZones.length)].name,
          eventType: ['Motion Detection', 'Crowd Alert', 'Equipment Issue'][Math.floor(Math.random() * 3)],
          timestamp: new Date(),
          severity: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)] as Alert['severity'],
          description: 'Real-time alert generated for demonstration',
          status: 'active'
        };
        callback([newAlert]);
      }
    }, 15000); // Check every 15 seconds

    return () => clearInterval(interval);
  }

  static subscribeToZones(callback: (zones: Zone[]) => void) {
    // Mock real-time zone updates
    const interval = setInterval(() => {
      const updatedZones = mockZones.map(zone => ({
        ...zone,
        lastUpdate: new Date(),
        activeIncidents: Math.max(0, zone.activeIncidents + (Math.random() > 0.7 ? 1 : -1))
      }));
      callback(updatedZones);
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }

  static async createAlert(alert: Omit<Alert, 'id' | 'timestamp'>) {
    // Mock alert creation
    const newAlert: Alert = {
      ...alert,
      id: Date.now().toString(),
      timestamp: new Date()
    };
    
    console.log('Alert created:', newAlert);
    return newAlert;
  }

  static async updateAlertStatus(alertId: string, status: Alert['status']) {
    // Mock alert status update
    console.log(`Alert ${alertId} status updated to:`, status);
    return true;
  }

  static async dispatchResponder(responderId: string, zoneId: string) {
    // Mock responder dispatch
    console.log(`Responder ${responderId} dispatched to zone ${zoneId}`);
    return true;
  }
}

// Event Types for the system
export const EVENT_TYPES = [
  'Motion Detection',
  'Crowd Density Alert',
  'Unauthorized Access',
  'Equipment Malfunction',
  'Perimeter Breach',
  'Suspicious Activity',
  'Emergency Button',
  'Fire Alarm',
  'Medical Emergency',
  'Security Check'
] as const;

export const ZONE_NAMES = [
  'Zone Alpha-1', 'Zone Alpha-2', 'Zone Alpha-3',
  'Zone Beta-1', 'Zone Beta-2',
  'Zone Gamma-1', 'Zone Gamma-2',
  'Zone Delta-1', 'Zone Delta-2'
] as const;

// Configuration for the dashboard
export const DASHBOARD_CONFIG = {
  refreshInterval: 5000, // 5 seconds
  alertRetentionHours: 24,
  mapCenter: { lat: 40.7128, lng: -74.0060 }, // New York City
  mapZoom: 13,
  videoQualityOptions: ['720p', '1080p', '4K'],
  notificationSound: '/notification.mp3', // Add this file to public folder
  maxAlertsDisplay: 50,
  chatHistoryLimit: 100
};
