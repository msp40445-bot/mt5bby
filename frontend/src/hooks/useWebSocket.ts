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
