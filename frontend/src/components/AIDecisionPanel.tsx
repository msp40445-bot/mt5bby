import { ArrowUpCircle, ArrowDownCircle, PauseCircle, Brain, Target, Shield, TrendingUp, Zap } from 'lucide-react';
import type { AIDecision } from '../hooks/useWebSocket';

interface AIDecisionPanelProps {
  decision: AIDecision;
  feedSource?: string;
}

export function AIDecisionPanel({ decision, feedSource }: AIDecisionPanelProps) {
  const isBuy = decision.direction === 'BUY';
  const isSell = decision.direction === 'SELL';

  const dirColor = isBuy ? 'text-green-400' : isSell ? 'text-red-400' : 'text-amber-400';
  const dirBg = isBuy ? 'bg-green-500/10' : isSell ? 'bg-red-500/10' : 'bg-amber-500/10';
  const dirBorder = isBuy ? 'border-green-500/30' : isSell ? 'border-red-500/30' : 'border-amber-500/30';
  const DirIcon = isBuy ? ArrowUpCircle : isSell ? ArrowDownCircle : PauseCircle;

  return (
    <div className={'rounded-lg border-2 overflow-hidden ' + dirBorder + ' ' + dirBg}>
      <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-bold text-slate-200">AI Trading Decision</h3>
          {decision.ai_powered && (
            <span className="text-[10px] px-1.5 py-0.5 bg-purple-500/20 text-purple-300 rounded font-medium">LLM</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{ backgroundColor: decision.quality_color + '20', color: decision.quality_color }}>
            {decision.quality}
          </span>
          {feedSource && (
            <span className={feedSource === 'tradingview' ? 'text-[10px] px-1.5 py-0.5 rounded font-medium bg-blue-500/20 text-blue-300' : 'text-[10px] px-1.5 py-0.5 rounded font-medium bg-slate-500/20 text-slate-400'}>
              {feedSource === 'tradingview' ? 'LIVE' : 'SIM'}
            </span>
          )}
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <DirIcon className={'w-10 h-10 ' + dirColor} />
            <div>
              <div className={'text-3xl font-black ' + dirColor}>{decision.direction}</div>
              <div className="text-xs text-slate-500">Confidence: {decision.confidence.toFixed(1)}%</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-500">Risk/Reward</div>
            <div className="text-xl font-bold text-slate-200">1:{decision.risk_reward}</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-slate-800/80 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Target className="w-3 h-3 text-blue-400" />
              <span className="text-[10px] text-slate-500 uppercase font-medium">Entry</span>
            </div>
            <div className="text-lg font-bold text-blue-400 font-mono">{decision.entry.toFixed(2)}</div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <TrendingUp className="w-3 h-3 text-green-400" />
              <span className="text-[10px] text-slate-500 uppercase font-medium">Take Profit</span>
            </div>
            <div className="text-lg font-bold text-green-400 font-mono">{decision.take_profit.toFixed(2)}</div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Shield className="w-3 h-3 text-red-400" />
              <span className="text-[10px] text-slate-500 uppercase font-medium">Stop Loss</span>
            </div>
            <div className="text-lg font-bold text-red-400 font-mono">{decision.stop_loss.toFixed(2)}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-2.5 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Sim Profit (1 lot)</div>
            <div className="text-lg font-bold text-green-400 font-mono">+${decision.sim_profit.toFixed(2)}</div>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-2.5 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Sim Risk (1 lot)</div>
            <div className="text-lg font-bold text-red-400 font-mono">${decision.sim_loss.toFixed(2)}</div>
          </div>
        </div>

        {decision.commentary && (
          <div className="bg-slate-800/60 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Zap className="w-3 h-3 text-amber-400" />
              <span className="text-[10px] text-slate-500 uppercase font-medium">AI Analysis</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">{decision.commentary}</p>
          </div>
        )}

        <div className="space-y-1">
          <div className="text-[10px] text-slate-500 uppercase font-medium mb-1.5">Signal Factors</div>
          {decision.reasons.map((reason, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-slate-400">
              <span className="text-slate-600 mt-0.5">&#8226;</span>
              <span>{reason}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
