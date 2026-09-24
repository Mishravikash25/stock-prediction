import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { CompanyScorecard } from "../components/company/CompanyScorecard";
import { ShapBarChart } from "../components/company/ShapBarChart";
import { DualThesisCard } from "../components/company/DualThesisCard";
import { PriceChart } from "../components/company/PriceChart";
import { LoadingState, ErrorState } from "../components/common/LoadingState";
import { CompanyItem } from "../types/api";
import { Building2, Cpu, Clock } from "lucide-react";

export const CompanyPage: React.FC = () => {
  const { ticker: paramTicker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();

  const activeTicker = paramTicker || "TATAMOTORS.NS";
  const [horizonDays, setHorizonDays] = useState<number>(7);
  const [modelType, setModelType] = useState<string>("xgboost");

  // Fetch list of tracked companies for dropdown selector
  const { data: companies } = useQuery({
    queryKey: ["companiesList"],
    queryFn: () => api.getCompanies(),
  });

  // Fetch company analysis (Prediction + SHAP + Structured Report)
  const {
    data: analysis,
    isLoading: isAnalysisLoading,
    isError: isAnalysisError,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useQuery({
    queryKey: ["companyAnalysis", activeTicker, horizonDays, modelType],
    queryFn: () =>
      api.getCompanyAnalysis(activeTicker, {
        horizon_days: horizonDays,
        model_type: modelType,
      }),
  });

  // Fetch company historical time series (Prices + Sentiment)
  const { data: timeSeries } = useQuery({
    queryKey: ["companyTimeSeries", activeTicker],
    queryFn: () => api.getCompanyTimeSeries(activeTicker),
  });

  const handleTickerSelect = (t: string) => {
    navigate(`/company/${t}`);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="w-6 h-6 text-brand" />
            <h1 className="text-2xl font-bold tracking-tight text-text-primary font-ui">
              {analysis?.company_name || activeTicker}
            </h1>
            <span className="font-mono text-sm font-bold text-brand bg-brand/10 border border-brand/20 px-2 py-0.5 rounded">
              {activeTicker}
            </span>
          </div>
          <p className="text-xs font-mono text-text-muted mt-1">
            Sector: <strong className="text-text-secondary">{analysis?.sector || "Automotive"}</strong> | Multi-Factor Scorecard & Explainable AI Narrative
          </p>
        </div>

        {/* Ticker & Horizon Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Company Dropdown */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-mono text-text-muted">Asset:</label>
            <select
              value={activeTicker}
              onChange={(e) => handleTickerSelect(e.target.value)}
              className="px-3 py-1.5 text-xs font-mono bg-surface-1 border border-border rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-brand"
            >
              {companies && companies.length > 0 ? (
                companies.map((c: CompanyItem) => (
                  <option key={c.ticker} value={c.ticker}>
                    {c.ticker} — {c.name}
                  </option>
                ))
              ) : (
                <>
                  <option value="TATAMOTORS.NS">TATAMOTORS.NS</option>
                  <option value="TATASTEEL.NS">TATASTEEL.NS</option>
                  <option value="RELIANCE.NS">RELIANCE.NS</option>
                  <option value="TCS.NS">TCS.NS</option>
                  <option value="INFY.NS">INFY.NS</option>
                  <option value="MARUTI.NS">MARUTI.NS</option>
                  <option value="JSWSTEEL.NS">JSWSTEEL.NS</option>
                  <option value="ONGC.NS">ONGC.NS</option>
                </>
              )}
            </select>
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-text-muted" />
            <div className="flex rounded-lg border border-border bg-surface-1 p-0.5 text-xs font-mono">
              {[1, 7, 30].map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizonDays(h)}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    horizonDays === h
                      ? "bg-brand text-white font-bold"
                      : "text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {h}D
                </button>
              ))}
            </div>
          </div>

          {/* Model Selector */}
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-text-muted" />
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="px-2.5 py-1 text-xs font-mono bg-surface-1 border border-border rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-brand"
            >
              <option value="xgboost">XGBoost (Primary)</option>
              <option value="lightgbm">LightGBM (Benchmark)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Analysis Body */}
      {isAnalysisLoading && <LoadingState message={`Computing multi-factor score and SHAP attributions for ${activeTicker}...`} />}
      {isAnalysisError && (
        <ErrorState
          message={(analysisError as Error).message || "Failed to load company analysis"}
          onRetry={() => refetchAnalysis()}
        />
      )}

      {analysis && (
        <div className="space-y-6">
          {/* Metrics Scorecard */}
          <CompanyScorecard analysis={analysis} />

          {/* Price Time Series & Sentiment Overlay */}
          {timeSeries && <PriceChart ticker={activeTicker} points={timeSeries.points} />}

          {/* 2-Column: SHAP Feature Attributions + Dual-Theses Narrative */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ShapBarChart attributions={analysis.shap_attributions} />
            <DualThesisCard report={analysis.structured_report} />
          </div>
        </div>
      )}
    </div>
  );
};
