import { useState, useEffect, useMemo } from 'react';
import { Calculator, DollarSign, Target, TrendingUp, TrendingDown, RotateCcw } from 'lucide-react';
import type { AIDecision, PriceData } from '../hooks/useWebSocket';

interface PnLSimulatorProps {
  decision: AIDecision;
  price: PriceData;
}

export function PnLSimulator({ decision, price }: PnLSimulatorProps) {
  const [entryPrice, setEntryPrice] = useState<string>('');
  const [lotSize, setLotSize] = useState<string>('1.00');
  const [direction, setDirection] = useState<'LONG' | 'SHORT'>('LONG');

  // Auto-fill entry from AI decision
  useEffect(() => {
    if (decision.entry > 0 && entryPrice === '') {
      setEntryPrice(decision.entry.toFixed(2));
    }
  }, [decision.entry, entryPrice]);

  // Auto-set direction from AI decision
  useEffect(() => {
    if (decision.direction === 'BUY' || decision.direction === 'STRONG BUY') {
      setDirection('LONG');
    } else if (decision.direction === 'SELL' || decision.direction === 'STRONG SELL') {
      setDirection('SHORT');
    }
  }, [decision.direction]);

  const calculations = useMemo(() => {
    const entry = parseFloat(entryPrice) || 0;
    const lots = parseFloat(lotSize) || 0;
    const current = price.price;

    if (entry <= 0 || lots <= 0 || current <= 0) {
      return null;
    }

    const contractSize = 100; // 1 lot = 100 oz for gold
    const pipValue = 0.01;

    const priceDiff = direction === 'LONG'
      ? current - entry
      : entry - current;

    const pips = priceDiff / pipValue;
    const pnl = priceDiff * lots * contractSize;

    // Distance to TP and SL
    const tpDist = direction === 'LONG'
      ? decision.take_profit - current
      : current - decision.take_profit;
    const slDist = direction === 'LONG'
      ? current - decision.stop_loss
      : decision.stop_loss - current;

    const tpPnl = (direction === 'LONG'
      ? decision.take_profit - entry
      : entry - decision.take_profit) * lots * contractSize;
    const slPnl = (direction === 'LONG'
      ? decision.stop_loss - entry
      : entry - decision.stop_loss) * lots * contractSize;

    // Break-even price (already the entry)
    const breakEven = entry;

    // Percentage P&L
    const pnlPct = (priceDiff / entry) * 100;

    // Distance from entry
    const distFromEntry = Math.abs(current - entry);

    return {
      pnl: Math.round(pnl * 100) / 100,
      pips: Math.round(pips * 10) / 10,
      pnlPct: Math.round(pnlPct * 1000) / 1000,
      tpDist: Math.round(tpDist * 100) / 100,
      slDist: Math.round(slDist * 100) / 100,
      tpPnl: Math.round(tpPnl * 100) / 100,
      slPnl: Math.round(slPnl * 100) / 100,
      breakEven,
      distFromEntry: Math.round(distFromEntry * 100) / 100,
      isProfit: pnl >= 0,
    };
  }, [entryPrice, lotSize, direction, price.price, decision.take_profit, decision.stop_loss]);

  const useAIEntry = () => {
    setEntryPrice(decision.entry.toFixed(2));
  };

  const useCurrentPrice = () => {
    setEntryPrice(price.price.toFixed(2));
  };

  const resetSim = () => {
    setEntryPrice('');
    setLotSize('1.00');
  };

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-200">P&L Simulator</h3>
        </div>
        <button
          onClick={resetSim}
          className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1 transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          Reset
        </button>
      </div>

      <div className="p-4 space-y-3">
        {/* Direction Toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setDirection('LONG')}
            className={`flex-1 py-1.5 text-xs font-bold rounded transition-colors ${
              direction === 'LONG'
                ? 'bg-green-500/20 text-green-400 border border-green-500/40'
                : 'bg-slate-700/50 text-slate-500 border border-slate-600/30 hover:text-slate-400'
            }`}
          >
            LONG
          </button>
          <button
            onClick={() => setDirection('SHORT')}
            className={`flex-1 py-1.5 text-xs font-bold rounded transition-colors ${
              direction === 'SHORT'
                ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                : 'bg-slate-700/50 text-slate-500 border border-slate-600/30 hover:text-slate-400'
            }`}
          >
            SHORT
          </button>
        </div>

        {/* Entry Price */}
        <div>
          <label className="text-[10px] text-slate-500 uppercase font-medium mb-1 block">Entry Price</label>
          <div className="flex gap-1.5">
            <input
              type="number"
              value={entryPrice}
              onChange={(e) => setEntryPrice(e.target.value)}
              placeholder={price.price.toFixed(2)}
              className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded px-2.5 py-1.5 text-sm font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50"
              step="0.01"
            />
            <button onClick={useAIEntry} className="px-2 py-1 text-[10px] bg-purple-500/20 text-purple-300 rounded border border-purple-500/30 hover:bg-purple-500/30 transition-colors" title="Use AI suggested entry">
              AI
            </button>
            <button onClick={useCurrentPrice} className="px-2 py-1 text-[10px] bg-blue-500/20 text-blue-300 rounded border border-blue-500/30 hover:bg-blue-500/30 transition-colors" title="Use current price">
              MKT
            </button>
          </div>
        </div>

        {/* Lot Size */}
        <div>
          <label className="text-[10px] text-slate-500 uppercase font-medium mb-1 block">Lot Size</label>
          <div className="flex gap-1.5">
            <input
              type="number"
              value={lotSize}
              onChange={(e) => setLotSize(e.target.value)}
              className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded px-2.5 py-1.5 text-sm font-mono text-slate-200 focus:outline-none focus:border-cyan-500/50"
              step="0.01"
              min="0.01"
              max="100"
            />
            {[0.1, 0.5, 1, 2, 5].map((size) => (
              <button
                key={size}
                onClick={() => setLotSize(size.toFixed(2))}
                className={`px-1.5 py-1 text-[10px] rounded border transition-colors ${
                  parseFloat(lotSize) === size
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                    : 'bg-slate-700/30 text-slate-500 border-slate-600/30 hover:text-slate-400'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>

        {/* Results */}
        {calculations && (
          <>
            {/* Main P&L Display */}
            <div className={`rounded-lg p-3 text-center border ${
              calculations.isProfit
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="text-[10px] text-slate-500 uppercase mb-1">Unrealized P&L</div>
              <div className={`text-2xl font-black font-mono ${
                calculations.isProfit ? 'text-green-400' : 'text-red-400'
              }`}>
                {calculations.isProfit ? '+' : ''}{calculations.pnl < 0 ? '-' : ''}${Math.abs(calculations.pnl).toFixed(2)}
              </div>
              <div className="flex justify-center gap-3 mt-1">
                <span className={`text-xs font-mono ${calculations.isProfit ? 'text-green-400/70' : 'text-red-400/70'}`}>
                  {calculations.isProfit ? '+' : ''}{calculations.pips} pips
                </span>
                <span className={`text-xs font-mono ${calculations.isProfit ? 'text-green-400/70' : 'text-red-400/70'}`}>
                  {calculations.isProfit ? '+' : ''}{calculations.pnlPct.toFixed(3)}%
                </span>
              </div>
            </div>

            {/* Key Levels Grid */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-700/30 rounded p-2">
                <div className="flex items-center gap-1 mb-1">
                  <TrendingUp className="w-3 h-3 text-green-400" />
                  <span className="text-[10px] text-slate-500 uppercase">To TP</span>
                </div>
                <div className="text-sm font-bold text-green-400 font-mono">{calculations.tpDist >= 0 ? '+' : ''}{calculations.tpDist.toFixed(2)}</div>
                <div className="text-[10px] text-slate-500">P&L at TP: <span className="text-green-400">${calculations.tpPnl.toFixed(2)}</span></div>
              </div>
              <div className="bg-slate-700/30 rounded p-2">
                <div className="flex items-center gap-1 mb-1">
                  <TrendingDown className="w-3 h-3 text-red-400" />
                  <span className="text-[10px] text-slate-500 uppercase">To SL</span>
                </div>
                <div className="text-sm font-bold text-red-400 font-mono">{calculations.slDist >= 0 ? '+' : ''}{calculations.slDist.toFixed(2)}</div>
                <div className="text-[10px] text-slate-500">P&L at SL: <span className="text-red-400">${calculations.slPnl.toFixed(2)}</span></div>
              </div>
            </div>

            {/* Info Row */}
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Break Even</div>
                <div className="text-xs font-mono text-slate-300 font-semibold flex items-center justify-center gap-1">
                  <Target className="w-3 h-3 text-amber-400" />
                  {calculations.breakEven.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Dist</div>
                <div className="text-xs font-mono text-slate-300 font-semibold flex items-center justify-center gap-1">
                  <DollarSign className="w-3 h-3 text-slate-400" />
                  {calculations.distFromEntry.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">R:R</div>
                <div className="text-xs font-mono text-slate-300 font-semibold">
                  1:{decision.risk_reward}
                </div>
              </div>
            </div>
          </>
        )}

        {!calculations && (
          <div className="text-center py-4 text-xs text-slate-500">
            Enter a price and lot size to simulate P&L
          </div>
        )}
      </div>
    </div>
  );
}
