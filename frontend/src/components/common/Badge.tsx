import React from "react";
import { cn } from "../../lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "bullish" | "bearish" | "neutral" | "outline" | "accent";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = "default", className }) => {
  const variantStyles = {
    default: "bg-surface-2 text-text-primary border-border",
    bullish: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    bearish: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30",
    neutral: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
    outline: "border-border text-text-secondary bg-transparent",
    accent: "bg-brand/10 text-brand border-brand/30",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border font-mono tracking-tight transition-colors",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
};
