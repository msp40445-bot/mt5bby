import { useEffect, useRef, useState, useCallback } from 'react';

export interface PriceData {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  high: number;
  low: number;
  open: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: number;
  source?: string;
}

export interface IndicatorValue {
  name: string;
  value: number | null;
  action: string;
}

export interface PivotLevel {
  name: string;
  classic: number | null;
  fibonacci: number | null;
  camarilla: number | null;
  woodie: number | null;
  dm: number | null;
}

export interface GaugeSummary {
  sell: number;
  neutral: number;
  buy: number;
  signal: string;
}

export interface TimeframeSignal {
  timeframe: string;
  oscillators: GaugeSummary;
  moving_averages: GaugeSummary;
  summary: GaugeSummary;
  strength: number;
  label: string;
}

export interface MasterSignal {
  action: string;
  strength: number;
  confidence: number;
  color: string;
  total_buy: number;
  total_sell: number;
  total_neutral: number;
}

export interface AIDecision {
  direction: string;
  entry: number;
  stop_loss: number;
  take_profit: number;
  risk_reward: number;
  sim_profit: number;
  sim_loss: number;
  confidence: number;
  quality: string;
  quality_color: string;
  strength: number;
  reasons: string[];
  action_advice: string;
  trailing_stop: number;
  break_even_zone: boolean;
  momentum_divergence: boolean;
  bb_position: string;
  bb_squeeze: boolean;
  commentary: string;
  timestamp: number;
  ai_powered: boolean;
}

export interface BollingerBands {
  upper: number;
  middle: number;
  lower: number;
  width: number;
  percent_b: number;
}

export interface MarketStructure {
  trend: string;
  higher_highs: number;
  lower_highs: number;
  higher_lows: number;
  lower_lows: number;
  strength: number;
}

export interface Pattern {
  name: string;
  bias: string;
  strength: number;
}

export interface TrendStrength {
  strength: number;
  direction: string;
  slope: number;
  ma_alignment: string;
  description: string;
}

export interface FibonacciData {
  swing_high: number;
  swing_low: number;
  levels: Record<string, number>;
}

export interface VolumeProfile {
  poc: number;
  value_area_high: number;
  value_area_low: number;
}

export interface AdvancedAnalysis {
  bollinger_bands?: BollingerBands;
  atr?: { value: number; period: number };
  obv?: { value: number; trend: string };
  vwap?: { value: number; deviation: number; deviation_pct: number; signal: string };
  fibonacci?: FibonacciData;
  market_structure?: MarketStructure;
  patterns?: Pattern[];
  volume_profile?: VolumeProfile;
  trend_strength?: TrendStrength;
}

export interface AnalysisData {
  price: PriceData;
  oscillators: IndicatorValue[];
  moving_averages: IndicatorValue[];
  pivots: PivotLevel[];
  oscillator_summary: GaugeSummary;
  ma_summary: GaugeSummary;
  overall_summary: GaugeSummary;
  timeframe_signals: TimeframeSignal[];
  master_signal: MasterSignal;
  advanced?: AdvancedAnalysis;
  ai_decision?: AIDecision;
  feed_source?: string;
  timestamp: number;
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export function useWebSocket() {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [connected, setConnected] = useState(false);
  const [latency, setLatency] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const lastUpdateRef = useRef<number>(Date.now());
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const now = Date.now();
      setLatency(now - lastUpdateRef.current);
      lastUpdateRef.current = now;

      const msg = JSON.parse(event.data);
      if (msg.type === 'full_analysis' || msg.type === 'update') {
        setData(msg.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectTimeoutRef.current = setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { data, connected, latency };
}
