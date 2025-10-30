import { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Play, Pause, Volume2, VolumeX, Maximize, Download, RotateCcw, Settings } from 'lucide-react';

interface VideoFeed {
  id: string;
  name: string;
  zone: string;
  status: 'live' | 'recorded' | 'offline';
  timestamp?: string;
  duration?: string;
}

const mockVideoFeeds: VideoFeed[] = [
  {
    id: 'cam-001',
    name: 'Main Entrance',
    zone: 'Zone Alpha-3',
    status: 'live',
  },
  {
    id: 'cam-002',
    name: 'Perimeter Check',
    zone: 'Zone Beta-1',
    status: 'recorded',
    timestamp: '14:23:15',
    duration: '02:45'
  },
  {
    id: 'cam-003',
    name: 'Crowd Monitor',
    zone: 'Zone Gamma-2',
    status: 'live',
  },
  {
    id: 'cam-004',
    name: 'Emergency Exit',
    zone: 'Zone Delta-1',
    status: 'offline',
  },
];

export function VideoPlayer() {
  const [selectedFeed, setSelectedFeed] = useState<VideoFeed>(mockVideoFeeds[0]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration] = useState(165); // 2:45 in seconds
  const videoRef = useRef<HTMLDivElement>(null);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: VideoFeed['status']) => {
    switch (status) {
      case 'live': return 'bg-destructive text-destructive-foreground animate-pulse';
      case 'recorded': return 'bg-warning text-warning-foreground';
      case 'offline': return 'bg-muted text-muted-foreground';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusText = (status: VideoFeed['status']) => {
    switch (status) {
      case 'live': return 'LIVE';
      case 'recorded': return 'RECORDED';
      case 'offline': return 'OFFLINE';
      default: return 'UNKNOWN';
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
    // Simulate time progression for recorded videos
    if (selectedFeed.status === 'recorded' && !isPlaying) {
      const interval = setInterval(() => {
        setCurrentTime(prev => {
          if (prev >= duration) {
            setIsPlaying(false);
            clearInterval(interval);
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    }
  };

  return (
    <Card className="h-full border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-foreground">
          <div className="flex items-center gap-2">
            <Play className="h-5 w-5 text-primary" />
            Video Feeds
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedFeed.id} onValueChange={(value) => {
              const feed = mockVideoFeeds.find(f => f.id === value);
              if (feed) {
                setSelectedFeed(feed);
                setIsPlaying(false);
                setCurrentTime(0);
              }
            }}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {mockVideoFeeds.map((feed) => (
                  <SelectItem key={feed.id} value={feed.id}>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        feed.status === 'live' ? 'bg-destructive animate-pulse' :
                        feed.status === 'recorded' ? 'bg-warning' : 'bg-muted'
                      }`} />
                      {feed.name} - {feed.zone}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="p-4">
        <div className="space-y-4">
          {/* Video Display Area */}
          <div className="relative bg-black rounded-lg overflow-hidden aspect-video border border-border/50">
            {selectedFeed.status === 'offline' ? (
              <div className="absolute inset-0 flex items-center justify-center bg-muted/80">
                <div className="text-center">
                  <div className="text-4xl mb-2">📹</div>
                  <p className="text-muted-foreground">Camera Offline</p>
                  <p className="text-sm text-muted-foreground">{selectedFeed.name}</p>
                </div>
              </div>
            ) : (
              <div 
                ref={videoRef}
                className="absolute inset-0 bg-gradient-to-br from-slate-800 to-slate-900"
              >
                {/* Simulated Video Content */}
                <div className="absolute inset-4 border-2 border-primary/30 rounded">
                  <div className="relative h-full bg-slate-700/50 rounded overflow-hidden">
                    {/* Animated elements to simulate video */}
                    <div className="absolute top-4 left-4 w-8 h-8 bg-primary/60 rounded-full animate-ping" />
                    <div className="absolute bottom-4 right-4 w-16 h-16 bg-warning/40 rounded animate-pulse" />
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                      <div className="text-white/80 text-center">
                        <div className="text-2xl mb-2">🎥</div>
                        <p className="text-sm">{selectedFeed.name}</p>
                        <p className="text-xs text-primary">{selectedFeed.zone}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Status Badge */}
                <div className="absolute top-4 right-4">
                  <Badge className={getStatusColor(selectedFeed.status)}>
                    {getStatusText(selectedFeed.status)}
                  </Badge>
                </div>

                {/* Timestamp for recorded videos */}
                {selectedFeed.status === 'recorded' && selectedFeed.timestamp && (
                  <div className="absolute top-4 left-4 bg-black/60 text-white text-xs px-2 py-1 rounded">
                    {selectedFeed.timestamp}
                  </div>
                )}

                {/* Live indicator */}
                {selectedFeed.status === 'live' && (
                  <div className="absolute bottom-4 left-4 flex items-center gap-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
                    <div className="w-2 h-2 bg-destructive rounded-full animate-pulse" />
                    LIVE
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Video Controls */}
          <div className="space-y-3">
            {/* Progress Bar (for recorded videos) */}
            {selectedFeed.status === 'recorded' && (
              <div className="space-y-1">
                <div className="relative h-2 bg-muted rounded-full">
                  <div 
                    className="absolute top-0 left-0 h-full bg-primary rounded-full transition-all"
                    style={{ width: `${(currentTime / duration) * 100}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
              </div>
            )}

            {/* Control Buttons */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {selectedFeed.status !== 'offline' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePlayPause}
                    disabled={selectedFeed.status === 'live'}
                  >
                    {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                )}
                
                <Button variant="outline" size="sm" onClick={() => setIsMuted(!isMuted)}>
                  {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                </Button>

                {selectedFeed.status === 'recorded' && (
                  <Button variant="outline" size="sm" onClick={() => setCurrentTime(0)}>
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                )}
              </div>

              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm">
                  <Maximize className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Feed Information */}
          <div className="grid grid-cols-2 gap-4 p-3 bg-muted/30 rounded-lg border border-border/50">
            <div>
              <p className="text-xs text-muted-foreground">Camera</p>
              <p className="font-medium text-foreground">{selectedFeed.name}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Zone</p>
              <p className="font-medium text-foreground">{selectedFeed.zone}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
