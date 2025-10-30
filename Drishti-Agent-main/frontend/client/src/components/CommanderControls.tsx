import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, 
  Send, 
  Shield, 
  AlertTriangle, 
  Users, 
  Radio,
  Eye,
  Lock,
  Unlock,
  Power,
  RefreshCw,
  Target,
  Siren
} from 'lucide-react';

interface ControlButtonProps {
  icon: React.ComponentType<any>;
  label: string;
  description?: string;
  variant: 'primary' | 'danger' | 'warning' | 'success' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  isActive?: boolean;
  onClick: () => void;
  disabled?: boolean;
}

const ControlButton = ({ 
  icon: Icon, 
  label, 
  description, 
  variant, 
  size = 'md', 
  isLoading = false,
  isActive = false,
  onClick,
  disabled = false
}: ControlButtonProps) => {
  const getVariantStyles = () => {
    const baseStyles = "border-2 transition-all duration-300 font-bold uppercase tracking-wider";
    
    switch (variant) {
      case 'primary':
        return `${baseStyles} ${
          isActive 
            ? 'bg-neon-blue text-command-bg border-neon-blue neon-glow animate-pulse-glow' 
            : 'bg-neon-blue/20 text-neon-blue border-neon-blue/50 hover:bg-neon-blue hover:text-command-bg hover:neon-glow'
        }`;
      case 'danger':
        return `${baseStyles} ${
          isActive 
            ? 'bg-danger text-white border-danger shadow-danger-glow animate-pulse-glow' 
            : 'bg-danger/20 text-danger border-danger/50 hover:bg-danger hover:text-white hover:shadow-danger-glow'
        }`;
      case 'warning':
        return `${baseStyles} ${
          isActive 
            ? 'bg-warning text-command-bg border-warning shadow-warning-glow animate-pulse-glow' 
            : 'bg-warning/20 text-warning border-warning/50 hover:bg-warning hover:text-command-bg hover:shadow-warning-glow'
        }`;
      case 'success':
        return `${baseStyles} ${
          isActive 
            ? 'bg-success text-command-bg border-success shadow-success-glow animate-pulse-glow' 
            : 'bg-success/20 text-success border-success/50 hover:bg-success hover:text-command-bg hover:shadow-success-glow'
        }`;
      case 'secondary':
        return `${baseStyles} ${
          isActive 
            ? 'bg-foreground text-command-bg border-foreground' 
            : 'bg-command-surface text-foreground border-command-border hover:bg-foreground hover:text-command-bg'
        }`;
      default:
        return baseStyles;
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-2 text-xs';
      case 'lg':
        return 'px-8 py-4 text-base';
      default:
        return 'px-6 py-3 text-sm';
    }
  };

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      disabled={disabled || isLoading}
      className={`
        relative rounded-lg flex flex-col items-center justify-center space-y-2
        ${getVariantStyles()} ${getSizeStyles()}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        group
      `}
    >
      {/* Loading Spinner */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-current/20 rounded-lg">
          <RefreshCw className="w-5 h-5 animate-spin" />
        </div>
      )}

      <Icon className={`${size === 'lg' ? 'w-8 h-8' : size === 'sm' ? 'w-4 h-4' : 'w-6 h-6'}`} />
      <span className="terminal-text">{label}</span>
      
      {description && (
        <span className="text-xs opacity-70 normal-case tracking-normal font-normal">
          {description}
        </span>
      )}

      {/* Scan Line Effect for Active Buttons */}
      {isActive && (
        <div className="absolute inset-0 overflow-hidden rounded-lg">
          <div className="scan-line" />
        </div>
      )}
    </motion.button>
  );
};

