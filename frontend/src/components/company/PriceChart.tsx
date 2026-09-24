import React from "react";
import {
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { TimeSeriesPoint } from "../../types/api";
import { formatCurrencyINR, formatShortDate } from "../../lib/utils";
import { LineChart, Activity } from "lucide-react";

interface PriceChartProps {
  ticker: string;
  points: TimeSeriesPoint[];
}

export const PriceChart: React.FC<PriceChartProps> = ({ ticker, points }) => {
  if (!points || points.length === 0) {
    return (
      <div className="p-8 text-center border border-border rounded-xl bg-surface-1 text-xs font-mono text-text-muted">
        No price time series available for ticker {ticker}.
      </div>
    );
  }

  const chartData = points.map((p) => ({
    date: p.date,
    close: p.close,
    open: p.open,
    high: p.high,
    low: p.low,
    volume: p.volume,
    sentiment: p.rolling_sentiment,
    events: p.associated_events,
  }));

  return (
    <div className="p-6 rounded-xl border border-border bg-surface-1 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LineChart className="w-4 h-4 text-brand" />
          <h3 className="text-xs font-bold font-mono text-text-primary uppercase tracking-wider">
            Price Action & FinBERT Rolling Sentiment Overlay
          </h3>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono text-text-muted">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-0.5 bg-brand" /> Close Price (INR)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-0.5 bg-amber-400" /> Rolling Sentiment
          </span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
            <XAxis
              dataKey="date"
              tickFormatter={formatShortDate}
              tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "JetBrains Mono" }}
            />
            <YAxis
              yAxisId="price"
              domain={["auto", "auto"]}
              tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "JetBrains Mono" }}
              tickFormatter={(v) => `₹${v}`}
            />
            <YAxis
              yAxisId="sentiment"
              orientation="right"
              domain={[-1, 1]}
              tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "JetBrains Mono" }}
              tickFormatter={(v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="p-3 rounded-lg border border-border bg-surface-1 shadow-lg text-xs font-mono space-y-1">
                      <div className="font-bold text-text-primary">{data.date}</div>
                      <div className="text-text-secondary">
                        Close: <strong className="text-brand">{formatCurrencyINR(data.close)}</strong>
                      </div>
                      <div className="text-text-secondary">
                        Sentiment:{" "}
                        <strong
                          className={
                            data.sentiment >= 0
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-rose-600 dark:text-rose-400"
                          }
                        >
                          {data.sentiment > 0 ? "+" : ""}
                          {data.sentiment.toFixed(2)}
                        </strong>
                      </div>
                      {data.events && data.events.length > 0 && (
                        <div className="pt-1 border-t border-border text-[10px] text-amber-500">
                          Events: {data.events.join(", ")}
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              yAxisId="price"
              type="monotone"
              dataKey="close"
              stroke="#3B82F6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#priceGradient)"
            />
            <Line
              yAxisId="sentiment"
              type="monotone"
              dataKey="sentiment"
              stroke="#F59E0B"
              strokeWidth={1.5}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
