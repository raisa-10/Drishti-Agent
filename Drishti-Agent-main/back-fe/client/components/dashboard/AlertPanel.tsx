import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock, MapPin, AlertTriangle, Shield, Eye } from 'lucide-react';

interface Alert {
  id: string;
  zone: string;
  eventType: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  status: 'active' | 'investigating' | 'resolved';
}

const mockAlerts: Alert[] = [
  {
    id: '1',
    zone: 'Zone Alpha-3',
    eventType: 'Crowd Density Alert',
    timestamp: new Date(Date.now() - 2 * 60 * 1000),
    severity: 'high',
    description: 'Unusual crowd gathering detected near main entrance',
    status: 'active'
  },
  {
    id: '2',
    zone: 'Zone Beta-1',
    eventType: 'Unauthorized Access',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    severity: 'critical',
    description: 'Motion detected in restricted area after hours',
    status: 'investigating'
  },
  {
    id: '3',
    zone: 'Zone Gamma-2',
    eventType: 'Equipment Malfunction',
    timestamp: new Date(Date.now() - 8 * 60 * 1000),
    severity: 'medium',
    description: 'Camera offline - maintenance required',
    status: 'active'
  },
  {
    id: '4',
    zone: 'Zone Alpha-1',
    eventType: 'Security Check',
    timestamp: new Date(Date.now() - 12 * 60 * 1000),
    severity: 'low',
    description: 'Routine patrol completed successfully',
    status: 'resolved'
  },
  {
    id: '5',
    zone: 'Zone Delta-4',
    eventType: 'Suspicious Activity',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    severity: 'high',
    description: 'Individual loitering near perimeter fence',
    status: 'investigating'
  },
];

const getSeverityColor = (severity: Alert['severity']) => {
  switch (severity) {
    case 'critical': return 'bg-destructive text-destructive-foreground';
    case 'high': return 'bg-warning text-warning-foreground';
    case 'medium': return 'bg-orange-500 text-white';
    case 'low': return 'bg-success text-success-foreground';
    default: return 'bg-muted text-muted-foreground';
  }
};

const getStatusIcon = (status: Alert['status']) => {
  switch (status) {
    case 'active': return <AlertTriangle className="h-4 w-4" />;
    case 'investigating': return <Eye className="h-4 w-4" />;
    case 'resolved': return <Shield className="h-4 w-4" />;
    default: return <AlertTriangle className="h-4 w-4" />;
  }
};

const formatTimeAgo = (timestamp: Date) => {
  const now = new Date();
  const diffMs = now.getTime() - timestamp.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
};

export function AlertPanel() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate new alerts
      const eventTypes = ['Crowd Density Alert', 'Motion Detection', 'Equipment Status', 'Security Breach'];
      const zones = ['Zone Alpha-1', 'Zone Alpha-2', 'Zone Beta-1', 'Zone Gamma-3', 'Zone Delta-2'];
      const severities: Alert['severity'][] = ['low', 'medium', 'high', 'critical'];
      
      if (Math.random() > 0.8) {
        const newAlert: Alert = {
          id: Date.now().toString(),
          zone: zones[Math.floor(Math.random() * zones.length)],
          eventType: eventTypes[Math.floor(Math.random() * eventTypes.length)],
          timestamp: new Date(),
          severity: severities[Math.floor(Math.random() * severities.length)],
          description: 'Real-time alert generated for demonstration',
          status: 'active'
        };
        
        setAlerts(prev => [newAlert, ...prev.slice(0, 9)]);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="h-full border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-foreground">
          <AlertTriangle className="h-5 w-5 text-primary" />
          Real-Time Alerts
          <Badge variant="secondary" className="ml-auto">
            {alerts.filter(a => a.status === 'active').length} Active
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[calc(100vh-200px)]">
          <div className="space-y-2 p-4">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="group p-4 rounded-lg border border-border/50 bg-card/30 hover:bg-card/60 transition-all duration-200 hover:shadow-lg hover:shadow-primary/10"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(alert.status)}
                    <Badge className={getSeverityColor(alert.severity)}>
                      {alert.severity.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {formatTimeAgo(alert.timestamp)}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    <span className="font-medium text-foreground">{alert.zone}</span>
                  </div>
                  
                  <h4 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                    {alert.eventType}
                  </h4>
                  
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {alert.description}
                  </p>
                  
                  <div className="flex items-center justify-between pt-2">
                    <Badge variant="outline" className="text-xs">
                      {alert.status.charAt(0).toUpperCase() + alert.status.slice(1)}
                    </Badge>
                    <button className="text-xs text-primary hover:text-primary/80 transition-colors">
                      View Details →
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
