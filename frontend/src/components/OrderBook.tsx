import { useState, useEffect } from 'react';

interface OrderBookEntry {
  price: number;
  volume: number;
  total: number;
}

interface OrderBookData {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  spread: number;
  mid_price: number;
}

export function OrderBook() {
  const [data, setData] = useState<OrderBookData | null>(null);

  useEffect(() => {
    const fetchOrderBook = async () => {
      try {
        const resp = await fetch('http://localhost:8000/api/orderbook');
        if (resp.ok) {
          setData(await resp.json());
        }
      } catch {
        // ignore
      }
    };
    fetchOrderBook();
    const interval = setInterval(fetchOrderBook, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!data) return null;

  const maxTotal = Math.max(
    data.bids[data.bids.length - 1]?.total || 0,
    data.asks[data.asks.length - 1]?.total || 0
  );

  return (
    <div className="bg-slate-800/50 rounded border border-slate-700/50">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-700/30">
        <span className="text-xs font-bold text-slate-300">ORDER BOOK</span>
        <span className="text-[10px] text-slate-500">Spread: {data.spread.toFixed(2)}</span>
      </div>
      <div className="p-1">
        <div className="grid grid-cols-3 text-[9px] text-slate-500 px-1 mb-0.5">
          <span>Price</span><span className="text-center">Vol</span><span className="text-right">Total</span>
        </div>
        {data.asks.slice().reverse().slice(0, 8).map((ask, i) => (
          <div key={`a${i}`} className="relative grid grid-cols-3 text-[10px] px-1 py-px">
            <div className="absolute right-0 top-0 bottom-0 bg-red-500/10" style={{ width: `${(ask.total / maxTotal) * 100}%` }} />
            <span className="text-red-400 font-mono relative z-10">{ask.price.toFixed(2)}</span>
            <span className="text-center text-slate-400 relative z-10">{ask.volume.toFixed(1)}</span>
            <span className="text-right text-slate-500 relative z-10">{ask.total.toFixed(1)}</span>
          </div>
        ))}
        <div className="text-center text-[10px] font-bold text-amber-400 py-0.5 border-y border-slate-700/30">
          {data.mid_price.toFixed(2)}
        </div>
        {data.bids.slice(0, 8).map((bid, i) => (
          <div key={`b${i}`} className="relative grid grid-cols-3 text-[10px] px-1 py-px">
            <div className="absolute left-0 top-0 bottom-0 bg-green-500/10" style={{ width: `${(bid.total / maxTotal) * 100}%` }} />
            <span className="text-green-400 font-mono relative z-10">{bid.price.toFixed(2)}</span>
            <span className="text-center text-slate-400 relative z-10">{bid.volume.toFixed(1)}</span>
            <span className="text-right text-slate-500 relative z-10">{bid.total.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
