interface PivotLevel {
  name: string;
  classic: number | null;
  fibonacci: number | null;
  camarilla: number | null;
  woodie: number | null;
  dm: number | null;
}

interface PivotTableProps {
  pivots: PivotLevel[];
}

function formatVal(val: number | null): string {
  if (val === null || val === undefined) return '—';
  return val.toFixed(2);
}

export function PivotTable({ pivots }: PivotTableProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-slate-700/50">
        <h3 className="text-sm font-semibold text-slate-200">Pivots &rsaquo;</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-500 text-xs border-b border-slate-700/30">
              <th className="text-left px-3 py-2 font-medium">Pivot</th>
              <th className="text-right px-3 py-2 font-medium">Classic</th>
              <th className="text-right px-3 py-2 font-medium">Fibonacci</th>
              <th className="text-right px-3 py-2 font-medium">Camarilla</th>
              <th className="text-right px-3 py-2 font-medium">Woodie</th>
              <th className="text-right px-3 py-2 font-medium">DM</th>
            </tr>
          </thead>
          <tbody>
            {pivots.map((p) => (
              <tr key={p.name} className="border-b border-slate-700/20 hover:bg-slate-700/20 transition-colors">
                <td className="px-3 py-1.5 text-slate-300 font-medium">{p.name}</td>
                <td className="px-3 py-1.5 text-right text-slate-200 font-mono text-xs">{formatVal(p.classic)}</td>
                <td className="px-3 py-1.5 text-right text-slate-200 font-mono text-xs">{formatVal(p.fibonacci)}</td>
                <td className="px-3 py-1.5 text-right text-slate-200 font-mono text-xs">{formatVal(p.camarilla)}</td>
                <td className="px-3 py-1.5 text-right text-slate-200 font-mono text-xs">{formatVal(p.woodie)}</td>
                <td className="px-3 py-1.5 text-right text-slate-200 font-mono text-xs">{formatVal(p.dm)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
