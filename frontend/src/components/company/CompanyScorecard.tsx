import React from "react";
import { CompanyAnalysisResponse } from "../../types/api";
import { TrendingUp, TrendingDown, ShieldAlert, Clock, Award } from "lucide-react";
import { cn, getRiskColor } from "../../lib/utils";

interface CompanyScorecardProps {
  analysis: CompanyAnalysisResponse;
}

export const CompanyScorecard: React.FC<CompanyScorecardProps> = ({ analysis }) => {
  const { prediction } = analysis;
  const isBull = prediction.direction === "BULLISH";
  const riskBadge = getRiskColor(prediction.risk_label);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Direction & Impact Score */}
      <div className="p-5 rounded-xl border border-border bg-surface-1 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs font-mono text-text-muted">
          <span>PROJECTED IMPACT</span>
          <div
            className={cn(
              "px-2 py-0.5 rounded text-[10px] font-bold border",
              isBull
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
            )}
          >
            {prediction.direction}
          </div>
        </div>

        <div className="my-2 flex items-baseline gap-2">
          {isBull ? (
            <TrendingUp className="w-6 h-6 text-emerald-500" />
          ) : (
            <TrendingDown className="w-6 h-6 text-rose-500" />
          )}
          <span
            className={cn(
              "font-mono text-3xl font-bold tracking-tight",
              isBull
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-rose-600 dark:text-rose-400"
            )}
          >
            {(prediction.impact_score * 100).toFixed(2)}%
          </span>
        </div>

        <div className="text-[11px] font-mono text-text-muted">
          Multi-Factor XGBoost Model
        </div>
      </div>

      {/* Model Confidence */}
      <div className="p-5 rounded-xl border border-border bg-surface-1 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs font-mono text-text-muted">
          <span>MODEL CONFIDENCE</span>
          <Award className="w-4 h-4 text-brand" />
        </div>

        <div className="my-2 font-mono text-3xl font-bold text-text-primary">
          {(prediction.confidence * 100).toFixed(1)}%
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-surface-2 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-brand h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${prediction.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Risk Level */}
      <div className="p-5 rounded-xl border border-border bg-surface-1 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs font-mono text-text-muted">
          <span>RISK PROFILE</span>
          <ShieldAlert className="w-4 h-4 text-amber-500" />
        </div>

        <div className="my-2">
          <span
            className={cn(
              "inline-block px-3 py-1 rounded-md text-base font-mono font-bold border",
              riskBadge.bg,
              riskBadge.text,
              riskBadge.border
            )}
          >
            {prediction.risk_label} RISK
          </span>
        </div>

        <div className="text-[11px] font-mono text-text-muted">
          Based on 30D volatility & beta
        </div>
      </div>

      {/* Forecast Horizon */}
      <div className="p-5 rounded-xl border border-border bg-surface-1 shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs font-mono text-text-muted">
          <span>FORECAST HORIZON</span>
          <Clock className="w-4 h-4 text-text-secondary" />
        </div>

        <div className="my-2 font-mono text-3xl font-bold text-text-primary">
          {prediction.horizon_days} Days
        </div>

        <div className="text-[11px] font-mono text-text-muted">
          Purged & Embargoed Split Validated
        </div>
      </div>
    </div>
  );
};
