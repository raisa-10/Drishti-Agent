import { useState, forwardRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Shield, Info, Clock, MapPin, Check } from 'lucide-react';
import { useAlerts, useAcknowledgeAlert, formatTime, formatLocationString } from '../services/api';
import type { Alert } from '../services/api';

const severityConfig = {
  critical: {
    icon: AlertTriangle,
    color: 'text-danger',
    bgColor: 'bg-danger/10',
    borderColor: 'border-danger/30',
    glowColor: 'shadow-danger-glow/20',
  },
  warning: {
    icon: Shield,
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    borderColor: 'border-warning/30',
    glowColor: 'shadow-warning-glow/20',
  },
  info: {
    icon: Info,
    color: 'text-neon-blue',
    bgColor: 'bg-neon-blue/10',
    borderColor: 'border-neon-blue/30',
    glowColor: 'shadow-neon-glow/20',
  },
};

interface AlertCardProps {
  alert: Alert;
  onAcknowledge: (alertId: string) => void;
  isAcknowledging: boolean;
}

const AlertCard = forwardRef<HTMLDivElement, AlertCardProps>(({ alert, onAcknowledge, isAcknowledging }, ref) => {
  const config = severityConfig[alert.severity];
  const Icon = config.icon;

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      whileHover={{ scale: 1.02 }}
      className={`
        relative p-4 rounded-lg border backdrop-blur-sm
        ${config.bgColor} ${config.borderColor}
        ${alert.acknowledged ? 'opacity-60' : 'animate-pulse-glow'}
        ${!alert.acknowledged ? config.glowColor : ''}
        transition-all duration-300 cursor-pointer group
      `}
      onClick={() => !alert.acknowledged && onAcknowledge(alert.id)}
    >
      {/* Scan line effect for critical alerts */}
      {alert.severity === 'critical' && !alert.acknowledged && (
        <div className="absolute inset-0 overflow-hidden rounded-lg">
          <div className="scan-line opacity-50" />
        </div>
      )}

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Icon 
              className={`w-5 h-5 ${config.color} ${!alert.acknowledged ? 'animate-pulse' : ''}`} 
            />
            <span className={`text-sm font-medium uppercase tracking-wider ${config.color}`}>
              {alert.severity}
            </span>
          </div>
          
          {alert.acknowledged ? (
            <Check className="w-4 h-4 text-success" />
          ) : (
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className={`w-2 h-2 rounded-full ${config.color.replace('text-', 'bg-')}`}
            />
          )}
        </div>

        <h3 className="font-semibold text-foreground mb-1 terminal-text">
          {alert.title}
        </h3>
        
        <p className="text-sm text-muted-foreground mb-3">
          {alert.message}
        </p>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3" />
              <span>{formatTime(alert.timestamp)}</span>
            </div>
            
            {alert.location && (
              <div className="flex items-center space-x-1">
                <MapPin className="w-3 h-3" />
                <span>{formatLocationString(alert.location)}</span>
              </div>
            )}
          </div>

          {!alert.acknowledged && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              disabled={isAcknowledging}
              className={`
                px-2 py-1 rounded text-xs font-medium
                ${config.color} ${config.borderColor} border
                hover:bg-current hover:text-command-bg
                transition-all duration-200
                ${isAcknowledging ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              {isAcknowledging ? 'Acknowledging...' : 'Acknowledge'}
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );
});

AlertCard.displayName = 'AlertCard';

export default function AlertPanel() {
  const { data: alerts = [], isLoading, error } = useAlerts();
  const acknowledgeAlert = useAcknowledgeAlert();
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const handleAcknowledge = async (alertId: string) => {
    setAcknowledgingId(alertId);
    try {
      await acknowledgeAlert.mutateAsync(alertId);
    } finally {
      setAcknowledgingId(null);
    }
  };

  const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged);
  const acknowledgedAlerts = alerts.filter(alert => alert.acknowledged);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-foreground terminal-text">ALERT STATUS</h2>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-neon-blue rounded-full animate-pulse" />
            <span className="text-sm text-muted-foreground">Loading...</span>
          </div>
        </div>
        
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div
              key={i}
              className="h-24 bg-command-surface/30 rounded-lg border border-command-border animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-danger" />
            <span className="text-danger font-medium">Alert System Error</span>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Unable to load alerts. System diagnostics in progress.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold text-foreground terminal-text">ALERT STATUS</h2>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-neon-blue rounded-full animate-pulse" />
            <span className="text-sm text-neon-blue">LIVE</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-danger rounded-full" />
            <span className="text-muted-foreground">
              {unacknowledgedAlerts.length} Active
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success rounded-full" />
            <span className="text-muted-foreground">
              {acknowledgedAlerts.length} Resolved
            </span>
          </div>
        </div>
      </div>

      {/* Alert List */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
        <AnimatePresence mode="popLayout">
          {/* Unacknowledged alerts first */}
          {unacknowledgedAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              isAcknowledging={acknowledgingId === alert.id}
            />
          ))}
          
          {/* Acknowledged alerts */}
          {acknowledgedAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              isAcknowledging={false}
            />
          ))}
        </AnimatePresence>

        {alerts.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <Shield className="w-12 h-12 text-success mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">All Clear</h3>
            <p className="text-sm text-muted-foreground">
              No active alerts. System monitoring continues.
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
