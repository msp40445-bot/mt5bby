import { useWebSocket } from './hooks/useWebSocket';
import { PriceTicker } from './components/PriceTicker';
import { Gauge } from './components/Gauge';
import { IndicatorTable } from './components/IndicatorTable';
import { PivotTable } from './components/PivotTable';
import { SignalPanel } from './components/SignalPanel';
import { Watchlist } from './components/Watchlist';
import { BarChart3, Zap } from 'lucide-react';

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin w-12 h-12 border-4 border-amber-400 border-t-transparent rounded-full mx-auto mb-4" />
        <h2 className="text-xl font-bold text-slate-200">Connecting to live feed...</h2>
        <p className="text-sm text-slate-500 mt-2">Initializing WebSocket connection</p>
      </div>
    </div>
  );
}

function App() {
  const { data, connected, latency } = useWebSocket();

  if (!data) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700/50 px-4 py-2.5 flex items-center justify-between sticky top-0 z-50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-amber-400" />
            <h1 className="text-lg font-black tracking-tight">
              <span className="text-amber-400">MT5</span>
              <span className="text-slate-300">BBY</span>
            </h1>
          </div>
          <span className="text-xs text-slate-500 hidden sm:inline">Trading Analysis Platform</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <Zap className={`w-3.5 h-3.5 ${connected ? 'text-green-400' : 'text-red-400'}`} />
            <span className={`text-xs font-medium ${connected ? 'text-green-400' : 'text-red-400'}`}>
              {connected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
          <span className="text-xs text-slate-500 font-mono">{latency}ms</span>
        </div>
      </header>

      <div className="flex">
        {/* Main Content */}
        <main className="flex-1 p-4 space-y-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 48px)' }}>
          {/* Price Ticker */}
          <PriceTicker price={data.price} connected={connected} latency={latency} />

          {/* Gauges Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4 flex justify-center">
              <Gauge
                title="Oscillators"
                sell={data.oscillator_summary.sell}
                neutral={data.oscillator_summary.neutral}
                buy={data.oscillator_summary.buy}
                signal={data.oscillator_summary.signal}
              />
            </div>
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4 flex justify-center">
              <Gauge
                title="Summary"
                sell={data.overall_summary.sell}
                neutral={data.overall_summary.neutral}
                buy={data.overall_summary.buy}
                signal={data.overall_summary.signal}
              />
            </div>
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4 flex justify-center">
              <Gauge
                title="Moving Averages"
                sell={data.ma_summary.sell}
                neutral={data.ma_summary.neutral}
                buy={data.ma_summary.buy}
                signal={data.ma_summary.signal}
              />
            </div>
          </div>

          {/* Multi-Timeframe Signal Panel */}
          <SignalPanel
            signals={data.timeframe_signals}
            masterSignal={data.master_signal}
          />

          {/* Indicator Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <IndicatorTable title="Oscillators" indicators={data.oscillators} />
            <IndicatorTable title="Moving Averages" indicators={data.moving_averages} />
          </div>

          {/* Pivot Table */}
          <PivotTable pivots={data.pivots} />
        </main>

        {/* Watchlist Sidebar */}
        <aside className="hidden xl:block w-72 border-l border-slate-700/50 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 48px)' }}>
          <Watchlist />
        </aside>
      </div>
    </div>
  );
}

export default App
