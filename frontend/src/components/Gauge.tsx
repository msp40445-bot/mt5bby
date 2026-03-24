import { useEffect, useRef } from 'react';

interface GaugeProps {
  title: string;
  sell: number;
  neutral: number;
  buy: number;
  signal: string;
  size?: number;
}

export function Gauge({ title, sell, neutral, buy, signal, size = 180 }: GaugeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const total = sell + neutral + buy;
  const ratio = total > 0 ? (buy - sell) / total : 0;
  const buyPct = total > 0 ? Math.round((buy / total) * 100) : 0;
  const sellPct = total > 0 ? Math.round((sell / total) * 100) : 0;
  const neutralPct = total > 0 ? Math.round((neutral / total) * 100) : 0;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = (size * 0.75) * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size * 0.75}px`;

    ctx.clearRect(0, 0, size, size * 0.75);

    const cx = size / 2;
    const cy = size * 0.58;
    const radius = size * 0.38;
    const lineWidth = size * 0.07;

    const startAngle = Math.PI;

    // Draw background track
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, 2 * Math.PI, false);
    ctx.strokeStyle = 'rgba(100, 116, 139, 0.15)';
    ctx.lineWidth = lineWidth + 4;
    ctx.stroke();

    // Gradient segments (7 segments for finer granularity)
    const segments = [
      { color: '#dc2626', start: 0, end: 0.143 },      // Strong Sell
      { color: '#ef4444', start: 0.143, end: 0.286 },   // Sell
      { color: '#f97316', start: 0.286, end: 0.429 },   // Weak Sell
      { color: '#9ca3af', start: 0.429, end: 0.571 },   // Neutral
      { color: '#84cc16', start: 0.571, end: 0.714 },   // Weak Buy
      { color: '#22c55e', start: 0.714, end: 0.857 },   // Buy
      { color: '#16a34a', start: 0.857, end: 1.0 },     // Strong Buy
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
      ctx.lineCap = 'butt';
      ctx.stroke();
    }

    // Tick marks
    const tickCount = 21;
    for (let i = 0; i <= tickCount; i++) {
      const pct = i / tickCount;
      const angle = startAngle + pct * Math.PI;
      const isMajor = i % 5 === 0;
      const innerR = radius - lineWidth / 2 - (isMajor ? 8 : 4);
      const outerR = radius - lineWidth / 2 - 1;

      ctx.beginPath();
      ctx.moveTo(
        cx + Math.cos(angle) * innerR,
        cy + Math.sin(angle) * innerR
      );
      ctx.lineTo(
        cx + Math.cos(angle) * outerR,
        cy + Math.sin(angle) * outerR
      );
      ctx.strokeStyle = isMajor ? 'rgba(226, 232, 240, 0.6)' : 'rgba(148, 163, 184, 0.3)';
      ctx.lineWidth = isMajor ? 1.5 : 0.8;
      ctx.stroke();
    }

    // Percentage labels on major ticks
    const pctLabels = ['-100', '-50', '0', '+50', '+100'];
    const pctPositions = [0, 0.25, 0.5, 0.75, 1.0];
    ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
    ctx.font = `${Math.max(7, size * 0.042)}px system-ui, sans-serif`;
    ctx.textAlign = 'center';
    const pctLabelRadius = radius - lineWidth / 2 - 14;

    for (let i = 0; i < pctLabels.length; i++) {
      const angle = startAngle + pctPositions[i] * Math.PI;
      const lx = cx + Math.cos(angle) * pctLabelRadius;
      const ly = cy + Math.sin(angle) * pctLabelRadius;
      ctx.fillText(pctLabels[i], lx, ly);
    }

    // Draw needle with glow
    const needleAngle = startAngle + ((ratio + 1) / 2) * Math.PI;
    const needleLen = radius * 0.75;

    // Needle glow
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(needleAngle);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(needleLen, 0);
    ctx.strokeStyle = 'rgba(226, 232, 240, 0.3)';
    ctx.lineWidth = 6;
    ctx.lineCap = 'round';
    ctx.stroke();
    ctx.restore();

    // Needle
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(needleAngle);
    ctx.beginPath();
    ctx.moveTo(-4, 0);
    ctx.lineTo(needleLen - 2, -1.5);
    ctx.lineTo(needleLen, 0);
    ctx.lineTo(needleLen - 2, 1.5);
    ctx.closePath();
    ctx.fillStyle = '#e2e8f0';
    ctx.fill();
    ctx.restore();

    // Needle center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#e2e8f0';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx, cy, 2.5, 0, 2 * Math.PI);
    ctx.fillStyle = '#1e293b';
    ctx.fill();

    // Outer labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = `bold ${Math.max(8, size * 0.055)}px system-ui, sans-serif`;
    ctx.textAlign = 'center';

    const labelRadius = radius + lineWidth / 2 + 12;
    const labels = ['Strong\nSell', 'Sell', 'Neutral', 'Buy', 'Strong\nBuy'];
    const positions = [0.07, 0.28, 0.5, 0.72, 0.93];

    for (let i = 0; i < labels.length; i++) {
      const angle = startAngle + positions[i] * Math.PI;
      const lx = cx + Math.cos(angle) * labelRadius;
      const ly = cy + Math.sin(angle) * labelRadius;
      const lines = labels[i].split('\n');
      for (let j = 0; j < lines.length; j++) {
        ctx.fillText(lines[j], lx, ly + j * 10);
      }
    }
  }, [sell, neutral, buy, signal, ratio, size]);

  const signalColor =
    signal === 'Strong Buy' ? '#16a34a' :
    signal === 'Buy' ? '#22c55e' :
    signal === 'Strong Sell' ? '#dc2626' :
    signal === 'Sell' ? '#ef4444' :
    '#9ca3af';

  // Strength indicator
  const strength = Math.abs(ratio);
  const strengthLabel = strength > 0.7 ? 'STRONG' : strength > 0.3 ? 'MODERATE' : 'WEAK';

  return (
    <div className="flex flex-col items-center">
      <h3 className="text-sm font-semibold text-slate-300 mb-1">{title}</h3>
      <canvas ref={canvasRef} />
      <div className="text-lg font-black mt-0.5" style={{ color: signalColor }}>
        {signal}
      </div>
      <div className="text-[10px] font-medium text-slate-500 mb-1.5">
        {strengthLabel} ({(ratio * 100).toFixed(0)}%)
      </div>
      <div className="flex gap-3 text-xs text-slate-500">
        <div className="text-center">
          <div className="text-red-400 font-bold text-sm">{sell}</div>
          <div>Sell</div>
          <div className="text-[10px] text-slate-600">{sellPct}%</div>
        </div>
        <div className="text-center">
          <div className="text-slate-400 font-bold text-sm">{neutral}</div>
          <div>Neutral</div>
          <div className="text-[10px] text-slate-600">{neutralPct}%</div>
        </div>
        <div className="text-center">
          <div className="text-green-400 font-bold text-sm">{buy}</div>
          <div>Buy</div>
          <div className="text-[10px] text-slate-600">{buyPct}%</div>
        </div>
      </div>
    </div>
  );
}
