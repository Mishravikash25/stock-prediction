import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { RippleCanvas } from "../components/ripple/RippleCanvas";
import { GraphControls } from "../components/ripple/GraphControls";
import { ImpactSummaryTable } from "../components/ripple/ImpactSummaryTable";
import { LoadingState, ErrorState } from "../components/common/LoadingState";
import { RippleGraphNode, EventItem } from "../types/api";
import { Share2 } from "lucide-react";

export const RipplePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const eventIdParam = searchParams.get("event_id");

  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [hopLimit, setHopLimit] = useState<number>(3);
  const [alpha, setAlpha] = useState<number>(0.75);
  const [minStrength, setMinStrength] = useState<number>(0.1);
  const [selectedNode, setSelectedNode] = useState<RippleGraphNode | null>(null);

  // Fetch available events for the selector
  const { data: eventsData } = useQuery({
    queryKey: ["eventsForRipple"],
    queryFn: () => api.getEvents({ limit: 50 }),
  });

  // Set initial event ID
  useEffect(() => {
    if (eventIdParam) {
      setSelectedEventId(eventIdParam);
    } else if (eventsData && eventsData.items.length > 0 && !selectedEventId) {
      setSelectedEventId(eventsData.items[0].id);
    }
  }, [eventIdParam, eventsData, selectedEventId]);

  // Fetch Ripple Graph
  const {
    data: graphData,
    isLoading: isGraphLoading,
    isError: isGraphError,
    error: graphError,
    refetch: refetchGraph,
  } = useQuery({
    queryKey: ["rippleGraph", selectedEventId, hopLimit, alpha, minStrength],
    queryFn: () =>
      api.getRippleGraph({
        event_id: selectedEventId,
        hop_limit: hopLimit,
        alpha,
        min_edge_strength: minStrength,
      }),
    enabled: Boolean(selectedEventId),
  });

  const handleEventChange = (eventId: string) => {
    setSelectedEventId(eventId);
    setSelectedNode(null);
    setSearchParams({ event_id: eventId });
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary font-ui flex items-center gap-2">
            <Share2 className="w-6 h-6 text-brand" />
            Multi-Hop Shock Propagation Map
          </h1>
          <p className="text-xs font-mono text-text-muted mt-1">
            Traversing Industry → Commodity → Supplier Nodes with α^hop Distance Decay
          </p>
        </div>

        {/* Event Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-mono text-text-secondary whitespace-nowrap">
            Active Shock Event:
          </label>
          <select
            value={selectedEventId}
            onChange={(e) => handleEventChange(e.target.value)}
            className="px-3 py-1.5 text-xs font-mono bg-surface-1 border border-border rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-brand max-w-xs truncate"
          >
            {eventsData?.items.map((ev: EventItem) => (
              <option key={ev.id} value={ev.id}>
                {ev.archetype}: {ev.origin_node_id} ({ev.title.slice(0, 32)}...)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Graph Sliders / Controls */}
      <GraphControls
        hopLimit={hopLimit}
        onHopLimitChange={setHopLimit}
        alpha={alpha}
        onAlphaChange={setAlpha}
        minStrength={minStrength}
        onMinStrengthChange={setMinStrength}
      />

      {/* Interactive Graph Canvas */}
      <div className="space-y-2">
        {isGraphLoading && <LoadingState message="Propagating shock wave through graph edges..." />}
        {isGraphError && (
          <ErrorState
            message={(graphError as Error).message || "Failed to load ripple graph"}
            onRetry={() => refetchGraph()}
          />
        )}

        {graphData && (
          <RippleCanvas
            nodes={graphData.nodes}
            edges={graphData.edges}
            onSelectNode={setSelectedNode}
            selectedNodeId={selectedNode?.id}
          />
        )}
      </div>

      {/* Selected Node Inspector Drawer / Card */}
      {selectedNode && (
        <div className="p-4 rounded-xl border border-brand/40 bg-brand/5 animate-in slide-in-from-bottom duration-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-surface-1 border border-border">
                {selectedNode.type}
              </span>
              <h4 className="text-sm font-bold font-mono text-text-primary">
                {selectedNode.label || selectedNode.id}
              </h4>
            </div>
            <p className="text-xs font-mono text-text-secondary mt-1">
              Sector: <strong>{selectedNode.sector || "Cross-Sector"}</strong> | Shock Exposure:{" "}
              <strong>
                {selectedNode.net_ripple_score !== undefined
                  ? `${(selectedNode.net_ripple_score * 100).toFixed(2)}%`
                  : "N/A"}
              </strong>
            </p>
          </div>

          {selectedNode.type === "Company" && (
            <a
              href={`/company/${selectedNode.id}`}
              className="px-3 py-1.5 rounded-lg bg-brand text-white text-xs font-mono font-bold hover:bg-brand-hover transition-colors"
            >
              Analyze {selectedNode.id} &rarr;
            </a>
          )}
        </div>
      )}

      {/* Impact Summary Table */}
      {graphData && (
        <ImpactSummaryTable
          items={graphData.impact_summary}
          selectedTicker={selectedNode?.id}
          onSelectTicker={(ticker: string) => {
            const found = graphData.nodes.find((n: RippleGraphNode) => n.id === ticker);
            if (found) setSelectedNode(found);
          }}
        />
      )}
    </div>
  );
};
