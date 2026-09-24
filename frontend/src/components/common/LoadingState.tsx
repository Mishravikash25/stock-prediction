import React from "react";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { cn } from "../../lib/utils";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading real-time financial intelligence...",
  className,
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-12 text-center", className)}>
      <Loader2 className="w-8 h-8 text-brand animate-spin mb-3" />
      <p className="text-sm font-mono text-text-secondary">{message}</p>
    </div>
  );
};

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Failed to fetch data",
  message,
  onRetry,
  className,
}) => {
  return (
    <div className={cn("p-8 rounded-xl border border-rose-500/20 bg-rose-500/5 text-center flex flex-col items-center", className)}>
      <AlertCircle className="w-10 h-10 text-rose-500 mb-3" />
      <h3 className="text-base font-semibold text-text-primary mb-1">{title}</h3>
      <p className="text-xs font-mono text-text-muted max-w-md mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-2 hover:bg-surface-3 border border-border text-xs font-medium text-text-primary transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      )}
    </div>
  );
};