export default function CommanderControls() {
  const [activeControls, setActiveControls] = useState<Set<string>>(new Set());
  const [loadingControls, setLoadingControls] = useState<Set<string>>(new Set());
  const [systemStatus, setSystemStatus] = useState<'locked' | 'unlocked'>('locked');

  const executeAction = async (actionId: string, duration = 2000) => {
    setLoadingControls(prev => new Set(prev).add(actionId));
    
    // Simulate action execution
    setTimeout(() => {
      setLoadingControls(prev => {
        const newSet = new Set(prev);
        newSet.delete(actionId);
        return newSet;
      });
      
      // Toggle active state for some actions
      if (['auto-dispatch', 'lockdown', 'surveillance'].includes(actionId)) {
        setActiveControls(prev => {
          const newSet = new Set(prev);
          if (newSet.has(actionId)) {
            newSet.delete(actionId);
          } else {
            newSet.add(actionId);
          }
          return newSet;
        });
      }
    }, duration);
  };

  const toggleSystemLock = () => {
    setSystemStatus(prev => prev === 'locked' ? 'unlocked' : 'locked');
  };

  const emergencyActions = [
    {
      id: 'simulate-anomaly',
      icon: Zap,
      label: 'Simulate Anomaly',
      description: 'Test system response',
      variant: 'warning' as const,
    },
    {
      id: 'emergency-alert',
      icon: Siren,
      label: 'Emergency Alert',
      description: 'Broadcast alert',
      variant: 'danger' as const,
    },
    {
      id: 'lockdown',
      icon: Lock,
      label: 'Facility Lockdown',
      description: 'Secure all sectors',
      variant: 'danger' as const,
    },
  ];

  const operationalActions = [
    {
      id: 'auto-dispatch',
      icon: Send,
      label: 'Auto Dispatch',
      description: 'Deploy nearest units',
      variant: 'primary' as const,
    },
    {
      id: 'surveillance',
      icon: Eye,
      label: 'Enhanced Surveillance',
      description: 'Activate all cameras',
      variant: 'primary' as const,
    },
    {
      id: 'shield-protocol',
      icon: Shield,
      label: 'Shield Protocol',
      description: 'Defensive measures',
      variant: 'success' as const,
    },
  ];

  const communicationActions = [
    {
      id: 'all-units',
      icon: Radio,
      label: 'Alert All Units',
      description: 'Mass communication',
      variant: 'secondary' as const,
      size: 'sm' as const,
    },
    {
      id: 'command-center',
      icon: Users,
      label: 'Command Center',
      description: 'Direct line',
      variant: 'secondary' as const,
      size: 'sm' as const,
    },
    {
      id: 'tactical-team',
      icon: Target,
      label: 'Tactical Team',
      description: 'Specialized unit',
      variant: 'secondary' as const,
      size: 'sm' as const,
    },
  ];

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 custom-scrollbar">
      {/* Header with System Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold text-foreground terminal-text">COMMAND CONTROLS</h2>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
            <span className="text-xs text-success">SYSTEMS ONLINE</span>
          </div>
        </div>

        {/* System Lock Toggle */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleSystemLock}
          className={`
            flex items-center space-x-2 px-4 py-2 rounded-lg border-2 transition-all duration-300
            ${systemStatus === 'locked' 
              ? 'bg-danger/20 text-danger border-danger/50 hover:bg-danger hover:text-white' 
              : 'bg-success/20 text-success border-success/50 hover:bg-success hover:text-command-bg'
            }
          `}
        >
          {systemStatus === 'locked' ? (
            <Lock className="w-4 h-4" />
          ) : (
            <Unlock className="w-4 h-4" />
          )}
          <span className="text-sm font-medium terminal-text">
            {systemStatus === 'locked' ? 'SYSTEM LOCKED' : 'SYSTEM UNLOCKED'}
          </span>
        </motion.button>
      </div>

      {/* Emergency Actions */}
      <div>
        <h3 className="text-lg font-semibold text-danger mb-4 terminal-text flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5" />
          <span>EMERGENCY PROTOCOLS</span>
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {emergencyActions.map((action) => (
            <ControlButton
              key={action.id}
              icon={action.icon}
              label={action.label}
              description={action.description}
              variant={action.variant}
              size="lg"
              isLoading={loadingControls.has(action.id)}
              isActive={activeControls.has(action.id)}
              onClick={() => executeAction(action.id)}
              disabled={systemStatus === 'locked'}
            />
          ))}
        </div>
      </div>

      {/* Operational Actions */}
      <div>
        <h3 className="text-lg font-semibold text-neon-blue mb-4 terminal-text flex items-center space-x-2">
          <Shield className="w-5 h-5" />
          <span>OPERATIONAL CONTROLS</span>
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {operationalActions.map((action) => (
            <ControlButton
              key={action.id}
              icon={action.icon}
              label={action.label}
              description={action.description}
              variant={action.variant}
              isLoading={loadingControls.has(action.id)}
              isActive={activeControls.has(action.id)}
              onClick={() => executeAction(action.id)}
              disabled={systemStatus === 'locked'}
            />
          ))}
        </div>
      </div>

      {/* Communication Panel */}
      <div>
        <h3 className="text-lg font-semibold text-foreground mb-4 terminal-text flex items-center space-x-2">
          <Radio className="w-5 h-5" />
          <span>COMMUNICATION CHANNELS</span>
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {communicationActions.map((action) => (
            <ControlButton
              key={action.id}
              icon={action.icon}
              label={action.label}
              description={action.description}
              variant={action.variant}
              size={action.size}
              isLoading={loadingControls.has(action.id)}
              onClick={() => executeAction(action.id, 1000)}
            />
          ))}
        </div>
      </div>

      {/* Status Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-command-border">
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">THREAT LEVEL</div>
          <div className="text-warning font-bold terminal-text">MODERATE</div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">UNITS DEPLOYED</div>
          <div className="text-success font-bold terminal-text">
            {activeControls.has('auto-dispatch') ? '8/12' : '3/12'}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">SURVEILLANCE</div>
          <div className={`font-bold terminal-text ${activeControls.has('surveillance') ? 'text-success' : 'text-muted-foreground'}`}>
            {activeControls.has('surveillance') ? 'ENHANCED' : 'STANDARD'}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">FACILITY STATUS</div>
          <div className={`font-bold terminal-text ${activeControls.has('lockdown') ? 'text-danger' : 'text-success'}`}>
            {activeControls.has('lockdown') ? 'LOCKED DOWN' : 'SECURE'}
          </div>
        </div>
      </div>

      {/* Authorization Warning */}
      <AnimatePresence>
        {systemStatus === 'locked' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-danger/10 border border-danger/30 rounded-lg p-4 flex items-center space-x-3"
          >
            <Lock className="w-5 h-5 text-danger flex-shrink-0" />
            <div>
              <div className="text-danger font-medium">Authorization Required</div>
              <div className="text-sm text-muted-foreground">
                Command controls are locked. Administrator access required to execute operations.
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
