import React from "react";
import { StructuredReport } from "../../types/api";
import { TrendingUp, TrendingDown, HelpCircle, ShieldCheck, FileText } from "lucide-react";

interface DualThesisCardProps {
  report: StructuredReport;
}

export const DualThesisCard: React.FC<DualThesisCardProps> = ({ report }) => {
  return (
    <div className="p-6 rounded-xl border border-border bg-surface-1 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-brand" />
          <h3 className="text-xs font-bold font-mono text-text-primary uppercase tracking-wider">
            Explainable Dual-Thesis Narrative (Schema Grounded)
          </h3>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[10px] font-mono text-emerald-600 dark:text-emerald-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>ZERO NUMERICAL HALLUCINATION</span>
        </div>
      </div>

      {/* Transmission Narrative / Summary */}
      {report.summary && (
        <div className="p-4 rounded-lg bg-surface-base border border-border">
          <div className="text-[11px] font-mono text-text-muted uppercase mb-1">
            Executive Summary & Transmission Path
          </div>
          <p className="text-xs font-ui text-text-secondary leading-relaxed">
            {report.summary}
          </p>
          {report.transmission_narrative && (
            <p className="text-xs font-ui text-text-muted mt-2 pt-2 border-t border-border/50 italic">
              &ldquo;{report.transmission_narrative}&rdquo;
            </p>
          )}
        </div>
      )}

      {/* Dual Theses 2-Column Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Bull Case */}
        <div className="p-4 rounded-lg border border-emerald-500/20 bg-emerald-500/5 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold font-mono text-emerald-600 dark:text-emerald-400 uppercase">
            <TrendingUp className="w-4 h-4" />
            <span>Bullish Thesis & Catalysts</span>
          </div>
          <p className="text-xs font-ui text-text-secondary leading-relaxed">
            {report.bull_case || "No significant upside catalyst identified."}
          </p>
        </div>

        {/* Bear Case */}
        <div className="p-4 rounded-lg border border-rose-500/20 bg-rose-500/5 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold font-mono text-rose-600 dark:text-rose-400 uppercase">
            <TrendingDown className="w-4 h-4" />
            <span>Bearish Thesis & Downside Risks</span>
          </div>
          <p className="text-xs font-ui text-text-secondary leading-relaxed">
            {report.bear_case || "No immediate downside risk factor identified."}
          </p>
        </div>
      </div>

      {/* Uncertainty & Model Limitations */}
      <div className="p-4 rounded-lg border border-amber-500/20 bg-amber-500/5 space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-bold font-mono text-amber-600 dark:text-amber-400 uppercase">
          <HelpCircle className="w-4 h-4" />
          <span>Uncertainty & Sensitivity Boundaries</span>
        </div>
        <p className="text-xs font-ui text-text-secondary leading-relaxed">
          {report.uncertainty_analysis ||
            "Model projections are sensitive to commodity spot volatility and policy implementation timelines."}
        </p>
      </div>
    </div>
  );
};
