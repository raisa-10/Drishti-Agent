import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MapPin, Zap, Users, Shield, Camera, RefreshCw } from 'lucide-react';

interface Zone {
  id: string;
  name: string;
  status: 'normal' | 'watch' | 'critical';
  position: { x: number; y: number };
  incidents: number;
  responders: number;
}

interface Responder {
  id: string;
  type: 'security' | 'medical' | 'fire';
  position: { x: number; y: number };
  status: 'active' | 'responding' | 'standby';
}

const mockZones: Zone[] = [
  { id: 'alpha-1', name: 'Alpha-1', status: 'normal', position: { x: 15, y: 20 }, incidents: 0, responders: 2 },
  { id: 'alpha-2', name: 'Alpha-2', status: 'watch', position: { x: 40, y: 25 }, incidents: 1, responders: 3 },
  { id: 'alpha-3', name: 'Alpha-3', status: 'critical', position: { x: 65, y: 15 }, incidents: 2, responders: 5 },
  { id: 'beta-1', name: 'Beta-1', status: 'critical', position: { x: 20, y: 50 }, incidents: 1, responders: 4 },
  { id: 'beta-2', name: 'Beta-2', status: 'normal', position: { x: 50, y: 55 }, incidents: 0, responders: 2 },
  { id: 'gamma-1', name: 'Gamma-1', status: 'normal', position: { x: 75, y: 45 }, incidents: 0, responders: 1 },
  { id: 'gamma-2', name: 'Gamma-2', status: 'watch', position: { x: 30, y: 75 }, incidents: 1, responders: 3 },
  { id: 'delta-1', name: 'Delta-1', status: 'normal', position: { x: 60, y: 80 }, incidents: 0, responders: 2 },
];

const mockResponders: Responder[] = [
  { id: 'sec-1', type: 'security', position: { x: 25, y: 30 }, status: 'active' },
  { id: 'sec-2', type: 'security', position: { x: 55, y: 40 }, status: 'responding' },
  { id: 'med-1', type: 'medical', position: { x: 35, y: 60 }, status: 'standby' },
  { id: 'fire-1', type: 'fire', position: { x: 70, y: 25 }, status: 'responding' },
];

const getZoneStatusColor = (status: Zone['status']) => {
  switch (status) {
    case 'critical': return 'bg-destructive border-destructive text-destructive-foreground';
    case 'watch': return 'bg-warning border-warning text-warning-foreground';
    case 'normal': return 'bg-success border-success text-success-foreground';
    default: return 'bg-muted border-muted text-muted-foreground';
  }
};

const getResponderIcon = (type: Responder['type']) => {
  switch (type) {
    case 'security': return <Shield className="h-3 w-3" />;
    case 'medical': return <Zap className="h-3 w-3" />;
    case 'fire': return <Camera className="h-3 w-3" />;
    default: return <Users className="h-3 w-3" />;
  }
};

const getResponderColor = (type: Responder['type'], status: Responder['status']) => {
  const baseColors = {
    security: 'bg-blue-500',
    medical: 'bg-green-500',
    fire: 'bg-red-500',
  };
  
  return status === 'responding' 
    ? `${baseColors[type]} animate-pulse` 
    : baseColors[type];
};

export function IncidentMap() {
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);

  return (
    <Card className="h-full border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-foreground">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            Incident Map
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <div className="relative bg-muted/30 rounded-lg border border-border/50 overflow-hidden">
          {/* Map Background */}
          <div className="relative h-96 bg-gradient-to-br from-muted/20 to-muted/40">
            {/* Grid Pattern */}
            <div className="absolute inset-0 opacity-10">
              <svg width="100%" height="100%">
                <defs>
                  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" strokeWidth="1"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
            </div>

            {/* Zones */}
            {mockZones.map((zone) => (
              <div
                key={zone.id}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all hover:scale-110 ${getZoneStatusColor(zone.status)}`}
                style={{
                  left: `${zone.position.x}%`,
                  top: `${zone.position.y}%`,
                }}
                onClick={() => setSelectedZone(zone)}
              >
                <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold shadow-lg">
                  {zone.incidents}
                </div>
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-1 text-xs font-medium whitespace-nowrap">
                  {zone.name}
                </div>
              </div>
            ))}

            {/* Responders */}
            {mockResponders.map((responder) => (
              <div
                key={responder.id}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 ${getResponderColor(responder.type, responder.status)}`}
                style={{
                  left: `${responder.position.x}%`,
                  top: `${responder.position.y}%`,
                }}
              >
                <div className="w-4 h-4 rounded-full border border-white flex items-center justify-center text-white shadow-lg">
                  {getResponderIcon(responder.type)}
                </div>
              </div>
            ))}

            {/* Legend */}
            <div className="absolute top-4 right-4 bg-card/90 backdrop-blur-sm rounded-lg p-3 border border-border/50">
              <h4 className="text-sm font-semibold mb-2 text-foreground">Zone Status</h4>
              <div className="space-y-1 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-success"></div>
                  <span>Normal</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-warning"></div>
                  <span>Watch</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-destructive"></div>
                  <span>Critical</span>
                </div>
              </div>
              
              <h4 className="text-sm font-semibold mt-3 mb-2 text-foreground">Responders</h4>
              <div className="space-y-1 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500 flex items-center justify-center">
                    <Shield className="h-2 w-2 text-white" />
                  </div>
                  <span>Security</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500 flex items-center justify-center">
                    <Zap className="h-2 w-2 text-white" />
                  </div>
                  <span>Medical</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500 flex items-center justify-center">
                    <Camera className="h-2 w-2 text-white" />
                  </div>
                  <span>Fire Safety</span>
                </div>
              </div>
            </div>
          </div>

          {/* Zone Details */}
          {selectedZone && (
            <div className="mt-4 p-4 bg-card/60 rounded-lg border border-border/50">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-foreground">{selectedZone.name} Details</h3>
                <Badge className={getZoneStatusColor(selectedZone.status).replace('border-', '')}>
                  {selectedZone.status.toUpperCase()}
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Active Incidents:</span>
                  <span className="ml-2 font-medium text-foreground">{selectedZone.incidents}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Responders:</span>
                  <span className="ml-2 font-medium text-foreground">{selectedZone.responders}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
