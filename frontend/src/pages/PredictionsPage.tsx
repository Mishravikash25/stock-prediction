import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { AccuracyMetrics } from "../components/predictions/AccuracyMetrics";
import { BacktestModal } from "../components/predictions/BacktestModal";
import { LoadingState, ErrorState } from "../components/common/LoadingState";
import { formatDate, formatCurrencyINR, formatPercent, cn } from "../lib/utils";
import { PredictionItem } from "../types/api";
import {
  History,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  ArrowRight,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

export const PredictionsPage: React.FC = () => {
  const [ticker, setTicker] = useState<string>("");
  const [horizon, setHorizon] = useState<number | undefined>(undefined);
  const [isCorrectFilter, setIsCorrectFilter] = useState<boolean | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [isBacktestOpen, setIsBacktestOpen] = useState(false);

  const limit = 10;
  const offset = (page - 1) * limit;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["predictions", ticker, horizon, isCorrectFilter, page],
    queryFn: () =>
      api.getPredictions({
        ticker: ticker.trim() || undefined,
        horizon_days: horizon,
        is_correct: isCorrectFilter,
        limit,
        offset,
      }),
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary font-ui flex items-center gap-2">
            <History className="w-6 h-6 text-brand" />
            Prediction Audit Ledger & Backtest History
          </h1>
          <p className="text-xs font-mono text-text-muted mt-1">
            Immutable Point-In-Time Evaluation: Forecast vs Horizon Realized Returns
          </p>
        </div>

        <button
          onClick={() => setIsBacktestOpen(true)}
          className="px-4 py-2 rounded-lg bg-brand hover:bg-brand-hover text-white text-xs font-mono font-bold transition-colors flex items-center gap-2 self-start sm:self-auto shadow-sm"
        >
          <Play className="w-3.5 h-3.5" />
          Run Walk-Forward Backtest
        </button>
      </div>

      {/* Accuracy Summary Stat Cards */}
      {data?.accuracy_summary && <AccuracyMetrics summary={data.accuracy_summary} />}

      {/* Filter Controls */}
      <div className="p-4 rounded-xl border border-border bg-surface-1 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Ticker Search */}
          <input
            type="text"
            placeholder="Filter by Ticker..."
            value={ticker}
            onChange={(e) => {
              setTicker(e.target.value);
              setPage(1);
            }}
            className="w-44 px-3 py-1.5 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-1 focus:ring-brand"
          />

          {/* Horizon Filter */}
          <select
            value={horizon !== undefined ? horizon : ""}
            onChange={(e) => {
              setHorizon(e.target.value ? parseInt(e.target.value) : undefined);
              setPage(1);
            }}
            className="px-3 py-1.5 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
          >
            <option value="">All Horizons</option>
            <option value="1">1 Day</option>
            <option value="7">7 Days</option>
            <option value="30">30 Days</option>
          </select>

          {/* Evaluation Status Filter */}
          <select
            value={isCorrectFilter === undefined ? "" : isCorrectFilter ? "true" : "false"}
            onChange={(e) => {
              setIsCorrectFilter(
                e.target.value === "" ? undefined : e.target.value === "true"
              );
              setPage(1);
            }}
            className="px-3 py-1.5 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
          >
            <option value="">All Outcomes</option>
            <option value="true">Directionally Correct Only</option>
            <option value="false">Directionally Incorrect Only</option>
          </select>
        </div>

        <div className="text-xs font-mono text-text-muted">
          Total Recorded: <strong>{data?.total || 0} Predictions</strong>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="rounded-xl border border-border bg-surface-1 overflow-hidden shadow-sm">
        {isLoading && <LoadingState message="Loading point-in-time prediction history..." />}
        {isError && (
          <ErrorState
            message={(error as Error).message || "Failed to load predictions"}
            onRetry={() => refetch()}
          />
        )}

        {data && data.predictions.length === 0 && (
          <div className="p-12 text-center text-xs font-mono text-text-muted">
            No predictions found matching the specified filters.
          </div>
        )}

        {data && data.predictions.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-border bg-surface-base text-[11px] text-text-muted uppercase">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Asset</th>
                  <th className="py-3 px-4 text-center">Horizon</th>
                  <th className="py-3 px-4 text-center">Forecast</th>
                  <th className="py-3 px-4 text-right">Confidence</th>
                  <th className="py-3 px-4 text-right">Entry Price</th>
                  <th className="py-3 px-4 text-right">Horizon Price</th>
                  <th className="py-3 px-4 text-right">Realized Return</th>
                  <th className="py-3 px-4 text-center">Audit Result</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.predictions.map((p: PredictionItem) => {
                  const isBull = p.predicted_direction === "BULLISH";
                  return (
                    <tr key={p.id} className="hover:bg-surface-base/50 transition-colors">
                      <td className="py-3 px-4 text-text-muted whitespace-nowrap">
                        {formatDate(p.created_at)}
                      </td>
                      <td className="py-3 px-4 font-bold text-text-primary">
                        {p.ticker}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded bg-surface-2 border border-border text-[10px] font-bold">
                          {p.horizon_days}D
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center whitespace-nowrap">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold border text-[10px]",
                            isBull
                              ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
                          )}
                        >
                          {isBull ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {p.predicted_direction} ({(p.predicted_score * 100).toFixed(1)}%)
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-text-secondary">
                        {(p.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="py-3 px-4 text-right">
                        {formatCurrencyINR(p.actual_price_at_prediction)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {p.actual_price_at_horizon !== undefined && p.actual_price_at_horizon !== null
                          ? formatCurrencyINR(p.actual_price_at_horizon)
                          : "Pending"}
                      </td>
                      <td className="py-3 px-4 text-right font-bold">
                        {p.actual_return_pct !== undefined && p.actual_return_pct !== null ? (
                          <span
                            className={
                              p.actual_return_pct >= 0
                                ? "text-emerald-600 dark:text-emerald-400"
                                : "text-rose-600 dark:text-rose-400"
                            }
                          >
                            {formatPercent(p.actual_return_pct)}
                          </span>
                        ) : (
                          <span className="text-text-muted">In Progress</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {p.is_correct === true && (
                          <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold text-[11px]">
                            <CheckCircle className="w-3.5 h-3.5" /> Hit
                          </span>
                        )}
                        {p.is_correct === false && (
                          <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400 font-bold text-[11px]">
                            <XCircle className="w-3.5 h-3.5" /> Miss
                          </span>
                        )}
                        {p.is_correct === undefined && (
                          <span className="inline-flex items-center gap-1 text-text-muted text-[11px]">
                            <Clock className="w-3.5 h-3.5" /> Open
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Link
                          to={`/company/${p.ticker}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-brand/10 hover:bg-brand/20 border border-brand/30 text-brand text-[11px] font-bold transition-colors"
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
        )}
      </div>

      {/* Backtest Modal */}
      <BacktestModal
        isOpen={isBacktestOpen}
        onClose={() => setIsBacktestOpen(false)}
      />
    </div>
  );
};
