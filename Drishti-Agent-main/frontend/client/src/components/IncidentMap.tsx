import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Maximize2, 
  Minimize2, 
  MapPin, 
  Users, 
  AlertTriangle,
  Navigation,
  Layers,
  ZoomIn,
  ZoomOut
} from 'lucide-react';
import { useIncidents, useAgents, formatTime, getLocationCoords } from '../services/api';
import type { Incident, Agent } from '../services/api';

interface MapMarkerProps {
  type: 'agent' | 'incident';
  data: Agent | Incident;
  onClick: () => void;
  isSelected: boolean;
}

const MapMarker = ({ type, data, onClick, isSelected }: MapMarkerProps) => {
  const isAgent = type === 'agent';
  const agent = isAgent ? data as Agent : undefined;
  const incident = !isAgent ? data as Incident : undefined;

  // Convert lat/lng to map coordinates
  const getMapPosition = () => {
    if (isAgent && agent?.location) {
      // Convert GPS coordinates to map percentage (simplified)
      const coords = getLocationCoords(agent.location);
      const x = ((coords.lng + 74.1) * 1000) % 80 + 10;
      const y = ((40.8 - coords.lat) * 1000) % 80 + 10;
      return { x: Math.max(5, Math.min(95, x)), y: Math.max(5, Math.min(95, y)) };
    } else if (incident?.location) {
      const coords = getLocationCoords(incident.location);
      const x = ((coords.lng + 74.1) * 1000) % 80 + 10;
      const y = ((40.8 - coords.lat) * 1000) % 80 + 10;
      return { x: Math.max(5, Math.min(95, x)), y: Math.max(5, Math.min(95, y)) };
    }
    return { x: 50, y: 50 }; // Default center position
  };

  const position = getMapPosition();

  const getMarkerColor = () => {
    if (isAgent) {
      switch (agent?.status) {
        case 'active': return 'bg-success';
        case 'busy': return 'bg-warning';
        case 'offline': return 'bg-muted-foreground';
        default: return 'bg-muted-foreground';
      }
    } else {
      switch (incident?.severity) {
        case 'critical': return 'bg-danger';
        case 'high': return 'bg-warning';
        case 'medium': return 'bg-neon-blue';
        case 'low': return 'bg-success';
        default: return 'bg-muted-foreground';
      }
    }
  };

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.2 }}
      whileTap={{ scale: 0.9 }}
      className={`
        absolute cursor-pointer transform -translate-x-1/2 -translate-y-1/2
        ${isSelected ? 'z-20' : 'z-10'}
      `}
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
      }}
      onClick={onClick}
    >
      <div className={`
        w-4 h-4 rounded-full ${getMarkerColor()}
        ${isSelected ? 'neon-glow animate-pulse-glow' : ''}
        border-2 border-background shadow-lg
        transition-all duration-300
      `} />
      
      {isSelected && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-6 left-1/2 transform -translate-x-1/2 min-w-48 z-30"
        >
          <div className="bg-command-surface border border-command-border rounded-lg p-3 shadow-xl">
            <div className="flex items-center space-x-2 mb-2">
              {isAgent ? (
                <Users className="w-4 h-4 text-neon-blue" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-danger" />
              )}
              <span className="font-medium text-foreground text-sm">
                {isAgent ? agent?.name : incident?.title}
              </span>
            </div>
            
            <div className="text-xs text-muted-foreground space-y-1">
              {isAgent ? (
                <>
                  <div>Status: <span className={`${getMarkerColor().replace('bg-', 'text-')}`}>
                    {agent?.status.toUpperCase()}
                  </span></div>
                  <div>Last seen: {agent?.lastSeen ? formatTime(agent.lastSeen) : 'Unknown'}</div>
                </>
              ) : (
                <>
                  <div>Severity: <span className={`${getMarkerColor().replace('bg-', 'text-')}`}>
                    {incident?.severity.toUpperCase()}
                  </span></div>
                  <div>Status: {incident?.status}</div>
                  <div>Time: {incident?.timestamp ? formatTime(incident.timestamp) : 'Unknown'}</div>
                </>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default function IncidentMap() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedMarker, setSelectedMarker] = useState<string | null>(null);
  const [mapLayer, setMapLayer] = useState<'satellite' | 'street' | 'tactical'>('tactical');
  const [zoomLevel, setZoomLevel] = useState(10);
  const mapRef = useRef<HTMLDivElement>(null);

  const { data: agents = [] } = useAgents();
  const { data: incidents = [] } = useIncidents();

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleMarkerClick = (id: string) => {
    setSelectedMarker(selectedMarker === id ? null : id);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -1 : 1;
    setZoomLevel(prev => Math.max(1, Math.min(20, prev + delta)));
  };

  const getLayerStyle = () => {
    switch (mapLayer) {
      case 'satellite':
        return 'bg-gradient-to-br from-gray-800 via-gray-700 to-gray-900';
      case 'street':
        return 'bg-gradient-to-br from-gray-200 via-gray-300 to-gray-400';
      case 'tactical':
        return 'bg-gradient-to-br from-command-bg via-command-surface to-gray-900';
      default:
        return 'bg-gradient-to-br from-command-bg via-command-surface to-gray-900';
    }
  };

  return (
    <motion.div
      animate={{
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : 'auto',
        left: isFullscreen ? 0 : 'auto',
        right: isFullscreen ? 0 : 'auto',
        bottom: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? 50 : 'auto',
      }}
      className={`
        ${isFullscreen ? 'w-screen h-screen' : 'w-full h-full'}
        bg-command-surface border border-command-border rounded-lg overflow-hidden
        transition-all duration-300
      `}
    >
      {/* Header Controls */}
      <div className="flex items-center justify-between p-4 bg-command-bg/80 backdrop-blur-sm border-b border-command-border">
        <div className="flex items-center space-x-4">
          <h3 className="font-bold text-foreground terminal-text">TACTICAL MAP</h3>
          
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
            <span className="text-xs text-success">GPS ACTIVE</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Layer Controls */}
          <div className="flex rounded border border-command-border overflow-hidden">
            {(['tactical', 'satellite', 'street'] as const).map((layer) => (
              <button
                key={layer}
                onClick={() => setMapLayer(layer)}
                className={`
                  px-3 py-1 text-xs font-medium uppercase transition-all duration-200
                  ${mapLayer === layer 
                    ? 'bg-neon-blue text-command-bg' 
                    : 'bg-command-surface text-muted-foreground hover:text-foreground'
                  }
                `}
              >
                {layer}
              </button>
            ))}
          </div>

          {/* Zoom Controls */}
          <div className="flex space-x-1">
            <button
              onClick={() => setZoomLevel(Math.min(20, zoomLevel + 1))}
              className="p-1 bg-command-surface border border-command-border rounded hover:bg-command-border transition-colors"
            >
              <ZoomIn className="w-4 h-4 text-muted-foreground" />
            </button>
            <button
              onClick={() => setZoomLevel(Math.max(1, zoomLevel - 1))}
              className="p-1 bg-command-surface border border-command-border rounded hover:bg-command-border transition-colors"
            >
              <ZoomOut className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>

          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            className="p-2 bg-command-surface border border-command-border rounded hover:bg-neon-blue hover:text-command-bg transition-all duration-200"
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div className="relative flex-1 h-full overflow-auto custom-scrollbar" onWheel={handleWheel}>
        <div
          ref={mapRef}
          className={`
            relative w-full h-full ${getLayerStyle()}
            min-w-full min-h-full overflow-hidden
          `}
          style={{
            transform: `scale(${Math.max(0.5, zoomLevel / 10)})`,
            transformOrigin: 'center center',
            width: zoomLevel > 10 ? `${100 + (zoomLevel - 10) * 10}%` : '100%',
            height: zoomLevel > 10 ? `${100 + (zoomLevel - 10) * 10}%` : '100%',
          }}
        >
          {/* Grid Overlay for Tactical View */}
          {mapLayer === 'tactical' && (
            <div className="absolute inset-0 opacity-20">
              <svg className="w-full h-full">
                <defs>
                  <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                    <path d="M 50 0 L 0 0 0 50" fill="none" stroke="currentColor" strokeWidth="1" className="text-neon-blue" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
            </div>
          )}

          {/* City Reference Points */}
          <div className="absolute inset-0 text-xs text-muted-foreground">
            <div className="absolute" style={{ left: '20%', top: '30%' }}>
              <div className="w-1 h-1 bg-muted-foreground rounded-full"></div>
              <span className="ml-2">Manhattan</span>
            </div>
            <div className="absolute" style={{ left: '60%', top: '45%' }}>
              <div className="w-1 h-1 bg-muted-foreground rounded-full"></div>
              <span className="ml-2">Brooklyn</span>
            </div>
            <div className="absolute" style={{ left: '35%', top: '70%' }}>
              <div className="w-1 h-1 bg-muted-foreground rounded-full"></div>
              <span className="ml-2">Staten Island</span>
            </div>
          </div>

          {/* Scanning Effect */}
          <div className="absolute inset-0 overflow-hidden">
            <motion.div
              animate={{
                rotate: 360,
              }}
              transition={{
                duration: 8,
                repeat: Infinity,
                ease: 'linear',
              }}
              className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
              style={{
                width: 'min(300px, 60vh, 60vw)',
                height: 'min(300px, 60vh, 60vw)',
              }}
            >
              {/* Radar Rings */}
              <div className="absolute inset-0 border border-neon-blue/30 rounded-full"></div>
              <div className="absolute inset-4 border border-neon-blue/20 rounded-full"></div>
              <div className="absolute inset-8 border border-neon-blue/15 rounded-full"></div>
              <div className="absolute inset-12 border border-neon-blue/10 rounded-full"></div>

              {/* Radar Sweep Line */}
              <div className="absolute top-0 left-1/2 w-0.5 h-1/2 bg-gradient-to-b from-neon-blue via-neon-blue/60 to-transparent transform -translate-x-1/2" />

              {/* Radar Center Dot */}
              <div className="absolute top-1/2 left-1/2 w-2 h-2 bg-neon-blue rounded-full transform -translate-x-1/2 -translate-y-1/2 animate-pulse" />
            </motion.div>
          </div>

          {/* Agent Markers */}
          <AnimatePresence>
            {agents.map((agent) => (
              <MapMarker
                key={agent.id}
                type="agent"
                data={agent}
                onClick={() => handleMarkerClick(agent.id)}
                isSelected={selectedMarker === agent.id}
              />
            ))}
          </AnimatePresence>

          {/* Incident Markers */}
          <AnimatePresence>
            {incidents.map((incident) => (
              <MapMarker
                key={incident.id}
                type="incident"
                data={incident}
                onClick={() => handleMarkerClick(incident.id)}
                isSelected={selectedMarker === incident.id}
              />
            ))}
          </AnimatePresence>

          {/* Center Crosshair with Coordinates */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <div className="w-6 h-6 border-2 border-neon-blue/50 rounded-full animate-pulse" />
            <div className="absolute top-1/2 left-1/2 w-8 h-0.5 bg-neon-blue/50 transform -translate-x-1/2 -translate-y-1/2" />
            <div className="absolute top-1/2 left-1/2 w-0.5 h-8 bg-neon-blue/50 transform -translate-x-1/2 -translate-y-1/2" />
            <div className="absolute top-8 left-1/2 transform -translate-x-1/2 text-xs text-neon-blue font-mono">
              40.7128°N, 74.0060°W
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-command-surface/90 backdrop-blur-sm border border-command-border rounded-lg p-3">
          <h4 className="text-xs font-medium text-foreground mb-2 terminal-text">LEGEND</h4>
          <div className="space-y-2 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success rounded-full" />
              <span className="text-muted-foreground">Active Agent</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-warning rounded-full" />
              <span className="text-muted-foreground">Busy Agent</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-danger rounded-full" />
              <span className="text-muted-foreground">Critical Incident</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-neon-blue rounded-full" />
              <span className="text-muted-foreground">Medium Incident</span>
            </div>
          </div>
        </div>

        {/* Stats Panel */}
        <div className="absolute top-4 right-4 bg-command-surface/90 backdrop-blur-sm border border-command-border rounded-lg p-3">
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between space-x-4">
              <span className="text-muted-foreground">Agents Online:</span>
              <span className="text-success font-medium">
                {agents.filter(a => a.status === 'active').length}/{agents.length}
              </span>
            </div>
            <div className="flex items-center justify-between space-x-4">
              <span className="text-muted-foreground">Active Incidents:</span>
              <span className="text-danger font-medium">
                {incidents.filter(i => i.status === 'active').length}
              </span>
            </div>
            <div className="flex items-center justify-between space-x-4">
              <span className="text-muted-foreground">Zoom Level:</span>
              <span className="text-neon-blue font-medium">{zoomLevel}x</span>
            </div>
            {zoomLevel > 10 && (
              <div className="text-neon-blue text-center pt-1 border-t border-command-border">
                <span className="text-xs">Scroll to pan map</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
