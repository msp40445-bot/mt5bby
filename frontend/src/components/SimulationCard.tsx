import { useState } from 'react';
import type { SimulationState } from '../hooks/useWebSocket';

interface Props {
  simulation: SimulationState;
  currentPrice: number;
  onForceClose: () => void;
}

export function SimulationCard({ simulation, currentPrice, onForceClose }: Props) {
  const [showHistory, setShowHistory] = useState(false);
  const trade = simulation.current_trade;
  const stats = simulation.stats;

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <div className="bg-slate-800/50 rounded border border-slate-700/50">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-700/30">
        <span className="text-xs font-bold text-slate-300">SIM <span className="text-amber-400 font-mono">{currentPrice.toFixed(2)}</span></span>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono ${stats.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            P&L: ${stats.total_pnl.toFixed(2)}
          </span>
          <button onClick={() => setShowHistory(!showHistory)} className="text-[10px] px-1.5 py-0.5 bg-slate-700 rounded text-slate-400 hover:text-white">
            {showHistory ? 'TRADE' : 'HISTORY'}
          </button>
        </div>
      </div>

      {!showHistory ? (
        <div className="p-2">
          {trade && trade.status === 'OPEN' ? (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${trade.direction === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {trade.direction}
                </span>
                <span className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${trade.pnl.toFixed(2)}
                </span>
              </div>
              <div className="grid grid-cols-4 gap-1 text-[10px]">
                <div><span className="text-slate-500">Entry</span><br/><span className="text-white font-mono">{trade.entry_price.toFixed(2)}</span></div>
                <div><span className="text-slate-500">TP</span><br/><span className="text-green-400 font-mono">{trade.take_profit.toFixed(2)}</span></div>
                <div><span className="text-slate-500">SL</span><br/><span className="text-red-400 font-mono">{trade.stop_loss.toFixed(2)}</span></div>
                <div><span className="text-slate-500">Time</span><br/><span className="text-slate-300 font-mono">{formatDuration(trade.duration_seconds)}</span></div>
              </div>
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-slate-500">BE: {trade.break_even_hit ? 'YES' : 'NO'} | Q: {trade.signal_quality} | C: {trade.confidence.toFixed(0)}%</span>
                <button onClick={onForceClose} className="px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 text-[10px]">CLOSE</button>
              </div>
            </div>
          ) : (
            <div className="text-center py-2">
              <span className="text-xs text-slate-500">Waiting for signal...</span>
              <div className="grid grid-cols-3 gap-2 mt-1.5 text-[10px]">
                <div><span className="text-slate-500">Trades</span><br/><span className="text-white">{stats.total_trades}</span></div>
                <div><span className="text-slate-500">Win Rate</span><br/><span className={stats.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}>{stats.win_rate.toFixed(0)}%</span></div>
                <div><span className="text-slate-500">PF</span><br/><span className="text-white">{stats.profit_factor.toFixed(2)}</span></div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-2 max-h-48 overflow-y-auto">
          {simulation.history.length === 0 ? (
            <div className="text-center py-2 text-xs text-slate-500">No trade history yet</div>
          ) : (
            <div className="space-y-1">
              {simulation.history.map((t) => (
                <div key={t.id} className="flex items-center justify-between text-[10px] py-0.5 border-b border-slate-700/30">
                  <div className="flex items-center gap-1.5">
                    <span className={t.direction === 'BUY' ? 'text-green-400' : 'text-red-400'}>{t.direction}</span>
                    <span className="text-slate-500">{t.entry_price.toFixed(2)}</span>
                    <span className="text-slate-600">-&gt;</span>
                    <span className="text-slate-400">{t.close_price?.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-500">{t.close_reason}</span>
                    <span className={t.pnl >= 0 ? 'text-green-400 font-mono' : 'text-red-400 font-mono'}>${t.pnl.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="mt-1.5 grid grid-cols-4 gap-1 text-[10px] border-t border-slate-700/30 pt-1.5">
            <div><span className="text-slate-500">Wins</span><br/><span className="text-green-400">{stats.win_count}</span></div>
            <div><span className="text-slate-500">Losses</span><br/><span className="text-red-400">{stats.loss_count}</span></div>
            <div><span className="text-slate-500">Avg Win</span><br/><span className="text-green-400">${stats.avg_win.toFixed(2)}</span></div>
            <div><span className="text-slate-500">Avg Loss</span><br/><span className="text-red-400">${stats.avg_loss.toFixed(2)}</span></div>
          </div>
        </div>
      )}
    </div>
  );
}
