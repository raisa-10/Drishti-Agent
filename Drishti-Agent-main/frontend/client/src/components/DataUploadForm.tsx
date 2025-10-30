import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  File, 
  Image, 
  Video, 
  FileText, 
  X, 
  Check, 
  AlertTriangle,
  Download,
  Eye,
  Trash2,
  RefreshCw
} from 'lucide-react';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  preview?: string;
}

const allowedTypes = {
  video: ['video/mp4', 'video/avi', 'video/mov', 'video/wmv'],
  image: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  document: ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  data: ['application/json', 'text/csv', 'application/xml']
};

const maxFileSize = 100 * 1024 * 1024; // 100MB

export default function DataUploadForm() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadMode, setUploadMode] = useState<'evidence' | 'intel' | 'media'>('evidence');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getFileIcon = (type: string) => {
    if (type.startsWith('video/')) return Video;
    if (type.startsWith('image/')) return Image;
    if (type.includes('pdf') || type.includes('document')) return FileText;
    return File;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > maxFileSize) {
      return { valid: false, error: 'File size exceeds 100MB limit' };
    }

    // Check file type based on upload mode
    const allAllowedTypes = Object.values(allowedTypes).flat();
    if (!allAllowedTypes.includes(file.type)) {
      return { valid: false, error: 'File type not supported' };
    }

    return { valid: true };
  };

  const simulateUpload = (fileId: string) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15 + 5;
      
      setFiles(prev => prev.map(file => 
        file.id === fileId 
          ? { ...file, progress: Math.min(100, progress) }
          : file
      ));

      if (progress >= 100) {
        clearInterval(interval);
        setFiles(prev => prev.map(file => 
          file.id === fileId 
            ? { ...file, status: 'completed', progress: 100 }
            : file
        ));
      }
    }, 200);
  };

  const handleFiles = useCallback((fileList: FileList) => {
    const newFiles: UploadedFile[] = [];

    Array.from(fileList).forEach(file => {
      const validation = validateFile(file);
      
      if (validation.valid) {
        const fileId = `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const uploadedFile: UploadedFile = {
          id: fileId,
          name: file.name,
          size: file.size,
          type: file.type,
          progress: 0,
          status: 'uploading',
        };

        // Create preview for images
        if (file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = (e) => {
            setFiles(prev => prev.map(f => 
              f.id === fileId 
                ? { ...f, preview: e.target?.result as string }
                : f
            ));
          };
          reader.readAsDataURL(file);
        }

        newFiles.push(uploadedFile);
        simulateUpload(fileId);
      }
    });

    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles]);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const retryUpload = (fileId: string) => {
    setFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, status: 'uploading', progress: 0 }
        : file
    ));
    simulateUpload(fileId);
  };

  const clearAllFiles = () => {
    setFiles([]);
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 custom-scrollbar">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold text-foreground terminal-text">DATA UPLOAD</h2>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-neon-blue rounded-full animate-pulse" />
            <span className="text-xs text-neon-blue">SECURE CHANNEL</span>
          </div>
        </div>

        {/* Upload Mode Selector */}
        <div className="flex rounded border border-command-border overflow-hidden">
          {(['evidence', 'intel', 'media'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setUploadMode(mode)}
              className={`
                px-4 py-2 text-xs font-medium uppercase transition-all duration-200
                ${uploadMode === mode 
                  ? 'bg-neon-blue text-command-bg' 
                  : 'bg-command-surface text-muted-foreground hover:text-foreground'
                }
              `}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Upload Zone */}
      <motion.div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        animate={{
          borderColor: isDragOver ? 'hsl(var(--neon-blue))' : 'hsl(var(--command-border))',
          backgroundColor: isDragOver ? 'hsl(var(--neon-blue) / 0.1)' : 'hsl(var(--command-surface))',
        }}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center
          transition-all duration-300 cursor-pointer group
          ${isDragOver ? 'neon-glow' : 'hover:border-neon-blue/50'}
        `}
        onClick={handleFileSelect}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          accept={Object.values(allowedTypes).flat().join(',')}
        />

        <motion.div
          animate={{ scale: isDragOver ? 1.1 : 1 }}
          className="space-y-4"
        >
          <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center ${
            isDragOver ? 'bg-neon-blue text-command-bg' : 'bg-neon-blue/20 text-neon-blue'
          } transition-all duration-300`}>
            <Upload className="w-8 h-8" />
          </div>

          <div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {isDragOver ? 'Drop files here' : 'Upload Files'}
            </h3>
            <p className="text-muted-foreground text-sm">
              Drag and drop files here, or click to select files
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Supports video, images, documents • Max 100MB per file
            </p>
          </div>

          <div className="text-xs text-muted-foreground">
            <div className="font-medium mb-1">Current mode: {uploadMode.toUpperCase()}</div>
            <div className="text-xs opacity-70">
              {uploadMode === 'evidence' && 'Crime scene photos, surveillance footage'}
              {uploadMode === 'intel' && 'Reports, documents, data files'}
              {uploadMode === 'media' && 'All media types and recordings'}
            </div>
          </div>
        </motion.div>

        {/* Scan Line Effect */}
        {isDragOver && (
          <div className="absolute inset-0 overflow-hidden rounded-lg">
            <div className="scan-line" />
          </div>
        )}
      </motion.div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground terminal-text">
              UPLOADED FILES ({files.length})
            </h3>
            <button
              onClick={clearAllFiles}
              className="text-sm text-muted-foreground hover:text-danger transition-colors flex items-center space-x-1"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear All</span>
            </button>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
            <AnimatePresence>
              {files.map((file) => {
                const FileIcon = getFileIcon(file.type);
                
                return (
                  <motion.div
                    key={file.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="bg-command-surface border border-command-border rounded-lg p-4"
                  >
                    <div className="flex items-center space-x-4">
                      {/* File Icon/Preview */}
                      <div className="flex-shrink-0">
                        {file.preview ? (
                          <img
                            src={file.preview}
                            alt={file.name}
                            className="w-12 h-12 object-cover rounded border border-command-border"
                          />
                        ) : (
                          <div className="w-12 h-12 bg-command-bg rounded flex items-center justify-center">
                            <FileIcon className="w-6 h-6 text-muted-foreground" />
                          </div>
                        )}
                      </div>

                      {/* File Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-foreground truncate terminal-text">
                            {file.name}
                          </h4>
                          
                          <div className="flex items-center space-x-2">
                            {file.status === 'completed' && (
                              <Check className="w-5 h-5 text-success" />
                            )}
                            {file.status === 'error' && (
                              <AlertTriangle className="w-5 h-5 text-danger" />
                            )}
                            {file.status === 'uploading' && (
                              <RefreshCw className="w-5 h-5 text-neon-blue animate-spin" />
                            )}
                            
                            <button
                              onClick={() => removeFile(file.id)}
                              className="text-muted-foreground hover:text-danger transition-colors"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-sm text-muted-foreground mt-1">
                          <span>{formatFileSize(file.size)}</span>
                          <span>{file.progress}%</span>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-command-bg rounded-full h-1.5 mt-2">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${file.progress}%` }}
                            className={`h-1.5 rounded-full transition-all duration-300 ${
                              file.status === 'completed' ? 'bg-success' :
                              file.status === 'error' ? 'bg-danger' :
                              'bg-neon-blue'
                            }`}
                          />
                        </div>

                        {/* Actions */}
                        {file.status === 'completed' && (
                          <div className="flex items-center space-x-3 mt-2">
                            <button className="text-xs text-neon-blue hover:underline flex items-center space-x-1">
                              <Eye className="w-3 h-3" />
                              <span>Preview</span>
                            </button>
                            <button className="text-xs text-neon-blue hover:underline flex items-center space-x-1">
                              <Download className="w-3 h-3" />
                              <span>Download</span>
                            </button>
                          </div>
                        )}

                        {file.status === 'error' && (
                          <button
                            onClick={() => retryUpload(file.id)}
                            className="text-xs text-danger hover:underline flex items-center space-x-1 mt-2"
                          >
                            <RefreshCw className="w-3 h-3" />
                            <span>Retry Upload</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Upload Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-command-border">
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">TOTAL FILES</div>
          <div className="text-foreground font-bold terminal-text">{files.length}</div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">COMPLETED</div>
          <div className="text-success font-bold terminal-text">
            {files.filter(f => f.status === 'completed').length}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">UPLOADING</div>
          <div className="text-neon-blue font-bold terminal-text">
            {files.filter(f => f.status === 'uploading').length}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">FAILED</div>
          <div className="text-danger font-bold terminal-text">
            {files.filter(f => f.status === 'error').length}
          </div>
        </div>
      </div>
    </div>
  );
}
