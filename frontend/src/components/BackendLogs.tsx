import { useRef, useEffect } from 'react';
import type { BackendLog } from '../hooks/useWebSocket';

interface Props {
  logs: BackendLog[];
}

export function BackendLogs({ logs }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const levelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-400';
      case 'WARNING': return 'text-amber-400';
      case 'INFO': return 'text-blue-400';
      case 'DEBUG': return 'text-slate-500';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="bg-slate-800/50 rounded border border-slate-700/50">
      <div className="px-3 py-1.5 border-b border-slate-700/30">
        <span className="text-xs font-bold text-slate-300">BACKEND LOGS</span>
      </div>
      <div ref={containerRef} className="p-1 max-h-32 overflow-y-auto font-mono">
        {(!logs || logs.length === 0) ? (
          <div className="text-center py-2 text-[10px] text-slate-600">No logs yet</div>
        ) : (
          logs.slice(-20).map((log, i) => (
            <div key={i} className="text-[9px] leading-tight py-px flex gap-1">
              <span className={levelColor(log.level)}>[{log.level.slice(0, 4)}]</span>
              <span className="text-slate-400 truncate">{log.message.replace(/^[\d\-:.\s]+\[\w+\]\s*[\w.]+:\s*/, '')}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
