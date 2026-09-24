import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Header } from "./components/layout/Header";
import { DashboardPage } from "./pages/DashboardPage";
import { EventsPage } from "./pages/EventsPage";
import { RipplePage } from "./pages/RipplePage";
import { CompanyPage } from "./pages/CompanyPage";
import { PredictionsPage } from "./pages/PredictionsPage";

export const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-surface-base text-text-primary flex flex-col font-ui antialiased transition-colors duration-200 selection:bg-brand selection:text-white">
        {/* Navigation Header */}
        <Header />

        {/* Main Content Viewport */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/ripple" element={<RipplePage />} />
            <Route path="/company" element={<CompanyPage />} />
            <Route path="/company/:ticker" element={<CompanyPage />} />
            <Route path="/predictions" element={<PredictionsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        {/* Terminal Footer */}
        <footer className="border-t border-border bg-surface-base py-6 transition-colors">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-text-muted">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>MARKET RIPPLE ENGINE v1.0.0 // QUANT RESEARCH & INTELLIGENCE</span>
            </div>
            <div className="flex items-center gap-4">
              <span>Stack: React + Vite + Tailwind + FastAPI + XGBoost + Neo4j</span>
              <span>•</span>
              <span>Point-In-Time Embargoed</span>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
};

export default App;
