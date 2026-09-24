import React from "react";
import { StatCard } from "../components/common/StatCard";
import { SectorHeatmap } from "../components/dashboard/SectorHeatmap";
import { RecentEventsFeed } from "../components/dashboard/RecentEventsFeed";
import { TopImpactedCompanies } from "../components/dashboard/TopImpactedCompanies";
import { 
  Network, 
  TrendingUp, 
  ShieldCheck, 
  Cpu
} from "lucide-react";

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary font-ui">
            Market Ripple Intelligence Dashboard
          </h1>
          <p className="text-xs font-mono text-text-muted mt-1">
            Real-Time Shock Propagation & Explainable Multi-Hop Asset Impact Engine
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 rounded-lg bg-surface-1 border border-border text-xs font-mono text-text-secondary flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span>Multi-Hop Engine: Active (α = 0.75)</span>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Knowledge Graph Nodes"
          value="104"
          subValue="Across 4 Key Sectors"
          change="+12 from Seeds"
          changeDirection="up"
          icon={Network}
          badgeText="Neo4j"
          badgeVariant="default"
        />
        <StatCard
          title="Tracked Multi-Hop Edges"
          value="268"
          subValue="Tagged Manual & Inferred"
          change="α^hop Decay"
          changeDirection="neutral"
          icon={Cpu}
          badgeText="Active"
          badgeVariant="bullish"
        />
        <StatCard
          title="7D Directional Accuracy"
          value="71.4%"
          subValue="Purged Test Split"
          change="+4.2% vs baseline"
          changeDirection="up"
          icon={TrendingUp}
          badgeText="XGBoost"
          badgeVariant="bullish"
        />
        <StatCard
          title="Zero Hallucination Gate"
          value="100%"
          subValue="SHAP Number Grounding"
          change="Schema Guarded"
          changeDirection="up"
          icon={ShieldCheck}
          badgeText="Verified"
          badgeVariant="bullish"
        />
      </div>

      {/* Sector Impact Matrix */}
      <SectorHeatmap />

      {/* 2-Column Section: Top Impacted Companies & Recent Events Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <TopImpactedCompanies />
        <RecentEventsFeed />
      </div>
    </div>
  );
};
