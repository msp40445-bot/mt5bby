import { useEffect, useRef, useState } from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import type { PriceData } from '../hooks/useWebSocket';

interface PriceTickerProps {
  price: PriceData;
  connected: boolean;
  latency: number;
}

export function PriceTicker({ price, connected, latency }: PriceTickerProps) {
  const [flash, setFlash] = useState<'up' | 'down' | null>(null);
  const prevPriceRef = useRef(price.price);

  useEffect(() => {
    if (price.price > prevPriceRef.current) {
      setFlash('up');
    } else if (price.price < prevPriceRef.current) {
      setFlash('down');
    }
    prevPriceRef.current = price.price;

    const timer = setTimeout(() => setFlash(null), 200);
    return () => clearTimeout(timer);
  }, [price.price]);

  const isPositive = price.change >= 0;

  return (
    <div className="bg-slate-800/80 rounded-lg border border-slate-700/50 px-5 py-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg font-bold text-amber-400">{price.symbol}</span>
            <span className="text-xs text-slate-500">Gold Spot / U.S. Dollar</span>
          </div>
          <div className={`text-3xl font-black font-mono tracking-tight transition-colors duration-150 ${
            flash === 'up' ? 'text-green-400' : flash === 'down' ? 'text-red-400' : 'text-slate-100'
          }`}>
            {price.price.toFixed(2)}
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            {isPositive ? (
              <TrendingUp className="w-4 h-4 text-green-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-400" />
            )}
            <span className={`text-sm font-semibold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {isPositive ? '+' : ''}{price.change.toFixed(2)} ({isPositive ? '+' : ''}{price.change_pct.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="text-right space-y-1.5">
          <div className="flex items-center gap-1.5 justify-end">
            <Activity className={`w-3 h-3 ${connected ? 'text-green-400' : 'text-red-400'}`} />
            <span className={`text-xs ${connected ? 'text-green-400' : 'text-red-400'}`}>
              {connected ? 'LIVE' : 'DISCONNECTED'}
            </span>
          </div>
          <div className="text-xs text-slate-500">
            Latency: <span className="text-slate-400 font-mono">{latency}ms</span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs mt-2">
            <span className="text-slate-500">Bid</span>
            <span className="text-slate-300 font-mono text-right">{price.bid.toFixed(2)}</span>
            <span className="text-slate-500">Ask</span>
            <span className="text-slate-300 font-mono text-right">{price.ask.toFixed(2)}</span>
            <span className="text-slate-500">High</span>
            <span className="text-green-400/70 font-mono text-right">{price.high.toFixed(2)}</span>
            <span className="text-slate-500">Low</span>
            <span className="text-red-400/70 font-mono text-right">{price.low.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
