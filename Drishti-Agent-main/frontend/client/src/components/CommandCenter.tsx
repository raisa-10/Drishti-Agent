import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Menu, 
  X, 
  Shield, 
  Activity, 
  MessageSquare, 
  Map, 
  Video, 
  Settings, 
  Upload,
  Power,
  Bell,
  User
} from 'lucide-react';
import AlertPanel from './AlertPanel';
import IncidentMap from './IncidentMap';
import AgentChat from './AgentChat';
import VideoPlayer from './VideoPlayer';
import CommanderControls from './CommanderControls';
import DataUploadForm from './DataUploadForm';
import ApiTest from './ApiTest';

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ComponentType<any>;
  component: React.ComponentType<any>;
}

const navigationItems: NavigationItem[] = [
  { id: 'test', label: 'API Test', icon: Activity, component: ApiTest },
  { id: 'alerts', label: 'Alerts', icon: Bell, component: AlertPanel },
  { id: 'map', label: 'Tactical Map', icon: Map, component: IncidentMap },
  { id: 'chat', label: 'AI Agent', icon: MessageSquare, component: AgentChat },
  { id: 'video', label: 'Surveillance', icon: Video, component: VideoPlayer },
  { id: 'controls', label: 'Command', icon: Shield, component: CommanderControls },
  { id: 'upload', label: 'Data Upload', icon: Upload, component: DataUploadForm },
];

export default function CommandCenter() {
  const [activeTab, setActiveTab] = useState('test');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const ActiveComponent = navigationItems.find(item => item.id === activeTab)?.component || AlertPanel;

  return (
    <div className="h-screen bg-command-bg text-foreground overflow-hidden">
      {/* Header */}
      <header className="h-16 bg-command-surface border-b border-command-border flex items-center justify-between px-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 rounded-lg bg-command-bg border border-command-border hover:bg-command-border transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-neon-blue to-neon-cyan rounded flex items-center justify-center">
              <Shield className="w-5 h-5 text-command-bg" />
            </div>
            <div>
              <h1 className="text-xl font-bold terminal-text">DRISHTI AEGIS AGENT</h1>
              <div className="text-xs text-neon-blue">Security Intelligence System</div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* System Status */}
          <div className="flex items-center space-x-2 px-3 py-1 bg-success/20 border border-success/30 rounded-full">
            <Activity className="w-4 h-4 text-success animate-pulse" />
            <span className="text-xs text-success font-medium">OPERATIONAL</span>
          </div>

          {/* User Info */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-command-bg border border-command-border rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="text-sm">
              <div className="text-foreground">Commander</div>
              <div className="text-xs text-muted-foreground">Level 9 Access</div>
            </div>
          </div>

          {/* System Controls */}
          <button className="p-2 rounded-lg bg-command-bg border border-command-border hover:bg-danger hover:border-danger hover:text-white transition-all duration-200">
            <Power className="w-4 h-4" />
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-4rem)]">
        {/* Sidebar */}
        <motion.aside
          animate={{ width: sidebarCollapsed ? '4rem' : '16rem' }}
          className="bg-command-surface border-r border-command-border flex flex-col overflow-hidden"
        >
          <nav className="flex-1 p-2 space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              
              return (
                <motion.button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`
                    w-full flex items-center space-x-3 p-3 rounded-lg text-left transition-all duration-200
                    ${isActive 
                      ? 'bg-neon-blue text-command-bg neon-glow' 
                      : 'text-muted-foreground hover:text-foreground hover:bg-command-border'
                    }
                  `}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <AnimatePresence>
                    {!sidebarCollapsed && (
                      <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: 'auto' }}
                        exit={{ opacity: 0, width: 0 }}
                        className="font-medium terminal-text whitespace-nowrap"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.button>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="p-2 border-t border-command-border">
            <button className={`
              w-full flex items-center space-x-3 p-3 rounded-lg text-left transition-all duration-200
              text-muted-foreground hover:text-foreground hover:bg-command-border
            `}>
              <Settings className="w-5 h-5 flex-shrink-0" />
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="font-medium terminal-text whitespace-nowrap"
                  >
                    Settings
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          </div>
        </motion.aside>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              <ActiveComponent />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Global Scan Line Animation */}
      <div className="fixed top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-neon-blue to-transparent opacity-30 animate-scan-line pointer-events-none" />
    </div>
  );
}
