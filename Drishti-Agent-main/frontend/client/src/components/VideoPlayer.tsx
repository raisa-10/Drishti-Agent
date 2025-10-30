import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Maximize2, 
  Minimize2,
  SkipBack,
  SkipForward,
  RotateCcw,
  Settings,
  Download,
  Share
} from 'lucide-react';

interface VideoPlayerProps {
  videoUrl?: string;
  title?: string;
  timestamp?: Date;
  onFullscreen?: (isFullscreen: boolean) => void;
}

export default function VideoPlayer({ 
  videoUrl, 
  title = "Incident Recording", 
  timestamp = new Date(),
  onFullscreen 
}: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showControls, setShowControls] = useState(true);
  const [buffered, setBuffered] = useState(0);

  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout>();

  // Mock video duration for demo
  const mockDuration = 180; // 3 minutes

  useEffect(() => {
    setDuration(mockDuration);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (isPlaying) {
        setCurrentTime(prev => {
          const newTime = prev + 1;
          if (newTime >= duration) {
            setIsPlaying(false);
            return 0;
          }
          return newTime;
        });
        
        // Simulate buffering
        setBuffered(prev => Math.min(duration, prev + 2));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, duration]);

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const toggleFullscreen = () => {
    const newFullscreen = !isFullscreen;
    setIsFullscreen(newFullscreen);
    onFullscreen?.(newFullscreen);
  };

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!timelineRef.current) return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const newTime = (clickX / rect.width) * duration;
    setCurrentTime(Math.max(0, Math.min(duration, newTime)));
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      if (isPlaying) {
        setShowControls(false);
      }
    }, 3000);
  };

  const skipTime = (seconds: number) => {
    setCurrentTime(prev => Math.max(0, Math.min(duration, prev + seconds)));
  };

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`
        relative bg-black rounded-lg overflow-hidden border border-command-border
        ${isFullscreen ? 'fixed inset-0 z-50 rounded-none' : 'w-full h-full'}
      `}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setShowControls(true)}
    >
      {/* Video Element (Mock) */}
      <div className="relative w-full h-full min-h-64 bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center">
        {/* Mock Video Content */}
        <div className="text-center">
          <motion.div
            animate={{ 
              scale: isPlaying ? [1, 1.1, 1] : 1,
              opacity: isPlaying ? [0.5, 1, 0.5] : 0.7 
            }}
            transition={{ duration: 2, repeat: isPlaying ? Infinity : 0 }}
            className="w-24 h-24 mx-auto mb-4 bg-neon-blue/20 rounded-full flex items-center justify-center border border-neon-blue/50"
          >
            <div className="text-neon-blue text-sm font-mono">
              {isPlaying ? 'LIVE' : 'READY'}
            </div>
          </motion.div>
          
          <div className="text-white/60 text-sm font-mono">
            {title}
          </div>
          <div className="text-white/40 text-xs font-mono mt-1">
            {timestamp.toLocaleString()}
          </div>
        </div>

        {/* Play/Pause Overlay */}
        <AnimatePresence>
          {showControls && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={togglePlay}
              className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/40 transition-all duration-200"
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/30"
              >
                {isPlaying ? (
                  <Pause className="w-8 h-8 text-white" />
                ) : (
                  <Play className="w-8 h-8 text-white ml-1" />
                )}
              </motion.div>
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Controls Overlay */}
      <AnimatePresence>
        {showControls && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/60 to-transparent p-4"
          >
            {/* Timeline */}
            <div className="mb-4">
              <div
                ref={timelineRef}
                onClick={handleTimelineClick}
                className="relative h-2 bg-white/20 rounded-full cursor-pointer group"
              >
                {/* Buffered Progress */}
                <div
                  className="absolute top-0 left-0 h-full bg-white/30 rounded-full transition-all duration-300"
                  style={{ width: `${(buffered / duration) * 100}%` }}
                />
                
                {/* Current Progress */}
                <div
                  className="absolute top-0 left-0 h-full bg-neon-blue rounded-full transition-all duration-300"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
                
                {/* Scrubber */}
                <div
                  className="absolute top-1/2 transform -translate-y-1/2 w-4 h-4 bg-neon-blue rounded-full border-2 border-white shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                  style={{ left: `${(currentTime / duration) * 100}%`, marginLeft: '-8px' }}
                />
              </div>
              
              <div className="flex justify-between text-xs text-white/60 mt-1 font-mono">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {/* Play/Pause */}
                <button
                  onClick={togglePlay}
                  className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200"
                >
                  {isPlaying ? (
                    <Pause className="w-5 h-5 text-white" />
                  ) : (
                    <Play className="w-5 h-5 text-white" />
                  )}
                </button>

                {/* Skip Controls */}
                <button
                  onClick={() => skipTime(-10)}
                  className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200"
                >
                  <SkipBack className="w-4 h-4 text-white" />
                </button>
                
                <button
                  onClick={() => skipTime(10)}
                  className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200"
                >
                  <SkipForward className="w-4 h-4 text-white" />
                </button>

                {/* Volume */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={toggleMute}
                    className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200"
                  >
                    {isMuted ? (
                      <VolumeX className="w-4 h-4 text-white" />
                    ) : (
                      <Volume2 className="w-4 h-4 text-white" />
                    )}
                  </button>
                  
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={isMuted ? 0 : volume}
                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                    className="w-20 h-1 bg-white/20 rounded-full appearance-none slider"
                  />
                </div>

                {/* Speed Control */}
                <select
                  value={playbackSpeed}
                  onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
                  className="bg-white/20 text-white text-xs px-2 py-1 rounded border-none outline-none"
                >
                  <option value={0.5}>0.5x</option>
                  <option value={1}>1x</option>
                  <option value={1.25}>1.25x</option>
                  <option value={1.5}>1.5x</option>
                  <option value={2}>2x</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                {/* Additional Controls */}
                <button className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200">
                  <Download className="w-4 h-4 text-white" />
                </button>
                
                <button className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200">
                  <Share className="w-4 h-4 text-white" />
                </button>
                
                <button className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200">
                  <Settings className="w-4 h-4 text-white" />
                </button>

                {/* Fullscreen */}
                <button
                  onClick={toggleFullscreen}
                  className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-all duration-200"
                >
                  {isFullscreen ? (
                    <Minimize2 className="w-4 h-4 text-white" />
                  ) : (
                    <Maximize2 className="w-4 h-4 text-white" />
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Recording Indicator */}
      {isPlaying && (
        <div className="absolute top-4 left-4 flex items-center space-x-2 bg-black/60 backdrop-blur-sm rounded-full px-3 py-1">
          <div className="w-2 h-2 bg-danger rounded-full animate-pulse" />
          <span className="text-white text-xs font-mono">REC</span>
        </div>
      )}

      {/* Timestamp Overlay */}
      <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm rounded px-2 py-1">
        <span className="text-white text-xs font-mono">
          {timestamp.toLocaleString()}
        </span>
      </div>
    </motion.div>
  );
}
