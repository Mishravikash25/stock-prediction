import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { EventFilters } from "../components/events/EventFilters";
import { AdHocDetectorModal } from "../components/events/AdHocDetectorModal";
import { LoadingState, ErrorState } from "../components/common/LoadingState";
import { formatDate, getArchetypeColor } from "../lib/utils";
import { EventItem } from "../types/api";
import { 
  Sparkles, 
  ArrowRight, 
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Filter
} from "lucide-react";

export const EventsPage: React.FC = () => {
  const [archetype, setArchetype] = useState("ALL");
  const [sector, setSector] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [isDetectorOpen, setIsDetectorOpen] = useState(false);

  const limit = 10;
  const offset = (page - 1) * limit;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["events", archetype, sector, page],
    queryFn: () =>
      api.getEvents({
        limit,
        offset,
        archetype,
        sector,
      }),
  });

  const filteredItems = React.useMemo(() => {
    if (!data?.items) return [];
    if (!searchTerm.trim()) return data.items;
    const q = searchTerm.toLowerCase();
    return data.items.filter(
      (item: EventItem) =>
        item.title?.toLowerCase().includes(q) ||
        item.source_headline?.toLowerCase().includes(q) ||
        item.origin_node_id?.toLowerCase().includes(q) ||
        item.archetype?.toLowerCase().includes(q)
    );
  }, [data, searchTerm]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / limit)) : 1;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary font-ui">
            Event Explorer & Staging Ledger
          </h1>
          <p className="text-xs font-mono text-text-muted mt-1">
            Real-Time Ingestion: Classified Archetypes, Origin Nodes & Downstream Shock Pathways
          </p>
        </div>

        <button
          onClick={() => setIsDetectorOpen(true)}
          className="px-4 py-2 rounded-lg bg-brand hover:bg-brand-hover text-white text-xs font-mono font-bold transition-colors flex items-center gap-2 self-start sm:self-auto shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5" />
          Classify Custom Headline
        </button>
      </div>

      {/* Filters Bar */}
      <EventFilters
        archetype={archetype}
        onArchetypeChange={(a: string) => {
          setArchetype(a);
          setPage(1);
        }}
        sector={sector}
        onSectorChange={(s: string) => {
          setSector(s);
          setPage(1);
        }}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />

      {/* Events Table Container */}
      <div className="rounded-xl border border-border bg-surface-1 overflow-hidden shadow-sm">
        {isLoading && <LoadingState message="Fetching events from PostgreSQL database..." />}
        {isError && (
          <ErrorState
            message={(error as Error).message || "Failed to load events"}
            onRetry={() => refetch()}
          />
        )}

        {data && filteredItems.length === 0 && (
          <div className="p-12 text-center">
            <Filter className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
            <p className="text-xs font-mono text-text-muted">
              No shock events match your current filter criteria.
            </p>
          </div>
        )}

        {data && filteredItems.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-base text-[11px] font-mono text-text-muted uppercase">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Archetype</th>
                  <th className="py-3 px-4">Event Headline & Details</th>
                  <th className="py-3 px-4">Origin Node</th>
                  <th className="py-3 px-4 text-right">Magnitude</th>
                  <th className="py-3 px-4 text-right">Confidence</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs font-mono">
                {filteredItems.map((event: EventItem) => {
                  const badge = getArchetypeColor(event.archetype);
                  return (
                    <tr
                      key={event.id}
                      className="hover:bg-surface-base/50 transition-colors group"
                    >
                      <td className="py-3.5 px-4 text-text-muted whitespace-nowrap">
                        {formatDate(event.timestamp)}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${badge.bg} ${badge.text} ${badge.border}`}
                        >
                          {event.archetype}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 max-w-md">
                        <div className="font-semibold text-text-primary group-hover:text-brand transition-colors font-ui text-xs">
                          {event.title || event.source_headline}
                        </div>
                        {event.source_url && (
                          <a
                            href={event.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[10px] text-text-muted hover:text-text-secondary flex items-center gap-1 mt-0.5"
                          >
                            <span>source link</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded bg-surface-2 border border-border text-text-primary text-[11px] font-semibold">
                          {event.origin_node_id}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right font-bold">
                        <span
                          className={
                            event.magnitude >= 0
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-rose-600 dark:text-rose-400"
                          }
                        >
                          {(event.magnitude * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right text-text-secondary font-bold">
                        {(event.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="py-3.5 px-4 text-center whitespace-nowrap">
                        <Link
                          to={`/ripple?event_id=${encodeURIComponent(event.id)}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-brand/10 hover:bg-brand/20 border border-brand/30 text-brand text-[11px] font-bold transition-colors"
                        >
                          Trace
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

        {/* Pagination Footer */}
        {data && data.total > limit && (
          <div className="p-4 border-t border-border bg-surface-base flex items-center justify-between text-xs font-mono">
            <span className="text-text-muted">
              Showing {offset + 1}–{Math.min(offset + limit, data.total)} of {data.total} events
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded border border-border bg-surface-1 hover:bg-surface-2 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-text-secondary px-2">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1.5 rounded border border-border bg-surface-1 hover:bg-surface-2 disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Ad-Hoc Detector Modal */}
      <AdHocDetectorModal
        isOpen={isDetectorOpen}
        onClose={() => setIsDetectorOpen(false)}
        onEventDetected={() => refetch()}
      />
    </div>
  );
};
