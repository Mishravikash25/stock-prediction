import React from "react";
import { cn } from "../../lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  change?: string;
  changeDirection?: "up" | "down" | "neutral";
  icon?: LucideIcon;
  badgeText?: string;
  badgeVariant?: "default" | "bullish" | "bearish" | "neutral";
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subValue,
  change,
  changeDirection,
  icon: Icon,
  badgeText,
  badgeVariant = "default",
  className,
}) => {
  return (
    <div
      className={cn(
        "p-5 rounded-xl border border-border bg-surface-1 hover:border-brand/40 transition-all duration-200 shadow-sm relative overflow-hidden group",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <div className="w-8 h-8 rounded-lg bg-surface-2 flex items-center justify-center text-text-secondary group-hover:text-brand group-hover:bg-brand/10 transition-colors">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="font-mono text-2xl font-bold tracking-tight text-text-primary">
          {value}
        </div>
        {badgeText && (
          <span
            className={cn(
              "px-2 py-0.5 text-xs font-mono font-semibold rounded-md border",
              badgeVariant === "bullish" && "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
              badgeVariant === "bearish" && "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20",
              badgeVariant === "neutral" && "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
              badgeVariant === "default" && "bg-surface-2 text-text-secondary border-border"
            )}
          >
            {badgeText}
          </span>
        )}
      </div>

      {(subValue || change) && (
        <div className="mt-2 flex items-center gap-2 text-xs font-mono text-text-muted">
          {change && (
            <span
              className={cn(
                "font-semibold",
                changeDirection === "up" && "text-emerald-600 dark:text-emerald-400",
                changeDirection === "down" && "text-rose-600 dark:text-rose-400",
                changeDirection === "neutral" && "text-text-secondary"
              )}
            >
              {change}
            </span>
          )}
          {subValue && <span>{subValue}</span>}
        </div>
      )}
    </div>
  );
};
