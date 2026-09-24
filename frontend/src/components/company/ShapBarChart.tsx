import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { ShapAttribution } from "../../types/api";
import { Cpu, HelpCircle } from "lucide-react";

interface ShapBarChartProps {
  attributions: ShapAttribution[];
}

export const ShapBarChart: React.FC<ShapBarChartProps> = ({ attributions }) => {
  // Sort by absolute SHAP contribution descending
  const sorted = React.useMemo(() => {
    return [...attributions].sort(
      (a, b) => Math.abs(b.shap_contribution) - Math.abs(a.shap_contribution)
    );
  }, [attributions]);

  const chartData = sorted.map((attr) => ({
    name: attr.feature.replace(/_/g, " "),
    rawFeature: attr.feature,
    value: attr.shap_contribution,
    featureValue: attr.value,
  }));

  return (
    <div className="p-6 rounded-xl border border-border bg-surface-1 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-brand" />
          <h3 className="text-xs font-bold font-mono text-text-primary uppercase tracking-wider">
            SHAP Feature Attributions (Local Explainability)
          </h3>
        </div>
        <div className="flex items-center gap-1 text-[11px] font-mono text-text-muted">
          <span>Base Value &plusmn; SHAP &rarr; Impact Score</span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
          >
            <XAxis
              type="number"
              tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "JetBrains Mono" }}
              domain={["auto", "auto"]}
              tickFormatter={(v) => `${(v * 100).toFixed(1)}%`}
            />
            <YAxis
              dataKey="name"
              type="category"
              tick={{ fill: "var(--text-secondary)", fontSize: 11, fontFamily: "Inter" }}
              width={140}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  const isBull = data.value >= 0;
                  return (
                    <div className="p-3 rounded-lg border border-border bg-surface-1 shadow-lg text-xs font-mono">
                      <div className="font-bold text-text-primary mb-1">{data.rawFeature}</div>
                      <div className="text-text-muted text-[11px]">
                        Raw Feature Value: <span className="text-text-primary font-bold">{data.featureValue}</span>
                      </div>
                      <div className="mt-1 text-[11px]">
                        SHAP Contribution:{" "}
                        <span
                          className={`font-bold ${
                            isBull
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-rose-600 dark:text-rose-400"
                          }`}
                        >
                          {(data.value * 100).toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine x={0} stroke="var(--border)" strokeWidth={1.5} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.value >= 0 ? "#10B981" : "#F43F5E"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between text-[11px] font-mono text-text-muted pt-2 border-t border-border">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500" /> Positive Attribution (Boost)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-xs bg-rose-500" /> Negative Attribution (Drag)
        </span>
      </div>
    </div>
  );
};
