import React from "react";
import { Link } from "react-router-dom";
import { TrendingUp, TrendingDown, Building2, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

interface ImpactedCompany {
  ticker: string;
  name: string;
  sector: string;
  impactScore: number;
  direction: "BULLISH" | "BEARISH";
  confidence: number;
  primaryDriver: string;
}

const TOP_COMPANIES: ImpactedCompany[] = [
  {
    ticker: "TATAMOTORS.NS",
    name: "Tata Motors Limited",
    sector: "Automotive",
    impactScore: -0.042,
    direction: "BEARISH",
    confidence: 0.88,
    primaryDriver: "Steel tariff surge & input inflation",
  },
  {
    ticker: "TATASTEEL.NS",
    name: "Tata Steel Limited",
    sector: "Steel & Metals",
    impactScore: 0.054,
    direction: "BULLISH",
    confidence: 0.82,
    primaryDriver: "HRC export parity & tariff protection",
  },
  {
    ticker: "RELIANCE.NS",
    name: "Reliance Industries",
    sector: "Energy & Oil",
    impactScore: -0.019,
    direction: "BEARISH",
    confidence: 0.76,
    primaryDriver: "Brent crude supply choke & GRM compression",
  },
  {
    ticker: "TCS.NS",
    name: "Tata Consultancy Services",
    sector: "IT Services",
    impactScore: 0.024,
    direction: "BULLISH",
    confidence: 0.79,
    primaryDriver: "USD/INR real depreciation & macro shift",
  },
];

export const TopImpactedCompanies: React.FC = () => {
  return (
    <div className="rounded-xl border border-border bg-surface-1 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-brand" />
          <h2 className="text-sm font-bold font-ui text-text-primary uppercase tracking-wider">
            Top Shock Propagations
          </h2>
        </div>
        <Link
          to="/company"
          className="text-xs font-mono text-brand hover:underline flex items-center gap-1"
        >
          All Companies <ChevronRight className="w-3 h-3" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TOP_COMPANIES.map((company) => {
          const isBull = company.direction === "BULLISH";
          return (
            <Link
              key={company.ticker}
              to={`/company/${company.ticker}`}
              className="p-4 rounded-lg border border-border bg-surface-base hover:border-brand/40 transition-all duration-150 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="font-mono text-xs font-bold text-text-primary group-hover:text-brand transition-colors">
                      {company.ticker}
                    </div>
                    <div className="text-[11px] text-text-muted">{company.name}</div>
                  </div>

                  <div
                    className={cn(
                      "px-2 py-0.5 rounded text-xs font-mono font-bold flex items-center gap-1 border",
                      isBull
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                        : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
                    )}
                  >
                    {isBull ? (
                      <TrendingUp className="w-3.5 h-3.5" />
                    ) : (
                      <TrendingDown className="w-3.5 h-3.5" />
                    )}
                    {(company.impactScore * 100).toFixed(2)}%
                  </div>
                </div>

                <p className="text-[11px] text-text-secondary line-clamp-1 mb-2">
                  {company.primaryDriver}
                </p>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-text-muted pt-2 border-t border-border/40">
                <span>Sector: {company.sector}</span>
                <span>Confidence: {(company.confidence * 100).toFixed(0)}%</span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};
