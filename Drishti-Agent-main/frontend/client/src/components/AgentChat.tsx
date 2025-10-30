import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Bot, 
  User, 
  Mic, 
  MicOff, 
  MoreVertical,
  Power,
  Zap,
  Shield
} from 'lucide-react';
import { useChatMessages, useSendMessage, formatTime } from '../services/api';
import type { ChatMessage } from '../services/api';

interface MessageBubbleProps {
  message: ChatMessage;
  index: number;
}

const MessageBubble = ({ message, index }: MessageBubbleProps) => {
  const isAI = message.sender === 'ai';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.1 }}
      className={`flex items-start space-x-3 ${isAI ? '' : 'flex-row-reverse space-x-reverse'} mb-4`}
    >
      {/* Avatar */}
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
        ${isAI 
          ? 'bg-neon-blue/20 border border-neon-blue/50' 
          : 'bg-success/20 border border-success/50'
        }
      `}>
        {isAI ? (
          <Bot className={`w-4 h-4 ${isAI ? 'text-neon-blue' : 'text-success'}`} />
        ) : (
          <User className={`w-4 h-4 ${isAI ? 'text-neon-blue' : 'text-success'}`} />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-xs ${isAI ? '' : 'text-right'}`}>
        <div className={`
          p-3 rounded-lg text-sm terminal-text
          ${isAI 
            ? 'bg-command-surface border border-command-border text-foreground' 
            : 'bg-neon-blue/20 border border-neon-blue/30 text-neon-blue'
          }
        `}>
          {message.message}
        </div>
        
        <div className={`text-xs text-muted-foreground mt-1 ${isAI ? '' : 'text-right'}`}>
          {formatTime(message.timestamp)}
        </div>
      </div>
    </motion.div>
  );
};

export default function AgentChat() {
  const [inputMessage, setInputMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [agentStatus, setAgentStatus] = useState<'online' | 'busy' | 'offline'>('online');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: messages = [] } = useChatMessages();
  const sendMessage = useSendMessage();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || sendMessage.isPending) return;

    const messageToSend = inputMessage.trim();
    setInputMessage('');
    
    try {
      await sendMessage.mutateAsync(messageToSend);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleVoiceToggle = () => {
    setIsRecording(!isRecording);
    // In a real implementation, this would handle voice recording
  };

  const getStatusColor = () => {
    switch (agentStatus) {
      case 'online': return 'text-success';
      case 'busy': return 'text-warning';
      case 'offline': return 'text-muted-foreground';
      default: return 'text-success';
    }
  };

  const getStatusIcon = () => {
    switch (agentStatus) {
      case 'online': return Shield;
      case 'busy': return Zap;
      case 'offline': return Power;
      default: return Shield;
    }
  };

  const StatusIcon = getStatusIcon();

  return (
    <div className="flex flex-col h-full bg-command-surface border border-command-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-command-bg border-b border-command-border">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className={`
              w-10 h-10 rounded-full bg-gradient-to-br from-neon-blue to-neon-cyan 
              flex items-center justify-center
            `}>
              <Bot className="w-5 h-5 text-command-bg" />
            </div>
            <div className={`
              absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-command-bg
              ${agentStatus === 'online' ? 'bg-success animate-pulse' : 
                agentStatus === 'busy' ? 'bg-warning' : 'bg-muted-foreground'}
            `} />
          </div>
          
          <div>
            <h3 className="font-bold text-foreground terminal-text">DRISHTI AEGIS AGENT</h3>
            <div className="flex items-center space-x-2">
              <StatusIcon className={`w-3 h-3 ${getStatusColor()}`} />
              <span className={`text-xs uppercase tracking-wider ${getStatusColor()}`}>
                {agentStatus}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-neon-blue rounded-full animate-pulse" />
            <span className="text-xs text-neon-blue">ENCRYPTED</span>
          </div>
          
          <button className="p-1 hover:bg-command-border rounded transition-colors">
            <MoreVertical className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        <AnimatePresence>
          {messages.map((message, index) => (
            <MessageBubble key={message.id} message={message} index={index} />
          ))}
        </AnimatePresence>

        {sendMessage.isPending && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-start space-x-3"
          >
            <div className="w-8 h-8 rounded-full bg-neon-blue/20 border border-neon-blue/50 flex items-center justify-center">
              <Bot className="w-4 h-4 text-neon-blue" />
            </div>
            <div className="bg-command-surface border border-command-border rounded-lg p-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-neon-blue rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-neon-blue rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-neon-blue rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-command-bg border-t border-command-border">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
          {/* Voice Input Button */}
          <button
            type="button"
            onClick={handleVoiceToggle}
            className={`
              p-2 rounded-lg transition-all duration-200 flex-shrink-0
              ${isRecording 
                ? 'bg-danger text-white animate-pulse-glow' 
                : 'bg-command-surface border border-command-border text-muted-foreground hover:text-foreground'
              }
            `}
          >
            {isRecording ? (
              <MicOff className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Enter command or query..."
              disabled={sendMessage.isPending}
              className={`
                w-full px-4 py-2 bg-command-surface border border-command-border 
                rounded-lg text-foreground placeholder-muted-foreground
                focus:outline-none focus:ring-2 focus:ring-neon-blue focus:border-neon-blue
                terminal-text text-sm
                ${sendMessage.isPending ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            />
            
            {/* Typing Indicator */}
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="w-2 h-2 bg-neon-blue rounded-full animate-pulse" />
            </div>
          </div>

          {/* Send Button */}
          <motion.button
            type="submit"
            disabled={!inputMessage.trim() || sendMessage.isPending}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`
              p-2 rounded-lg transition-all duration-200 flex-shrink-0
              ${inputMessage.trim() && !sendMessage.isPending
                ? 'bg-neon-blue text-command-bg hover:bg-neon-cyan neon-glow' 
                : 'bg-command-surface border border-command-border text-muted-foreground cursor-not-allowed'
              }
            `}
          >
            <Send className="w-4 h-4" />
          </motion.button>
        </form>

        {/* Quick Actions */}
        <div className="flex items-center space-x-2 mt-3">
          <span className="text-xs text-muted-foreground">Quick Actions:</span>
          {[
            'System Status',
            'Threat Analysis',
            'Deploy Units',
            'Emergency Protocol'
          ].map((action) => (
            <button
              key={action}
              onClick={() => setInputMessage(action)}
              className="px-2 py-1 text-xs bg-command-surface border border-command-border rounded text-muted-foreground hover:text-foreground hover:border-neon-blue transition-all duration-200"
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
