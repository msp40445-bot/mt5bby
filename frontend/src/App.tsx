import { useWebSocket } from './hooks/useWebSocket';
import { PriceTicker } from './components/PriceTicker';
import { Gauge } from './components/Gauge';
import { IndicatorTable } from './components/IndicatorTable';
import { PivotTable } from './components/PivotTable';
import { SignalPanel } from './components/SignalPanel';
import { AIDecisionPanel } from './components/AIDecisionPanel';
import { AdvancedAnalysisPanel } from './components/AdvancedAnalysisPanel';
import { SimulationCard } from './components/SimulationCard';
import { SignalProducer } from './components/SignalProducer';
import { OrderBook } from './components/OrderBook';
import { BackendLogs } from './components/BackendLogs';
import { AIChat } from './components/AIChat';
import { BarChart3, Zap, Brain, Activity } from 'lucide-react';

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin w-10 h-10 border-3 border-amber-400 border-t-transparent rounded-full mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-200">Connecting...</h2>
        <p className="text-xs text-slate-500 mt-1">Initializing WebSocket</p>
      </div>
    </div>
  );
}

function App() {
  const { data, connected, latency, sendChat, forceClose, chatMessages } = useWebSocket();

  if (!data) {
    return <LoadingScreen />;
  }

  const feedSource = data.feed_source || 'simulation';

  return (
    <div className="h-screen bg-slate-950 text-slate-200 flex flex-col overflow-hidden">
      {/* Compact Header */}
      <header className="bg-slate-900/90 border-b border-slate-800 px-3 py-1.5 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-amber-400" />
          <h1 className="text-sm font-black tracking-tight">
            <span className="text-amber-400">MT5</span>
            <span className="text-slate-400">BBY</span>
          </h1>
          <span className="text-[10px] text-slate-600 hidden sm:inline">v3.0</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <Brain className="w-3 h-3 text-purple-400" />
            <span className="text-[10px] font-medium text-purple-400">AI</span>
          </div>
          <div className="flex items-center gap-1">
            <Activity className={feedSource === 'tradingview' ? 'w-3 h-3 text-blue-400' : feedSource === 'api_calibrated' ? 'w-3 h-3 text-green-400' : 'w-3 h-3 text-amber-400'} />
            <span className={`text-[10px] font-medium ${feedSource === 'tradingview' ? 'text-blue-400' : feedSource === 'api_calibrated' ? 'text-green-400' : 'text-amber-400'}`}>
              {feedSource === 'tradingview' ? 'TV' : feedSource === 'api_calibrated' ? 'API' : 'SIM'}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Zap className={connected ? 'w-3 h-3 text-green-400' : 'w-3 h-3 text-red-400'} />
            <span className={`text-[10px] font-medium ${connected ? 'text-green-400' : 'text-red-400'}`}>
              {connected ? 'LIVE' : 'OFF'}
            </span>
          </div>
          <span className="text-[10px] text-slate-600 font-mono">{latency}ms</span>
        </div>
      </header>

      {/* Main Grid Layout - Everything fits on 1 page */}
      <div className="flex-1 overflow-hidden p-1.5 gap-1.5 grid grid-rows-[auto_1fr_auto]" style={{ maxHeight: 'calc(100vh - 36px)' }}>

        {/* Top Row: Price + Signal Producer + Simulation */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-1.5">
          {/* Price Ticker - compact */}
          <div className="lg:col-span-3">
            <PriceTicker price={data.price} connected={connected} latency={latency} />
          </div>

          {/* Signal Producer */}
          <div className="lg:col-span-5">
            <SignalProducer
              masterSignal={data.master_signal}
              aiDecision={data.ai_decision}
              oscSummary={data.oscillator_summary}
              maSummary={data.ma_summary}
              overallSummary={data.overall_summary}
              currentPrice={data.price.price}
            />
          </div>

          {/* Simulation Card */}
          <div className="lg:col-span-4">
            {data.simulation && (
              <SimulationCard
                simulation={data.simulation}
                currentPrice={data.price.price}
                onForceClose={forceClose}
              />
            )}
          </div>
        </div>

        {/* Middle Row: Gauges + AI Decision + Advanced + Order Book */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-1.5 overflow-hidden">
          {/* Left Column: Gauges + Signals */}
          <div className="lg:col-span-3 space-y-1.5 overflow-y-auto">
            {/* 3 Gauges stacked compact */}
            <div className="bg-slate-800/50 rounded border border-slate-700/50 p-2">
              <div className="grid grid-cols-3 gap-1">
                <Gauge title="OSC" sell={data.oscillator_summary.sell} neutral={data.oscillator_summary.neutral} buy={data.oscillator_summary.buy} signal={data.oscillator_summary.signal} />
                <Gauge title="ALL" sell={data.overall_summary.sell} neutral={data.overall_summary.neutral} buy={data.overall_summary.buy} signal={data.overall_summary.signal} />
                <Gauge title="MA" sell={data.ma_summary.sell} neutral={data.ma_summary.neutral} buy={data.ma_summary.buy} signal={data.ma_summary.signal} />
              </div>
            </div>
            {/* Signal Panel */}
            <SignalPanel signals={data.timeframe_signals} masterSignal={data.master_signal} />
          </div>

          {/* Center: AI Decision + Indicators */}
          <div className="lg:col-span-6 space-y-1.5 overflow-y-auto">
            {data.ai_decision && (
              <AIDecisionPanel decision={data.ai_decision} feedSource={feedSource} />
            )}
            {/* Indicator Tables side by side */}
            <div className="grid grid-cols-2 gap-1.5">
              <IndicatorTable title="Oscillators" indicators={data.oscillators} />
              <IndicatorTable title="Moving Averages" indicators={data.moving_averages} />
            </div>
            {/* Advanced Analysis */}
            {data.advanced && (
              <AdvancedAnalysisPanel advanced={data.advanced} currentPrice={data.price.price} />
            )}
            {/* Pivots */}
            <PivotTable pivots={data.pivots} />
          </div>

          {/* Right Column: Order Book + Logs */}
          <div className="lg:col-span-3 space-y-1.5 overflow-y-auto">
            <OrderBook />
            <BackendLogs logs={data.backend_logs || []} />
          </div>
        </div>
      </div>

      {/* AI Chat Button (fixed bottom-right) */}
      <AIChat chatMessages={chatMessages} onSendChat={sendChat} />
    </div>
  );
}

export default App;
