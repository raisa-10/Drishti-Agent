import { AlertPanel } from '@/components/dashboard/AlertPanel';
import { IncidentMap } from '@/components/dashboard/IncidentMap';
import { AgentChat } from '@/components/dashboard/AgentChat';
import { VideoPlayer } from '@/components/dashboard/VideoPlayer';
import { CommanderControls } from '@/components/dashboard/CommanderControls';
import { DataUploadForm } from '@/components/dashboard/DataUploadForm';

export function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      {/* Main Dashboard Grid */}
      <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-screen">
        {/* Left Column - Alerts */}
        <div className="lg:col-span-3">
          <AlertPanel />
        </div>

        {/* Center Column - Map and Video */}
        <div className="lg:col-span-6 space-y-6">
          {/* Incident Map */}
          <div className="h-[500px]">
            <IncidentMap />
          </div>
          
          {/* Video Player */}
          <div className="h-[400px]">
            <VideoPlayer />
          </div>
        </div>

        {/* Right Column - Chat and Controls */}
        <div className="lg:col-span-3 space-y-6">
          {/* Agent Chat */}
          <div className="h-[500px]">
            <AgentChat />
          </div>
          
          {/* Commander Controls and Upload Form in stacked layout for desktop */}
          <div className="grid grid-cols-1 xl:grid-cols-1 gap-6">
            <div className="h-[400px]">
              <CommanderControls />
            </div>
            
            <div className="h-[400px]">
              <DataUploadForm />
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Layout Adjustments */}
      <style jsx>{`
        @media (max-width: 1024px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
          }
          .dashboard-item {
            height: 400px;
          }
        }
      `}</style>
    </div>
  );
}
