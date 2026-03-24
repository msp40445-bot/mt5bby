import { Activity, BarChart2, Layers, GitBranch, TrendingUp, TrendingDown } from 'lucide-react';
import type { AdvancedAnalysis } from '../hooks/useWebSocket';

interface AdvancedAnalysisPanelProps {
  advanced: AdvancedAnalysis;
  currentPrice: number;
}

export function AdvancedAnalysisPanel({ advanced, currentPrice }: AdvancedAnalysisPanelProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {advanced.bollinger_bands && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Activity className="w-3.5 h-3.5 text-purple-400" />
              <h4 className="text-xs font-semibold text-slate-300">Bollinger Bands</h4>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Upper</span>
                <span className="text-red-400 font-mono">{advanced.bollinger_bands.upper.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Middle</span>
                <span className="text-slate-300 font-mono">{advanced.bollinger_bands.middle.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Lower</span>
                <span className="text-green-400 font-mono">{advanced.bollinger_bands.lower.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pt-1 border-t border-slate-700/30">
                <span className="text-slate-500">%B</span>
                <span className="text-slate-300 font-mono">{advanced.bollinger_bands.percent_b.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        )}

        {advanced.atr && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <BarChart2 className="w-3.5 h-3.5 text-amber-400" />
              <h4 className="text-xs font-semibold text-slate-300">ATR ({advanced.atr.period})</h4>
            </div>
            <div className="text-2xl font-bold text-amber-400 font-mono mb-1">{advanced.atr.value.toFixed(2)}</div>
            <div className="text-xs text-slate-500">
              Volatility: {currentPrice > 0 ? ((advanced.atr.value / currentPrice) * 100).toFixed(3) : '0'}%
            </div>
          </div>
        )}

        {advanced.vwap && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <h4 className="text-xs font-semibold text-slate-300">VWAP</h4>
            </div>
            <div className="text-lg font-bold text-cyan-400 font-mono mb-1">{advanced.vwap.value.toFixed(2)}</div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Signal</span>
                <span className={advanced.vwap.signal === 'Buy' ? 'text-green-400 font-semibold' : advanced.vwap.signal === 'Sell' ? 'text-red-400 font-semibold' : 'text-slate-400 font-semibold'}>
                  {advanced.vwap.signal}
                </span>
              </div>
            </div>
          </div>
        )}

        {advanced.obv && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
              <h4 className="text-xs font-semibold text-slate-300">OBV</h4>
            </div>
            <div className="text-lg font-bold text-emerald-400 font-mono mb-1">
              {Math.abs(advanced.obv.value) > 1000000
                ? (advanced.obv.value / 1000000).toFixed(1) + 'M'
                : Math.abs(advanced.obv.value) > 1000
                ? (advanced.obv.value / 1000).toFixed(1) + 'K'
                : advanced.obv.value.toFixed(0)}
            </div>
            <div className="flex items-center gap-1 text-xs">
              <span className="text-slate-500">Trend:</span>
              <span className={advanced.obv.trend === 'Rising' ? 'text-green-400 font-semibold' : advanced.obv.trend === 'Falling' ? 'text-red-400 font-semibold' : 'text-slate-400 font-semibold'}>
                {advanced.obv.trend}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {advanced.market_structure && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <GitBranch className="w-3.5 h-3.5 text-blue-400" />
              <h4 className="text-xs font-semibold text-slate-300">Market Structure</h4>
            </div>
            <div className={advanced.market_structure.trend === 'Uptrend' ? 'text-lg font-bold mb-2 text-green-400' : advanced.market_structure.trend === 'Downtrend' ? 'text-lg font-bold mb-2 text-red-400' : 'text-lg font-bold mb-2 text-amber-400'}>
              {advanced.market_structure.trend === 'Uptrend' && <TrendingUp className="w-4 h-4 inline mr-1" />}
              {advanced.market_structure.trend === 'Downtrend' && <TrendingDown className="w-4 h-4 inline mr-1" />}
              {advanced.market_structure.trend}
            </div>
            <div className="grid grid-cols-2 gap-1.5 text-xs">
              <div className="flex justify-between"><span className="text-slate-500">HH</span><span className="text-green-400 font-mono">{advanced.market_structure.higher_highs}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">LH</span><span className="text-red-400 font-mono">{advanced.market_structure.lower_highs}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">HL</span><span className="text-green-400 font-mono">{advanced.market_structure.higher_lows}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">LL</span><span className="text-red-400 font-mono">{advanced.market_structure.lower_lows}</span></div>
            </div>
          </div>
        )}

        <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <Activity className="w-3.5 h-3.5 text-orange-400" />
            <h4 className="text-xs font-semibold text-slate-300">Candlestick Patterns</h4>
          </div>
          {advanced.patterns && advanced.patterns.length > 0 ? (
            <div className="space-y-1.5">
              {advanced.patterns.map((pattern, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">{pattern.name}</span>
                  <span className={pattern.bias === 'Bullish' ? 'text-green-400 font-semibold' : pattern.bias === 'Bearish' ? 'text-red-400 font-semibold' : 'text-slate-400 font-semibold'}>
                    {pattern.bias}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-500 py-2">No patterns detected</div>
          )}
        </div>

        {advanced.trend_strength && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
              <h4 className="text-xs font-semibold text-slate-300">Trend Analysis</h4>
            </div>
            <div className={advanced.trend_strength.direction.includes('Up') ? 'text-lg font-bold mb-1 text-green-400' : advanced.trend_strength.direction.includes('Down') ? 'text-lg font-bold mb-1 text-red-400' : 'text-lg font-bold mb-1 text-amber-400'}>
              {advanced.trend_strength.direction}
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">MA Alignment</span>
                <span className={advanced.trend_strength.ma_alignment === 'Bullish' ? 'text-green-400 font-semibold' : advanced.trend_strength.ma_alignment === 'Bearish' ? 'text-red-400 font-semibold' : 'text-amber-400 font-semibold'}>
                  {advanced.trend_strength.ma_alignment}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Slope</span>
                <span className="text-slate-400 font-mono">{advanced.trend_strength.slope.toFixed(4)}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {advanced.fibonacci && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Layers className="w-3.5 h-3.5 text-yellow-400" />
              <h4 className="text-xs font-semibold text-slate-300">Fibonacci Retracement</h4>
            </div>
            <div className="space-y-1 text-xs">
              {Object.entries(advanced.fibonacci.levels).map(([level, price]) => (
                <div key={level} className="flex justify-between py-0.5">
                  <span className="text-slate-500">{(parseFloat(level) * 100).toFixed(1)}%</span>
                  <span className="font-mono text-slate-300">{price.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {advanced.volume_profile && (
          <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <BarChart2 className="w-3.5 h-3.5 text-pink-400" />
              <h4 className="text-xs font-semibold text-slate-300">Volume Profile</h4>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">POC</span>
                <span className="text-pink-400 font-mono font-semibold">{advanced.volume_profile.poc.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">VA High</span>
                <span className="text-slate-300 font-mono">{advanced.volume_profile.value_area_high.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">VA Low</span>
                <span className="text-slate-300 font-mono">{advanced.volume_profile.value_area_low.toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
