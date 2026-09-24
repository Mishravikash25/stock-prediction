import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { formatDate, getArchetypeColor } from "../../lib/utils";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Layers, ArrowRight, Activity } from "lucide-react";

export const RecentEventsFeed: React.FC = () => {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["recentEvents"],
    queryFn: () => api.getEvents({ limit: 5 }),
  });

  return (
    <div className="rounded-xl border border-border bg-surface-1 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand" />
          <h2 className="text-sm font-bold font-ui text-text-primary uppercase tracking-wider">
            Live Shock Feed
          </h2>
        </div>
        <Link
          to="/events"
          className="text-xs font-mono text-brand hover:underline flex items-center gap-1"
        >
          View all events <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {isLoading && <LoadingState message="Connecting to ingestion event bus..." />}
      {isError && (
        <ErrorState
          message={(error as Error).message || "Could not load recent events"}
          onRetry={() => refetch()}
        />
      )}

      {data && data.items.length === 0 && (
        <div className="text-center py-8 text-xs font-mono text-text-muted">
          No macro shock events detected in the staging pipeline.
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-3">
          {data.items.map((event) => {
            const badge = getArchetypeColor(event.archetype);
            return (
              <div
                key={event.id}
                className="p-4 rounded-lg border border-border bg-surface-base hover:border-brand/40 transition-all duration-150 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${badge.bg} ${badge.text} ${badge.border}`}
                    >
                      {event.archetype.replace(/_/g, " ")}
                    </span>
                    <span className="text-[11px] font-mono text-text-muted">
                      {formatDate(event.timestamp)}
                    </span>
                  </div>
                  <h3 className="text-xs font-semibold text-text-primary line-clamp-1">
                    {event.title || event.source_headline}
                  </h3>
                  <div className="flex items-center gap-3 text-[11px] font-mono text-text-secondary">
                    <span>
                      Origin: <strong className="text-text-primary">{event.origin_node_id}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Mag:{" "}
                      <strong
                        className={
                          event.magnitude >= 0
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-rose-600 dark:text-rose-400"
                        }
                      >
                        {(event.magnitude * 100).toFixed(1)}%
                      </strong>
                    </span>
                    <span>•</span>
                    <span>
                      Conf: <strong>{(event.confidence * 100).toFixed(0)}%</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <Link
                    to={`/ripple?event_id=${encodeURIComponent(event.id)}`}
                    className="px-3 py-1.5 rounded-md bg-brand/10 hover:bg-brand/20 border border-brand/30 text-brand text-xs font-mono font-semibold transition-colors whitespace-nowrap flex items-center gap-1"
                  >
                    Trace Shock
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
