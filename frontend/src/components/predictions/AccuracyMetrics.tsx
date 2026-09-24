import React from "react";
import { AccuracySummary } from "../../types/api";
import { StatCard } from "../common/StatCard";
import { CheckCircle2, TrendingUp, Target, BarChart2 } from "lucide-react";

interface AccuracyMetricsProps {
  summary: AccuracySummary;
}

export const AccuracyMetrics: React.FC<AccuracyMetricsProps> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="1-Day Directional Acc"
        value={`${(summary.horizon_1d_directional_acc * 100).toFixed(1)}%`}
        subValue="Short-Term Market Shocks"
        icon={TrendingUp}
        badgeText="1D"
        badgeVariant="bullish"
      />
      <StatCard
        title="7-Day Directional Acc"
        value={`${(summary.horizon_7d_directional_acc * 100).toFixed(1)}%`}
        subValue="Multi-Hop Ripple Absorption"
        icon={Target}
        badgeText="7D"
        badgeVariant="bullish"
      />
      <StatCard
        title="30-Day Directional Acc"
        value={`${(summary.horizon_30d_directional_acc * 100).toFixed(1)}%`}
        subValue="Fundamental Equilibrium"
        icon={CheckCircle2}
        badgeText="30D"
        badgeVariant="bullish"
      />
      <StatCard
        title="7-Day Brier Score"
        value={summary.brier_score_7d.toFixed(4)}
        subValue="Probabilistic Calibration (Lower is Better)"
        icon={BarChart2}
        badgeText="Calibrated"
        badgeVariant="default"
      />
    </div>
  );
};
