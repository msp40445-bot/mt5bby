interface Indicator {
  name: string;
  value: number | null;
  action: string;
}

interface IndicatorTableProps {
  title: string;
  indicators: Indicator[];
}

function ActionBadge({ action }: { action: string }) {
  const colors: Record<string, string> = {
    Buy: 'text-green-400',
    Sell: 'text-red-400',
    Neutral: 'text-slate-400',
  };

  return (
    <span className={`font-medium ${colors[action] || 'text-slate-400'}`}>
      {action}
    </span>
  );
}

export function IndicatorTable({ title, indicators }: IndicatorTableProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-slate-700/50 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">{title} &rsaquo;</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-500 text-xs border-b border-slate-700/30">
              <th className="text-left px-4 py-2 font-medium">Name</th>
              <th className="text-right px-4 py-2 font-medium">Value</th>
              <th className="text-right px-4 py-2 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {indicators.map((ind) => (
              <tr key={ind.name} className="border-b border-slate-700/20 hover:bg-slate-700/20 transition-colors">
                <td className="px-4 py-1.5 text-slate-300">{ind.name}</td>
                <td className="px-4 py-1.5 text-right text-slate-200 font-mono text-xs">
                  {ind.value !== null ? ind.value.toFixed(2) : '—'}
                </td>
                <td className="px-4 py-1.5 text-right">
                  <ActionBadge action={ind.action} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
