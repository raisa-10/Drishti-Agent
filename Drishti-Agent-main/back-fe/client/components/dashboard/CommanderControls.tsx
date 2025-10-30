import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Shield, Zap, CheckCircle, Radio, AlertTriangle, Settings, PlayCircle } from 'lucide-react';
import { toast } from 'sonner';

interface ActionLog {
  id: string;
  action: string;
  timestamp: Date;
  status: 'success' | 'pending' | 'failed';
  details: string;
}

const zones = [
  'Zone Alpha-1', 'Zone Alpha-2', 'Zone Alpha-3',
  'Zone Beta-1', 'Zone Beta-2',
  'Zone Gamma-1', 'Zone Gamma-2',
  'Zone Delta-1', 'Zone Delta-2'
];

export function CommanderControls() {
  const [actionLogs, setActionLogs] = useState<ActionLog[]>([
    {
      id: '1',
      action: 'System Initialization',
      timestamp: new Date(Date.now() - 300000),
      status: 'success',
      details: 'All monitoring systems online'
    }
  ]);
  const [selectedZone, setSelectedZone] = useState<string>('');

  const addActionLog = (action: string, status: ActionLog['status'], details: string) => {
    const newLog: ActionLog = {
      id: Date.now().toString(),
      action,
      timestamp: new Date(),
      status,
      details
    };
    setActionLogs(prev => [newLog, ...prev.slice(0, 4)]);
  };

  const simulateAnomaly = () => {
    const anomalyTypes = [
      'Crowd Density Spike',
      'Unauthorized Movement',
      'Equipment Malfunction',
      'Perimeter Breach',
      'Suspicious Activity'
    ];
    const randomType = anomalyTypes[Math.floor(Math.random() * anomalyTypes.length)];
    const randomZone = zones[Math.floor(Math.random() * zones.length)];
    
    addActionLog(
      'Anomaly Simulation',
      'success',
      `Generated ${randomType} in ${randomZone}`
    );
    
    toast.success('Anomaly Simulated', {
      description: `${randomType} created in ${randomZone}`,
    });
  };

  const markIncidentResolved = () => {
    if (!selectedZone) {
      toast.error('Please select a zone first');
      return;
    }

    addActionLog(
      'Incident Resolution',
      'success',
      `All incidents in ${selectedZone} marked as resolved`
    );

    toast.success('Incident Resolved', {
      description: `All incidents in ${selectedZone} have been resolved`,
    });
    setSelectedZone('');
  };

  const triggerDispatch = () => {
    if (!selectedZone) {
      toast.error('Please select a zone first');
      return;
    }

    const responderTypes = ['Security Team', 'Medical Unit', 'Fire Safety', 'Emergency Response'];
    const randomResponder = responderTypes[Math.floor(Math.random() * responderTypes.length)];

    addActionLog(
      'Manual Dispatch',
      'pending',
      `${randomResponder} dispatched to ${selectedZone}`
    );

    toast.success('Dispatch Triggered', {
      description: `${randomResponder} en route to ${selectedZone}`,
    });

    // Simulate completion after 3 seconds
    setTimeout(() => {
      setActionLogs(prev => prev.map(log => 
        log.action === 'Manual Dispatch' && log.status === 'pending'
          ? { ...log, status: 'success' as const, details: `${randomResponder} arrived at ${selectedZone}` }
          : log
      ));
    }, 3000);
    setSelectedZone('');
  };

  const systemReset = () => {
    addActionLog(
      'System Reset',
      'pending',
      'Resetting all monitoring systems...'
    );

    toast.info('System Reset Initiated', {
      description: 'All systems will restart in 30 seconds',
    });

    setTimeout(() => {
      setActionLogs(prev => prev.map(log => 
        log.action === 'System Reset' && log.status === 'pending'
          ? { ...log, status: 'success' as const, details: 'All systems successfully restarted' }
          : log
      ));
    }, 2000);
  };

  const getStatusIcon = (status: ActionLog['status']) => {
    switch (status) {
      case 'success': return <CheckCircle className="h-4 w-4 text-success" />;
      case 'pending': return <PlayCircle className="h-4 w-4 text-warning animate-spin" />;
      case 'failed': return <AlertTriangle className="h-4 w-4 text-destructive" />;
      default: return <CheckCircle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: ActionLog['status']) => {
    switch (status) {
      case 'success': return 'bg-success text-success-foreground';
      case 'pending': return 'bg-warning text-warning-foreground';
      case 'failed': return 'bg-destructive text-destructive-foreground';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <Card className="h-full border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-foreground">
          <Shield className="h-5 w-5 text-primary" />
          Commander Controls
          <Badge variant="secondary" className="ml-auto">
            System Active
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="p-4 space-y-6">
        {/* Zone Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Target Zone</label>
          <Select value={selectedZone} onValueChange={setSelectedZone}>
            <SelectTrigger>
              <SelectValue placeholder="Select zone for actions" />
            </SelectTrigger>
            <SelectContent>
              {zones.map((zone) => (
                <SelectItem key={zone} value={zone}>
                  {zone}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            onClick={simulateAnomaly}
            variant="outline"
            className="h-16 flex flex-col items-center gap-1 hover:bg-warning/10 hover:border-warning"
          >
            <Zap className="h-5 w-5 text-warning" />
            <span className="text-xs">Simulate Anomaly</span>
          </Button>

          <Button
            onClick={markIncidentResolved}
            disabled={!selectedZone}
            variant="outline"
            className="h-16 flex flex-col items-center gap-1 hover:bg-success/10 hover:border-success"
          >
            <CheckCircle className="h-5 w-5 text-success" />
            <span className="text-xs">Mark Resolved</span>
          </Button>

          <Button
            onClick={triggerDispatch}
            disabled={!selectedZone}
            variant="outline"
            className="h-16 flex flex-col items-center gap-1 hover:bg-primary/10 hover:border-primary"
          >
            <Radio className="h-5 w-5 text-primary" />
            <span className="text-xs">Trigger Dispatch</span>
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                className="h-16 flex flex-col items-center gap-1 hover:bg-destructive/10 hover:border-destructive"
              >
                <Settings className="h-5 w-5 text-destructive" />
                <span className="text-xs">System Reset</span>
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>System Reset Confirmation</AlertDialogTitle>
                <AlertDialogDescription>
                  This will restart all monitoring systems and may cause a brief interruption in surveillance coverage. 
                  Are you sure you want to proceed?
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={systemReset}>
                  Confirm Reset
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        {/* Action Log */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-foreground">Recent Actions</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {actionLogs.map((log) => (
              <div
                key={log.id}
                className="p-3 rounded-lg border border-border/50 bg-muted/20 hover:bg-muted/40 transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(log.status)}
                    <span className="text-sm font-medium text-foreground">{log.action}</span>
                  </div>
                  <Badge className={getStatusColor(log.status)} variant="secondary">
                    {log.status.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-1">{log.details}</p>
                <p className="text-xs text-muted-foreground">{formatTime(log.timestamp)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 p-3 bg-muted/30 rounded-lg border border-border/50">
          <div className="text-center">
            <div className="text-lg font-bold text-success">12</div>
            <div className="text-xs text-muted-foreground">Actions Today</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-warning">3</div>
            <div className="text-xs text-muted-foreground">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-primary">2.3s</div>
            <div className="text-xs text-muted-foreground">Avg Response</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
