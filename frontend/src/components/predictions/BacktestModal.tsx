import React, { useState } from "react";
import { X, Play, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "../../lib/api";
import { BacktestRunRequest, BacktestJobResponse } from "../../types/api";

interface BacktestModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BacktestModal: React.FC<BacktestModalProps> = ({ isOpen, onClose }) => {
  const [trainStart, setTrainStart] = useState("2021-01-01");
  const [trainEnd, setTrainEnd] = useState("2023-12-31");
  const [valStart, setValStart] = useState("2024-01-01");
  const [valEnd, setValEnd] = useState("2024-06-30");
  const [testStart, setTestStart] = useState("2024-07-01");
  const [testEnd, setTestEnd] = useState("2024-12-31");
  const [embargoDays, setEmbargoDays] = useState(14);
  const [modelType, setModelType] = useState("xgboost");

  const [isLoading, setIsLoading] = useState(false);
  const [jobResponse, setJobResponse] = useState<BacktestJobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setJobResponse(null);

    const payload: BacktestRunRequest = {
      train_start_date: trainStart,
      train_end_date: trainEnd,
      val_start_date: valStart,
      val_end_date: valEnd,
      test_start_date: testStart,
      test_end_date: testEnd,
      embargo_window_days: embargoDays,
      model_type: modelType,
    };

    try {
      const res = await api.triggerBacktest(payload);
      setJobResponse(res);
    } catch (err) {
      setError((err as Error).message || "Failed to trigger backtest");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-xl rounded-xl border border-border bg-surface-1 shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-border flex items-center justify-between bg-surface-base">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand/10 border border-brand/30 flex items-center justify-center text-brand">
              <Play className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary">
                Run Purged & Embargoed Walk-Forward Backtest
              </h3>
              <p className="text-[11px] font-mono text-text-muted">
                Zero Lookahead Guarantee: Celery Distributed Worker Queue
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text-primary transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  TRAIN START
                </label>
                <input
                  type="date"
                  value={trainStart}
                  onChange={(e) => setTrainStart(e.target.value)}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  TRAIN END
                </label>
                <input
                  type="date"
                  value={trainEnd}
                  onChange={(e) => setTrainEnd(e.target.value)}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  VAL START
                </label>
                <input
                  type="date"
                  value={valStart}
                  onChange={(e) => setValStart(e.target.value)}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  VAL END
                </label>
                <input
                  type="date"
                  value={valEnd}
                  onChange={(e) => setValEnd(e.target.value)}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  TEST START (OUT-OF-SAMPLE)
                </label>
                <input
                  type="date"
                  value={testStart}
                  onChange={(e) => setTestStart(e.target.value)}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  TEST END
                </label>
                <input
                  type="date"
                  value={testEnd}
                  onChange={(e) => setTestEnd(e.target.value)}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  EMBARGO WINDOW (DAYS)
                </label>
                <input
                  type="number"
                  min="0"
                  max="60"
                  value={embargoDays}
                  onChange={(e) => setEmbargoDays(parseInt(e.target.value))}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] font-mono text-text-muted mb-1">
                  MODEL ARCHITECTURE
                </label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  className="w-full p-2 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:ring-1 focus:ring-brand"
                >
                  <option value="xgboost">XGBoost (Primary Multi-Factor)</option>
                  <option value="lightgbm">LightGBM (Benchmark)</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-lg bg-brand hover:bg-brand-hover text-white text-xs font-mono font-bold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Dispatching Job to Celery Worker...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Launch Walk-Forward Backtest Job
                </>
              )}
            </button>
          </form>

          {/* Error */}
          {error && (
            <div className="p-3 rounded-lg border border-rose-500/20 bg-rose-500/5 text-xs font-mono text-rose-500 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Job Result */}
          {jobResponse && (
            <div className="p-4 rounded-lg border border-emerald-500/30 bg-emerald-500/5 text-xs font-mono space-y-2">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Job Dispatched Successfully!</span>
              </div>
              <div className="text-text-muted">
                Job ID: <strong className="text-text-primary">{jobResponse.job_id}</strong>
              </div>
              <div className="text-text-muted">
                Status: <strong className="text-amber-500">{jobResponse.status}</strong>
              </div>
              <div className="text-text-muted">
                Estimated Duration: <strong>~{jobResponse.estimated_seconds} seconds</strong>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
