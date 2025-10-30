import { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, FileVideo, Trash2, CheckCircle, AlertTriangle, Clock } from 'lucide-react';
import { toast } from 'sonner';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  zone: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  uploadTime: Date;
}

const zones = [
  'Zone Alpha-1', 'Zone Alpha-2', 'Zone Alpha-3',
  'Zone Beta-1', 'Zone Beta-2',
  'Zone Gamma-1', 'Zone Gamma-2',
  'Zone Delta-1', 'Zone Delta-2'
];

export function DataUploadForm() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([
    {
      id: '1',
      name: 'incident_alpha3_14h23m.mp4',
      size: 15728640, // 15MB
      type: 'video/mp4',
      zone: 'Zone Alpha-3',
      status: 'completed',
      progress: 100,
      uploadTime: new Date(Date.now() - 300000)
    },
    {
      id: '2',
      name: 'security_check_beta1.mp4',
      size: 8388608, // 8MB
      type: 'video/mp4',
      zone: 'Zone Beta-1',
      status: 'completed',
      progress: 100,
      uploadTime: new Date(Date.now() - 600000)
    }
  ]);
  const [selectedZone, setSelectedZone] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading': return <Upload className="h-4 w-4 text-primary animate-pulse" />;
      case 'processing': return <Clock className="h-4 w-4 text-warning animate-spin" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-success" />;
      case 'failed': return <AlertTriangle className="h-4 w-4 text-destructive" />;
      default: return <Upload className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading': return 'bg-primary text-primary-foreground';
      case 'processing': return 'bg-warning text-warning-foreground';
      case 'completed': return 'bg-success text-success-foreground';
      case 'failed': return 'bg-destructive text-destructive-foreground';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const simulateUpload = (file: File, zone: string) => {
    const newFile: UploadedFile = {
      id: Date.now().toString(),
      name: file.name,
      size: file.size,
      type: file.type,
      zone,
      status: 'uploading',
      progress: 0,
      uploadTime: new Date()
    };

    setUploadedFiles(prev => [newFile, ...prev]);

    // Simulate upload progress
    const uploadInterval = setInterval(() => {
      setUploadedFiles(prev => prev.map(f => {
        if (f.id === newFile.id && f.status === 'uploading') {
          const newProgress = Math.min(f.progress + Math.random() * 20, 100);
          if (newProgress >= 100) {
            clearInterval(uploadInterval);
            
            // Start processing phase
            setTimeout(() => {
              setUploadedFiles(prev => prev.map(f2 => 
                f2.id === newFile.id ? { ...f2, status: 'processing' } : f2
              ));

              // Complete processing after 2 seconds
              setTimeout(() => {
                setUploadedFiles(prev => prev.map(f3 => 
                  f3.id === newFile.id ? { ...f3, status: 'completed' } : f3
                ));
                toast.success('Upload Completed', {
                  description: `${file.name} uploaded to ${zone}`,
                });
              }, 2000);
            }, 500);

            return { ...f, progress: 100, status: 'processing' as const };
          }
          return { ...f, progress: newProgress };
        }
        return f;
      }));
    }, 300);
  };

  const handleFileSelect = () => {
    if (!selectedZone) {
      toast.error('Please select a zone first');
      return;
    }
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    Array.from(files).forEach(file => {
      // Validate file type
      if (!file.type.startsWith('video/')) {
        toast.error('Invalid file type', {
          description: 'Please upload video files only',
        });
        return;
      }

      // Validate file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        toast.error('File too large', {
          description: 'Maximum file size is 100MB',
        });
        return;
      }

      simulateUpload(file, selectedZone);
    });

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    toast.success('File removed');
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Card className="h-full border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-foreground">
          <Upload className="h-5 w-5 text-primary" />
          Data Upload
          <Badge variant="secondary" className="ml-auto">
            {uploadedFiles.filter(f => f.status === 'completed').length} Files
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="p-4 space-y-6">
        {/* Upload Form */}
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="zone-select" className="text-sm font-medium text-foreground">
              Target Zone
            </Label>
            <Select value={selectedZone} onValueChange={setSelectedZone}>
              <SelectTrigger id="zone-select">
                <SelectValue placeholder="Select zone for upload" />
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

          <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">Video Files</Label>
            <div className="flex gap-2">
              <Button 
                onClick={handleFileSelect}
                disabled={!selectedZone}
                className="flex-1"
                variant="outline"
              >
                <FileVideo className="h-4 w-4 mr-2" />
                Select Video Files
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                multiple
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Supported formats: MP4, AVI, MOV. Max size: 100MB per file.
            </p>
          </div>
        </div>

        {/* Upload Queue */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-foreground">Upload Queue</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {uploadedFiles.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileVideo className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No files uploaded yet</p>
              </div>
            ) : (
              uploadedFiles.map((file) => (
                <div
                  key={file.id}
                  className="p-3 rounded-lg border border-border/50 bg-muted/20 hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {getStatusIcon(file.status)}
                      <span className="text-sm font-medium text-foreground truncate">
                        {file.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getStatusColor(file.status)} variant="secondary">
                        {file.status.toUpperCase()}
                      </Badge>
                      {file.status === 'completed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(file.id)}
                          className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {(file.status === 'uploading' || file.status === 'processing') && (
                    <div className="mb-2">
                      <Progress value={file.progress} className="h-2" />
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>{file.progress.toFixed(0)}%</span>
                        <span>{formatFileSize(file.size)}</span>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{file.zone}</span>
                    <span>{formatTime(file.uploadTime)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Upload Stats */}
        <div className="grid grid-cols-3 gap-4 p-3 bg-muted/30 rounded-lg border border-border/50">
          <div className="text-center">
            <div className="text-lg font-bold text-success">
              {uploadedFiles.filter(f => f.status === 'completed').length}
            </div>
            <div className="text-xs text-muted-foreground">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-warning">
              {uploadedFiles.filter(f => f.status === 'uploading' || f.status === 'processing').length}
            </div>
            <div className="text-xs text-muted-foreground">In Progress</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-primary">
              {formatFileSize(uploadedFiles.reduce((total, file) => total + file.size, 0))}
            </div>
            <div className="text-xs text-muted-foreground">Total Size</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
