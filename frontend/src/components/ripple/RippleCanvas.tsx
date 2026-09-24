import React, { useState, useMemo } from "react";
import { RippleGraphNode, RippleGraphEdge } from "../../types/api";
import { cn } from "../../lib/utils";
import { ZoomIn, ZoomOut, RotateCcw, Info } from "lucide-react";

interface RippleCanvasProps {
  nodes: RippleGraphNode[];
  edges: RippleGraphEdge[];
  onSelectNode: (node: RippleGraphNode | null) => void;
  selectedNodeId?: string | null;
}

export const RippleCanvas: React.FC<RippleCanvasProps> = ({
  nodes,
  edges,
  onSelectNode,
  selectedNodeId,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Calculate dynamic circular or layered graph positions for nodes
  const nodePositions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    if (!nodes || nodes.length === 0) return map;

    // Center coordinates
    const cx = 450;
    const cy = 260;

    // Origin or central nodes (Commodity or Event nodes)
    const origins = nodes.filter((n) => n.type === "Commodity" || n.type === "Macro" || n.type === "Sector");
    const companies = nodes.filter((n) => n.type === "Company");
    const others = nodes.filter((n) => !origins.includes(n) && !companies.includes(n));

    // Place origins at inner ring / center
    if (origins.length === 1) {
      map.set(origins[0].id, { x: cx, y: cy });
    } else {
      origins.forEach((node, idx) => {
        const angle = (idx / Math.max(1, origins.length)) * 2 * Math.PI - Math.PI / 2;
        const r = 110;
        map.set(node.id, {
          x: cx + r * Math.cos(angle),
          y: cy + r * Math.sin(angle),
        });
      });
    }

    // Place company nodes on outer ring
    companies.forEach((node, idx) => {
      const angle = (idx / Math.max(1, companies.length)) * 2 * Math.PI - Math.PI / 2;
      const r = 210;
      map.set(node.id, {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      });
    });

    // Place remaining nodes
    others.forEach((node, idx) => {
      const angle = (idx / Math.max(1, others.length)) * 2 * Math.PI;
      const r = 160;
      map.set(node.id, {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      });
    });

    return map;
  }, [nodes]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target instanceof SVGElement && e.target.tagName === "svg") {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const getNodeColor = (node: RippleGraphNode) => {
    switch (node.type) {
      case "Commodity":
        return { fill: "#F59E0B", stroke: "#D97706", text: "#F59E0B" }; // Amber
      case "Sector":
        return { fill: "#3B82F6", stroke: "#2563EB", text: "#3B82F6" }; // Blue
      case "Company":
        if (node.net_ripple_score !== undefined && node.net_ripple_score < 0) {
          return { fill: "#F43F5E", stroke: "#E11D48", text: "#F43F5E" }; // Rose
        }
        return { fill: "#10B981", stroke: "#059669", text: "#10B981" }; // Emerald
      case "Macro":
        return { fill: "#8B5CF6", stroke: "#7C3AED", text: "#8B5CF6" }; // Purple
      default:
        return { fill: "#64748B", stroke: "#475569", text: "#64748B" }; // Slate
    }
  };

  return (
    <div className="relative w-full h-[520px] rounded-xl border border-border bg-surface-base overflow-hidden select-none">
      {/* Zoom / Pan Controls Toolbar */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 p-1 rounded-lg border border-border bg-surface-1/90 backdrop-blur-xs shadow-sm">
        <button
          onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
          className="p-1.5 rounded hover:bg-surface-2 text-text-secondary hover:text-text-primary transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(0.5, z - 0.2))}
          className="p-1.5 rounded hover:bg-surface-2 text-text-secondary hover:text-text-primary transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          className="p-1.5 rounded hover:bg-surface-2 text-text-secondary hover:text-text-primary transition-colors"
          title="Reset View"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Legend Badge */}
      <div className="absolute bottom-4 left-4 z-10 p-3 rounded-lg border border-border bg-surface-1/90 backdrop-blur-xs shadow-sm text-[11px] font-mono space-y-1.5">
        <div className="text-text-muted font-bold uppercase text-[10px]">Node Types & Tags</div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-amber-500">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Commodity
          </span>
          <span className="flex items-center gap-1 text-blue-500">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Sector
          </span>
          <span className="flex items-center gap-1 text-emerald-500">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Company (+ / -)
          </span>
        </div>
        <div className="flex items-center gap-3 text-text-muted pt-1 border-t border-border/50">
          <span>Solid Line: manual_seed</span>
          <span>Dashed Line: inferred</span>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="8"
            markerHeight="6"
            refX="18"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" fill="currentColor" className="text-border" />
          </marker>
        </defs>

        <g
          transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}
          className="transition-transform duration-75"
        >
          {/* Render Edges */}
          {edges.map((edge, idx) => {
            const sourcePos = nodePositions.get(edge.source);
            const targetPos = nodePositions.get(edge.target);
            if (!sourcePos || !targetPos) return null;

            const isManual = edge.source_tag === "manual_seed";
            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={sourcePos.x}
                  y1={sourcePos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke={isManual ? "var(--border)" : "var(--border)"}
                  strokeWidth={Math.max(1.2, edge.strength * 2.5)}
                  strokeDasharray={isManual ? undefined : "4 4"}
                  strokeOpacity={Math.max(0.3, 1 - edge.hop * 0.2)}
                  markerEnd="url(#arrowhead)"
                />
                {/* Edge Label on Midpoint */}
                <text
                  x={(sourcePos.x + targetPos.x) / 2}
                  y={(sourcePos.y + targetPos.y) / 2 - 4}
                  textAnchor="middle"
                  fill="var(--text-muted)"
                  fontSize="9"
                  fontFamily="JetBrains Mono, monospace"
                  className="pointer-events-none"
                >
                  {edge.relation} ({(edge.path_shock * 100).toFixed(1)}%)
                </text>
              </g>
            );
          })}

          {/* Render Nodes */}
          {nodes.map((node) => {
            const pos = nodePositions.get(node.id);
            if (!pos) return null;

            const isSelected = selectedNodeId === node.id;
            const colors = getNodeColor(node);

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectNode(isSelected ? null : node);
                }}
                className="cursor-pointer group"
              >
                {/* Pulse Glow for Selected Node */}
                {isSelected && (
                  <circle
                    r="28"
                    fill="none"
                    stroke={colors.fill}
                    strokeWidth="2"
                    strokeOpacity="0.6"
                    className="animate-ping"
                  />
                )}

                {/* Node Body */}
                <circle
                  r={node.type === "Commodity" ? 22 : 18}
                  fill="var(--surface-1)"
                  stroke={colors.fill}
                  strokeWidth={isSelected ? 3 : 2}
                  className="transition-all duration-150 group-hover:scale-110"
                />

                {/* Node Inner Core */}
                <circle
                  r={node.type === "Commodity" ? 8 : 6}
                  fill={colors.fill}
                />

                {/* Node Label */}
                <text
                  y="30"
                  textAnchor="middle"
                  fill="var(--text-primary)"
                  fontSize="10"
                  fontWeight="600"
                  fontFamily="JetBrains Mono, monospace"
                  className="pointer-events-none drop-shadow-xs"
                >
                  {node.label || node.id}
                </text>

                {/* Net Ripple Score Badge */}
                {node.net_ripple_score !== undefined && (
                  <text
                    y="-24"
                    textAnchor="middle"
                    fill={colors.text}
                    fontSize="9"
                    fontWeight="bold"
                    fontFamily="JetBrains Mono, monospace"
                    className="pointer-events-none"
                  >
                    {(node.net_ripple_score * 100).toFixed(1)}%
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
};
