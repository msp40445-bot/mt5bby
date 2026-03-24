import { useState } from 'react';
import { BarChart3, Clock, TrendingUp, TrendingDown } from 'lucide-react';
import type { AIDecision } from '../hooks/useWebSocket';

interface StatsPanelProps {
  decision: AIDecision;
}

interface SignalRecord {
  direction: string;
  entry: number;
  take_profit: number;
  stop_loss: number;
  confidence: number;
  timestamp: number;
}

export function StatsPanel({ decision }: StatsPanelProps) {
  const [history, setHistory] = useState<SignalRecord[]>([]);
  const [lastRecorded, setLastRecorded] = useState(0);

  // Record new signals (debounced by 10 seconds)
  if (decision && decision.timestamp - lastRecorded > 10) {
    const record: SignalRecord = {
      direction: decision.direction,
      entry: decision.entry,
      take_profit: decision.take_profit,
      stop_loss: decision.stop_loss,
      confidence: decision.confidence,
      timestamp: decision.timestamp,
    };
    setHistory(prev => [record, ...prev].slice(0, 50));
    setLastRecorded(decision.timestamp);
  }

  const buyCount = history.filter(h => h.direction === 'BUY').length;
  const sellCount = history.filter(h => h.direction === 'SELL').length;
  const holdCount = history.filter(h => h.direction !== 'BUY' && h.direction !== 'SELL').length;
  const total = history.length || 1;

  const avgConfidence = history.length > 0
    ? history.reduce((sum, h) => sum + h.confidence, 0) / history.length
    : 0;

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-700/50 flex items-center gap-2">
        <BarChart3 className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-bold text-slate-200">Signal Statistics</h3>
        <span className="text-[10px] text-slate-500 ml-auto">{history.length} signals tracked</span>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="text-center">
            <div className="text-[10px] text-slate-500 uppercase mb-1">Buy</div>
            <div className="text-lg font-bold text-green-400">{buyCount}</div>
            <div className="text-[10px] text-slate-500">{((buyCount / total) * 100).toFixed(0)}%</div>
          </div>
          <div className="text-center">
            <div className="text-[10px] text-slate-500 uppercase mb-1">Sell</div>
            <div className="text-lg font-bold text-red-400">{sellCount}</div>
            <div className="text-[10px] text-slate-500">{((sellCount / total) * 100).toFixed(0)}%</div>
          </div>
          <div className="text-center">
            <div className="text-[10px] text-slate-500 uppercase mb-1">Hold</div>
            <div className="text-lg font-bold text-amber-400">{holdCount}</div>
            <div className="text-[10px] text-slate-500">{((holdCount / total) * 100).toFixed(0)}%</div>
          </div>
          <div className="text-center">
            <div className="text-[10px] text-slate-500 uppercase mb-1">Avg Conf</div>
            <div className="text-lg font-bold text-slate-200">{avgConfidence.toFixed(0)}%</div>
          </div>
        </div>

        <div className="text-[10px] text-slate-500 uppercase font-medium mb-2">Recent Signals</div>
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {history.slice(0, 15).map((sig, i) => (
            <div key={i} className="flex items-center gap-2 text-xs py-1 border-b border-slate-700/20">
              <span className="w-4">
                {sig.direction === 'BUY' ? <TrendingUp className="w-3 h-3 text-green-400" /> : sig.direction === 'SELL' ? <TrendingDown className="w-3 h-3 text-red-400" /> : <Clock className="w-3 h-3 text-amber-400" />}
              </span>
              <span className={sig.direction === 'BUY' ? 'w-10 font-semibold text-green-400' : sig.direction === 'SELL' ? 'w-10 font-semibold text-red-400' : 'w-10 font-semibold text-amber-400'}>{sig.direction}</span>
              <span className="text-slate-400 font-mono flex-1">{sig.entry.toFixed(2)}</span>
              <span className="text-slate-500">{sig.confidence.toFixed(0)}%</span>
              <span className="text-slate-600 text-[10px]">{new Date(sig.timestamp * 1000).toLocaleTimeString()}</span>
            </div>
          ))}
          {history.length === 0 && (
            <div className="text-xs text-slate-500 py-2 text-center">Collecting signals...</div>
          )}
        </div>
      </div>
    </div>
  );
}
