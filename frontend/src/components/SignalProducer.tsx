import type { MasterSignal, AIDecision, GaugeSummary } from '../hooks/useWebSocket';

interface Props {
  masterSignal: MasterSignal;
  aiDecision?: AIDecision;
  oscSummary: GaugeSummary;
  maSummary: GaugeSummary;
  overallSummary: GaugeSummary;
  currentPrice: number;
}

export function SignalProducer({ masterSignal, aiDecision, oscSummary, maSummary, overallSummary, currentPrice }: Props) {
  const signal = aiDecision?.direction || masterSignal.action;
  const confidence = masterSignal.confidence;
  const quality = aiDecision?.quality || 'N/A';

  const signalColor = () => {
    if (signal.includes('BUY')) return 'text-green-400 bg-green-500/10 border-green-500/30';
    if (signal.includes('SELL')) return 'text-red-400 bg-red-500/10 border-red-500/30';
    if (signal === 'EXIT') return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
  };

  const getManagementAdvice = () => {
    if (!aiDecision) return 'Waiting for data...';
    return aiDecision.action_advice || 'No advice available';
  };

  return (
    <div className="bg-slate-800/50 rounded border border-slate-700/50">
      <div className="px-3 py-1.5 border-b border-slate-700/30">
        <span className="text-xs font-bold text-slate-300">SIGNAL PRODUCER</span>
      </div>
      <div className="p-2">
        <div className="flex items-center gap-2 mb-2">
          <div className={`px-2 py-1 rounded border text-sm font-bold ${signalColor()}`}>
            {signal}
          </div>
          <div className="flex-1">
            <div className="flex justify-between text-[10px]">
              <span className="text-slate-500">Confidence</span>
              <span className="text-white">{confidence.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-1 mt-0.5">
              <div
                className={`h-1 rounded-full ${confidence > 70 ? 'bg-green-500' : confidence > 40 ? 'bg-amber-500' : 'bg-red-500'}`}
                style={{ width: `${Math.min(confidence, 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-1 text-[10px] mb-1.5">
          <div className="text-center">
            <span className="text-slate-500">OSC</span>
            <div className={oscSummary.signal.includes('Buy') ? 'text-green-400' : oscSummary.signal.includes('Sell') ? 'text-red-400' : 'text-slate-400'}>
              {oscSummary.signal}
            </div>
            <div className="text-slate-600">{oscSummary.buy}B/{oscSummary.sell}S/{oscSummary.neutral}N</div>
          </div>
          <div className="text-center">
            <span className="text-slate-500">MA</span>
            <div className={maSummary.signal.includes('Buy') ? 'text-green-400' : maSummary.signal.includes('Sell') ? 'text-red-400' : 'text-slate-400'}>
              {maSummary.signal}
            </div>
            <div className="text-slate-600">{maSummary.buy}B/{maSummary.sell}S/{maSummary.neutral}N</div>
          </div>
          <div className="text-center">
            <span className="text-slate-500">ALL</span>
            <div className={overallSummary.signal.includes('Buy') ? 'text-green-400' : overallSummary.signal.includes('Sell') ? 'text-red-400' : 'text-slate-400'}>
              {overallSummary.signal}
            </div>
            <div className="text-slate-600">{overallSummary.buy}B/{overallSummary.sell}S/{overallSummary.neutral}N</div>
          </div>
        </div>

        {aiDecision && (
          <div className="grid grid-cols-3 gap-1 text-[10px] border-t border-slate-700/30 pt-1.5">
            <div><span className="text-slate-500">Entry</span><br/><span className="text-white font-mono">{aiDecision.entry.toFixed(2)}</span></div>
            <div><span className="text-slate-500">TP</span><br/><span className="text-green-400 font-mono">{aiDecision.take_profit.toFixed(2)}</span></div>
            <div><span className="text-slate-500">SL</span><br/><span className="text-red-400 font-mono">{aiDecision.stop_loss.toFixed(2)}</span></div>
          </div>
        )}

        <div className="mt-1.5 text-[10px] text-slate-500 border-t border-slate-700/30 pt-1">
          <span className="text-slate-600">Quality: {quality} | R:R {aiDecision?.risk_reward.toFixed(1) || '0'}:1 | Price: {currentPrice.toFixed(2)}</span>
        </div>
        <div className="mt-1 text-[10px] text-slate-400 italic truncate">{getManagementAdvice()}</div>
      </div>
    </div>
  );
}
