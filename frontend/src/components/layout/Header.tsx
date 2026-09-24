import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { 
  Activity, 
  Layers, 
  Share2, 
  Building2, 
  History, 
  Search
} from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "../../lib/utils";

export const Header: React.FC = () => {
  const [quickSearch, setQuickSearch] = React.useState("");
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickSearch.trim()) return;
    const ticker = quickSearch.trim().toUpperCase();
    navigate(`/company/${ticker}`);
    setQuickSearch("");
  };

  const navItems = [
    { label: "Dashboard", path: "/", icon: Activity },
    { label: "Events", path: "/events", icon: Layers },
    { label: "Ripple Map", path: "/ripple", icon: Share2 },
    { label: "Company Intel", path: "/company", icon: Building2 },
    { label: "Predictions", path: "/predictions", icon: History },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface-base/80 backdrop-blur-md transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-brand/10 border border-brand/30 flex items-center justify-center text-brand font-mono font-black text-sm group-hover:bg-brand group-hover:text-white transition-all shadow-[0_0_12px_rgba(59,130,246,0.2)]">
              RE
            </div>
            <div>
              <div className="font-mono text-sm font-bold tracking-tight text-text-primary flex items-center gap-1.5">
                RIPPLE ENGINE
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              </div>
              <div className="text-[10px] font-mono text-text-muted tracking-wider uppercase">
                Explainable AI Terminal
              </div>
            </div>
          </NavLink>

          {/* Nav Items */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === "/"}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium font-ui transition-all duration-150",
                      isActive
                        ? "bg-surface-2 text-text-primary border border-border shadow-xs"
                        : "text-text-secondary hover:text-text-primary hover:bg-surface-1"
                    )
                  }
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Search & Actions */}
        <div className="flex items-center gap-3">
          <form onSubmit={handleSearch} className="relative hidden sm:block">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Search ticker (e.g. TATAMOTORS.NS)..."
              value={quickSearch}
              onChange={(e) => setQuickSearch(e.target.value)}
              className="w-56 lg:w-64 pl-8 pr-3 py-1.5 text-xs font-mono bg-surface-1 border border-border rounded-lg text-text-input placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand transition-all"
              style={{ color: "var(--text-input)" }}
            />
          </form>

          <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface-1 border border-border text-[11px] font-mono text-text-muted">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>XGBOOST + SHAP // LIVE</span>
          </div>

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
};
