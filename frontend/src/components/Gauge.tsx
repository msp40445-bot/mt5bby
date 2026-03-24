import { useEffect, useRef } from 'react';

interface GaugeProps {
  title: string;
  sell: number;
  neutral: number;
  buy: number;
  signal: string;
  size?: number;
}

export function Gauge({ title, sell, neutral, buy, signal, size = 160 }: GaugeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const total = sell + neutral + buy;
  const ratio = total > 0 ? (buy - sell) / total : 0;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = (size * 0.7) * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size * 0.7}px`;

    ctx.clearRect(0, 0, size, size * 0.7);

    const cx = size / 2;
    const cy = size * 0.55;
    const radius = size * 0.38;
    const lineWidth = size * 0.06;

    // Draw background arc
    const startAngle = Math.PI;

    // Draw colored segments
    const segments = [
      { color: '#ef4444', start: 0, end: 0.2 },
      { color: '#f97316', start: 0.2, end: 0.4 },
      { color: '#9ca3af', start: 0.4, end: 0.6 },
      { color: '#84cc16', start: 0.6, end: 0.8 },
      { color: '#22c55e', start: 0.8, end: 1.0 },
    ];

    for (const seg of segments) {
      ctx.beginPath();
      ctx.arc(
        cx, cy, radius,
        startAngle + seg.start * Math.PI,
        startAngle + seg.end * Math.PI,
        false
      );
      ctx.strokeStyle = seg.color;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      ctx.stroke();
    }

    // Draw needle
    const needleAngle = startAngle + ((ratio + 1) / 2) * Math.PI;
    const needleLen = radius * 0.7;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(needleAngle);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(needleLen, 0);
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Needle center dot
    ctx.beginPath();
    ctx.arc(0, 0, 4, 0, 2 * Math.PI);
    ctx.fillStyle = '#e2e8f0';
    ctx.fill();
    ctx.restore();

    // Labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = `${Math.max(9, size * 0.065)}px system-ui, sans-serif`;
    ctx.textAlign = 'center';

    const labelRadius = radius + lineWidth + 8;
    const labels = ['Strong sell', 'Sell', 'Neutral', 'Buy', 'Strong buy'];
    const positions = [0.1, 0.3, 0.5, 0.7, 0.9];

    for (let i = 0; i < labels.length; i++) {
      const angle = startAngle + positions[i] * Math.PI;
      const lx = cx + Math.cos(angle) * labelRadius;
      const ly = cy + Math.sin(angle) * labelRadius;
      ctx.fillText(labels[i], lx, ly);
    }
  }, [sell, neutral, buy, signal, ratio, size]);

  const signalColor =
    signal === 'Strong Buy' ? '#22c55e' :
    signal === 'Buy' ? '#84cc16' :
    signal === 'Strong Sell' ? '#ef4444' :
    signal === 'Sell' ? '#f97316' :
    '#9ca3af';

  return (
    <div className="flex flex-col items-center">
      <h3 className="text-sm font-medium text-slate-400 mb-1">{title}</h3>
      <canvas ref={canvasRef} />
      <div className="text-lg font-bold mt-1" style={{ color: signalColor }}>
        {signal}
      </div>
      <div className="flex gap-4 text-xs text-slate-500 mt-1">
        <span>Sell<br /><span className="text-slate-300 font-semibold">{sell}</span></span>
        <span>Neutral<br /><span className="text-slate-300 font-semibold">{neutral}</span></span>
        <span>Buy<br /><span className="text-slate-300 font-semibold">{buy}</span></span>
      </div>
    </div>
  );
}
