import React from "react";
import { Sliders, Activity } from "lucide-react";

interface GraphControlsProps {
  hopLimit: number;
  onHopLimitChange: (hops: number) => void;
  alpha: number;
  onAlphaChange: (alpha: number) => void;
  minStrength: number;
  onMinStrengthChange: (strength: number) => void;
}

export const GraphControls: React.FC<GraphControlsProps> = ({
  hopLimit,
  onHopLimitChange,
  alpha,
  onAlphaChange,
  minStrength,
  onMinStrengthChange,
}) => {
  return (
    <div className="p-4 rounded-xl border border-border bg-surface-1 shadow-sm space-y-4">
      <div className="flex items-center gap-2 pb-2 border-b border-border text-xs font-bold text-text-primary uppercase tracking-wider font-mono">
        <Sliders className="w-3.5 h-3.5 text-brand" />
        Shock Propagation Parameters
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {/* Hop Limit */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-text-secondary">Max Traversal Hops:</span>
            <span className="font-bold text-text-primary">{hopLimit} Hops</span>
          </div>
          <input
            type="range"
            min="1"
            max="4"
            step="1"
            value={hopLimit}
            onChange={(e) => onHopLimitChange(parseInt(e.target.value))}
            className="w-full h-1.5 bg-surface-base rounded-lg appearance-none cursor-pointer accent-brand"
          />
          <div className="flex justify-between text-[10px] font-mono text-text-muted">
            <span>1</span>
            <span>2</span>
            <span>3</span>
            <span>4</span>
          </div>
        </div>

        {/* Alpha Decay Parameter */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-text-secondary">Alpha Decay (α^hop):</span>
            <span className="font-bold text-brand">{alpha.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={alpha}
            onChange={(e) => onAlphaChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-surface-base rounded-lg appearance-none cursor-pointer accent-brand"
          />
          <div className="flex justify-between text-[10px] font-mono text-text-muted">
            <span>0.10 (fast decay)</span>
            <span>0.75 (calibrated)</span>
            <span>1.00 (undamped)</span>
          </div>
        </div>

        {/* Min Edge Strength */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-text-secondary">Min Edge Weight:</span>
            <span className="font-bold text-text-primary">{minStrength.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.0"
            max="0.8"
            step="0.05"
            value={minStrength}
            onChange={(e) => onMinStrengthChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-surface-base rounded-lg appearance-none cursor-pointer accent-brand"
          />
          <div className="flex justify-between text-[10px] font-mono text-text-muted">
            <span>0.00</span>
            <span>0.40</span>
            <span>0.80</span>
          </div>
        </div>
      </div>
    </div>
  );
};
