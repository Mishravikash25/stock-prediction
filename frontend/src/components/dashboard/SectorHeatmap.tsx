import React from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, ArrowDownRight, Layers } from "lucide-react";
import { cn } from "../../lib/utils";

interface SectorStat {
  id: string;
  name: string;
  shockMagnitude: number; // e.g. -0.042
  topShockArchetype: string;
  activeCompanies: number;
  leadingCompany: string;
  sentimentScore: number;
}

const SECTOR_DATA: SectorStat[] = [
  {
    id: "Automotive",
    name: "Automotive & EVs",
    shockMagnitude: -0.038,
    topShockArchetype: "COMMODITY_SHOCK",
    activeCompanies: 4,
    leadingCompany: "TATAMOTORS.NS",
    sentimentScore: -0.45,
  },
  {
    id: "Steel_Metals",
    name: "Steel & Metals",
    shockMagnitude: 0.052,
    topShockArchetype: "COMMODITY_SHOCK",
    activeCompanies: 3,
    leadingCompany: "TATASTEEL.NS",
    sentimentScore: 0.62,
  },
  {
    id: "Energy_Oil",
    name: "Energy & Petrochemicals",
    shockMagnitude: -0.021,
    topShockArchetype: "SUPPLY_DISRUPTION",
    activeCompanies: 3,
    leadingCompany: "RELIANCE.NS",
    sentimentScore: -0.15,
  },
  {
    id: "IT_Services",
    name: "IT & Technology Services",
    shockMagnitude: 0.018,
    topShockArchetype: "MACRO_RATE_SHIFT",
    activeCompanies: 3,
    leadingCompany: "TCS.NS",
    sentimentScore: 0.28,
  },
];

export const SectorHeatmap: React.FC = () => {
  return (
    <div className="rounded-xl border border-border bg-surface-1 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-brand" />
          <h2 className="text-sm font-bold font-ui text-text-primary uppercase tracking-wider">
            Sector Ripple Impact Matrix
          </h2>
        </div>
        <span className="text-xs font-mono text-text-muted">4 Core Sectors (GRCh38 / NSE)</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {SECTOR_DATA.map((sector) => {
          const isBullish = sector.shockMagnitude >= 0;
          return (
            <Link
              key={sector.id}
              to={`/ripple?sector=${sector.id}`}
              className={cn(
                "p-4 rounded-lg border transition-all duration-200 group flex flex-col justify-between relative overflow-hidden",
                isBullish
                  ? "bg-emerald-500/5 hover:bg-emerald-500/10 border-emerald-500/20 hover:border-emerald-500/40"
                  : "bg-rose-500/5 hover:bg-rose-500/10 border-rose-500/20 hover:border-rose-500/40"
              )}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-xs font-bold text-text-primary group-hover:text-brand transition-colors">
                    {sector.name}
                  </span>
                  <div
                    className={cn(
                      "flex items-center text-xs font-mono font-bold",
                      isBullish ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                    )}
                  >
                    {isBullish ? (
                      <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                    ) : (
                      <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
                    )}
                    {(sector.shockMagnitude * 100).toFixed(2)}%
                  </div>
                </div>

                <div className="text-[11px] font-mono text-text-muted mb-3">
                  Driver: <span className="text-text-secondary">{sector.topShockArchetype}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-border/50 flex items-center justify-between text-[11px] font-mono">
                <span className="text-text-muted">Top Bellwether:</span>
                <span className="font-semibold text-text-primary group-hover:underline">
                  {sector.leadingCompany}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};
