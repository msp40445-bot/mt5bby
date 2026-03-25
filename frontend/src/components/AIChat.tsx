import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';

interface Props {
  chatMessages: Array<{role: string; message: string; timestamp: number}>;
  onSendChat: (message: string) => void;
}

export function AIChat({ chatMessages, onSendChat }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = () => {
    if (input.trim()) {
      onSendChat(input.trim());
      setInput('');
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-50 w-12 h-12 bg-purple-600 hover:bg-purple-500 rounded-full flex items-center justify-center shadow-lg shadow-purple-900/50 transition-all"
      >
        <MessageCircle className="w-5 h-5 text-white" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 h-96 bg-slate-800 border border-slate-700 rounded-lg shadow-xl flex flex-col">
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-700 bg-slate-800/90 rounded-t-lg">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-bold text-slate-200">MT5BBY AI</span>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {chatMessages.length === 0 && (
          <div className="text-center py-8">
            <MessageCircle className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs text-slate-500">Ask about signals, prices, or positions</p>
          </div>
        )}
        {chatMessages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] px-2 py-1.5 rounded text-xs ${
              msg.role === 'user'
                ? 'bg-purple-600/30 text-purple-200'
                : 'bg-slate-700/50 text-slate-300'
            }`}>
              {msg.message}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-2 border-t border-slate-700">
        <div className="flex gap-1.5">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask MT5BBY AI..."
            className="flex-1 bg-slate-700/50 border border-slate-600 rounded px-2 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
          <button onClick={handleSend} className="bg-purple-600 hover:bg-purple-500 rounded p-1.5">
            <Send className="w-3 h-3 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
