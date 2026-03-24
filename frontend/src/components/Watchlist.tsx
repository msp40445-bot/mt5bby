import { TrendingUp, TrendingDown } from 'lucide-react';

interface WatchlistItem {
  symbol: string;
  price: number;
  change: number;
  changePct: number;
  category: string;
}

const WATCHLIST_DATA: WatchlistItem[] = [
  { symbol: 'SPX', price: 6561.43, change: -18.56, changePct: -0.28, category: 'INDICES' },
  { symbol: 'NDQ', price: 24002.0, change: -186.52, changePct: -0.77, category: 'INDICES' },
  { symbol: 'DJI', price: 46188.6, change: -19.85, changePct: -0.04, category: 'INDICES' },
  { symbol: 'VIX', price: 27.12, change: 0.97, changePct: 3.71, category: 'INDICES' },
  { symbol: 'DXY', price: 99.51, change: 0.367, changePct: 0.37, category: 'INDICES' },
  { symbol: 'AAPL', price: 253.37, change: 1.88, changePct: 0.75, category: 'STOCKS' },
  { symbol: 'TSLA', price: 381.80, change: 0.95, changePct: 0.25, category: 'STOCKS' },
  { symbol: 'NFLX', price: 91.56, change: -1.80, changePct: -1.93, category: 'STOCKS' },
  { symbol: 'USOIL', price: 92.73, change: 3.87, changePct: 4.36, category: 'FUTURES' },
  { symbol: 'GOLD', price: 4395.79, change: -11.56, changePct: -0.26, category: 'FUTURES' },
  { symbol: 'SILVER', price: 69.22, change: 0.115, changePct: 0.17, category: 'FUTURES' },
  { symbol: 'EURUSD', price: 1.1571, change: -0.004, changePct: -0.34, category: 'FOREX' },
  { symbol: 'GBPUSD', price: 1.3374, change: -0.005, changePct: -0.37, category: 'FOREX' },
  { symbol: 'USDJPY', price: 159.05, change: 0.647, changePct: 0.41, category: 'FOREX' },
  { symbol: 'BTCUSD', price: 69192, change: -1691, changePct: -2.39, category: 'CRYPTO' },
  { symbol: 'ETHUSD', price: 2113.2, change: -38.5, changePct: -1.79, category: 'CRYPTO' },
];

export function Watchlist() {
  const categories = [...new Set(WATCHLIST_DATA.map(i => i.category))];

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden h-full">
      <div className="px-3 py-2 border-b border-slate-700/50 flex items-center justify-between">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Watchlist</h3>
      </div>
      <div className="text-xs">
        <div className="grid grid-cols-4 gap-1 px-3 py-1.5 text-slate-500 border-b border-slate-700/30 font-medium">
          <span>Symbol</span>
          <span className="text-right">Last</span>
          <span className="text-right">Chg</span>
          <span className="text-right">Chg%</span>
        </div>
        {categories.map(cat => (
          <div key={cat}>
            <div className="px-3 py-1 text-slate-500 text-xs font-medium bg-slate-800/30">
              ~ {cat}
            </div>
            {WATCHLIST_DATA.filter(i => i.category === cat).map(item => (
              <div
                key={item.symbol}
                className="grid grid-cols-4 gap-1 px-3 py-1 hover:bg-slate-700/30 transition-colors cursor-pointer border-b border-slate-700/10"
              >
                <span className="text-slate-300 font-medium flex items-center gap-1">
                  {item.change >= 0 ? (
                    <TrendingUp className="w-2.5 h-2.5 text-green-400" />
                  ) : (
                    <TrendingDown className="w-2.5 h-2.5 text-red-400" />
                  )}
                  {item.symbol}
                </span>
                <span className="text-right text-slate-200 font-mono">
                  {item.price >= 1000 ? item.price.toFixed(1) : item.price.toFixed(item.price < 10 ? 4 : 2)}
                </span>
                <span className={`text-right font-mono ${item.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {item.change >= 0 ? '+' : ''}{item.change >= 1000 ? item.change.toFixed(0) : item.change.toFixed(item.change < 1 && item.change > -1 ? 3 : 2)}
                </span>
                <span className={`text-right font-mono ${item.changePct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {item.changePct >= 0 ? '+' : ''}{item.changePct.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
