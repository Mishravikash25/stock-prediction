import React from "react";
import { Filter, Search } from "lucide-react";
import { EventArchetype } from "../../types/api";

interface EventFiltersProps {
  archetype: string;
  onArchetypeChange: (archetype: string) => void;
  searchTerm: string;
  onSearchChange: (search: string) => void;
  sector: string;
  onSectorChange: (sector: string) => void;
}

const ARCHETYPES: Array<{ id: string; label: string }> = [
  { id: "ALL", label: "All Archetypes" },
  { id: "COMMODITY_SHOCK", label: "Commodity Shock" },
  { id: "POLICY_TAX_CHANGE", label: "Policy / Tax Change" },
  { id: "SUPPLY_DISRUPTION", label: "Supply Disruption" },
  { id: "MACRO_RATE_SHIFT", label: "Macro Rate Shift" },
];

const SECTORS: Array<{ id: string; label: string }> = [
  { id: "ALL", label: "All Sectors" },
  { id: "Automotive", label: "Automotive" },
  { id: "Steel_Metals", label: "Steel & Metals" },
  { id: "Energy_Oil", label: "Energy & Oil" },
  { id: "IT_Services", label: "IT Services" },
];

export const EventFilters: React.FC<EventFiltersProps> = ({
  archetype,
  onArchetypeChange,
  searchTerm,
  onSearchChange,
  sector,
  onSectorChange,
}) => {
  return (
    <div className="p-4 rounded-xl border border-border bg-surface-1 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
      {/* Search Input */}
      <div className="relative w-full md:w-72">
        <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Filter headline, origin, commodity..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-8 pr-3 py-1.5 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand"
        />
      </div>

      {/* Selects & Filters */}
      <div className="flex items-center gap-3 w-full md:w-auto flex-wrap">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-text-muted" />
          <select
            value={archetype}
            onChange={(e) => onArchetypeChange(e.target.value)}
            className="px-3 py-1.5 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-brand"
          >
            {ARCHETYPES.map((a) => (
              <option key={a.id} value={a.id}>
                {a.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={sector}
            onChange={(e) => onSectorChange(e.target.value)}
            className="px-3 py-1.5 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-brand"
          >
            {SECTORS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};
