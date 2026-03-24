import type { TimeframeSignal, MasterSignal } from '../hooks/useWebSocket';

interface SignalPanelProps {
  signals: TimeframeSignal[];
  masterSignal: MasterSignal;
}

function getSignalColor(label: string): string {
  switch (label) {
    case 'STRONG BUY': return '#22c55e';
    case 'BUY': return '#84cc16';
    case 'STRONG SELL': return '#ef4444';
    case 'SELL': return '#f97316';
    default: return '#94a3b8';
  }
}

function getStrengthBarWidth(strength: number): string {
  return `${Math.abs(strength) * 100}%`;
}

function TimeframeRow({ signal }: { signal: TimeframeSignal }) {
  const color = getSignalColor(signal.label);

  return (
    <div className="flex items-center gap-3 px-4 py-2 border-b border-slate-700/20 hover:bg-slate-700/20 transition-colors">
      <div className="w-12 text-xs font-mono text-slate-400 font-medium">{signal.timeframe}</div>
      <div className="flex-1">
        <div className="h-2 bg-slate-700 rounded-full overflow-hidden relative">
          <div
            className="absolute top-0 h-full rounded-full transition-all duration-300"
            style={{
              backgroundColor: color,
              width: getStrengthBarWidth(signal.strength),
              left: signal.strength >= 0 ? '50%' : `${50 - Math.abs(signal.strength) * 50}%`,
            }}
          />
          <div className="absolute top-0 left-1/2 w-px h-full bg-slate-500" />
        </div>
      </div>
      <div className="w-20 text-right">
        <span className="text-xs font-bold" style={{ color }}>{signal.label}</span>
      </div>
      <div className="w-16 text-right text-xs text-slate-400 font-mono">
        {(signal.strength * 100).toFixed(1)}%
      </div>
    </div>
  );
}

export function SignalPanel({ signals, masterSignal }: SignalPanelProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-700/50">
        <h3 className="text-sm font-semibold text-slate-200">Multi-Timeframe Signals</h3>
        <p className="text-xs text-slate-500 mt-0.5">Real-time signal across 8 timeframes (1s to 1h)</p>
      </div>

      {/* Master Signal */}
      <div className="px-4 py-4 border-b border-slate-600/50 bg-slate-800/80">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wider">Master Signal</div>
            <div className="text-2xl font-black mt-1" style={{ color: masterSignal.color }}>
              {masterSignal.action}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-500">Confidence</div>
            <div className="text-xl font-bold text-slate-200">{masterSignal.confidence}%</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-500">Strength</div>
            <div className="text-lg font-mono font-bold" style={{ color: masterSignal.color }}>
              {(masterSignal.strength * 100).toFixed(1)}%
            </div>
          </div>
        </div>
        <div className="flex gap-4 mt-3 text-xs">
          <span className="text-green-400">Buy: {masterSignal.total_buy}</span>
          <span className="text-slate-400">Neutral: {masterSignal.total_neutral}</span>
          <span className="text-red-400">Sell: {masterSignal.total_sell}</span>
        </div>
      </div>

      {/* Timeframe Signals */}
      <div className="divide-y divide-slate-700/20">
        <div className="flex items-center gap-3 px-4 py-1.5 text-xs text-slate-500 bg-slate-800/30">
          <div className="w-12 font-medium">TF</div>
          <div className="flex-1 text-center font-medium">← Sell | Buy →</div>
          <div className="w-20 text-right font-medium">Signal</div>
          <div className="w-16 text-right font-medium">Strength</div>
        </div>
        {signals.map((sig) => (
          <TimeframeRow key={sig.timeframe} signal={sig} />
        ))}
      </div>
    </div>
  );
}
