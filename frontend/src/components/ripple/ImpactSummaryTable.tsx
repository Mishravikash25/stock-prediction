import React from "react";
import { Link } from "react-router-dom";
import { ImpactSummaryItem } from "../../types/api";
import { ArrowRight, TrendingUp, TrendingDown, Layers } from "lucide-react";
import { cn } from "../../lib/utils";

interface ImpactSummaryTableProps {
  items: ImpactSummaryItem[];
  selectedTicker?: string | null;
  onSelectTicker?: (ticker: string) => void;
}

export const ImpactSummaryTable: React.FC<ImpactSummaryTableProps> = ({
  items,
  selectedTicker,
  onSelectTicker,
}) => {
  if (!items || items.length === 0) {
    return (
      <div className="p-8 text-center border border-border rounded-xl bg-surface-1 text-xs font-mono text-text-muted">
        No downstream asset impacts detected within the current hop and strength threshold.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-surface-1 overflow-hidden shadow-sm">
      <div className="p-4 border-b border-border bg-surface-base flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-brand" />
          <h3 className="text-xs font-bold font-mono text-text-primary uppercase tracking-wider">
            Downstream Impact Summary ({items.length} Assets)
          </h3>
        </div>
        <span className="text-[11px] font-mono text-text-muted">
          Ranked by Abs(Ripple Score)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead>
            <tr className="border-b border-border bg-surface-base/50 text-[11px] text-text-muted uppercase">
              <th className="py-2.5 px-4">Ticker</th>
              <th className="py-2.5 px-4 text-right">Net Shock Score</th>
              <th className="py-2.5 px-4 text-center">Hop Distance</th>
              <th className="py-2.5 px-4">Propagation Pathway</th>
              <th className="py-2.5 px-4 text-center">Scorecard</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.map((item) => {
              const isBull = item.net_ripple_score >= 0;
              const isSelected = selectedTicker === item.ticker;

              return (
                <tr
                  key={item.ticker}
                  onClick={() => onSelectTicker && onSelectTicker(item.ticker)}
                  className={cn(
                    "hover:bg-surface-base/50 transition-colors cursor-pointer",
                    isSelected && "bg-brand/5 border-l-2 border-l-brand"
                  )}
                >
                  <td className="py-3 px-4 font-bold text-text-primary">
                    {item.ticker}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 font-bold",
                        isBull
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-rose-600 dark:text-rose-400"
                      )}
                    >
                      {isBull ? (
                        <TrendingUp className="w-3.5 h-3.5" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5" />
                      )}
                      {(item.net_ripple_score * 100).toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="px-2 py-0.5 rounded-full bg-surface-2 border border-border text-[10px] font-bold">
                      {item.hop_distance} {item.hop_distance === 1 ? "Hop" : "Hops"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-text-secondary text-[11px] max-w-xs truncate">
                    {item.path_description}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <Link
                      to={`/company/${item.ticker}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-brand/10 hover:bg-brand/20 border border-brand/30 text-brand text-[11px] font-bold transition-colors"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Deep Dive
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
