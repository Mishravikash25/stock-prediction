import React, { useState } from "react";
import { X, Sparkles, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import { api } from "../../lib/api";
import { DetectEventResponse } from "../../types/api";
import { getArchetypeColor } from "../../lib/utils";

interface AdHocDetectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEventDetected?: () => void;
}

export const AdHocDetectorModal: React.FC<AdHocDetectorModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [text, setText] = useState("");
  const [sourceName, setSourceName] = useState("Live Terminal Ingestion");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<DetectEventResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDetect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.detectEvent({
        text: text.trim(),
        source_name: sourceName,
      });
      setResult(response);
    } catch (err) {
      setError((err as Error).message || "Event classification failed");
    } finally {
      setIsLoading(false);
    }
  };

  const sampleTexts = [
    "Ministry of Steel imposes 15% export tax on hot-rolled coil steel to curb domestic inflation.",
    "Crude oil surges 8% following drone strikes on key refinery infrastructure in the Middle East.",
    "Federal Reserve signals 50 bps interest rate hike as core inflation remains elevated.",
    "Automotive chip supplier halts fabrication line in Taiwan due to severe seismic event.",
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-2xl rounded-xl border border-border bg-surface-1 shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-border flex items-center justify-between bg-surface-base">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand/10 border border-brand/30 flex items-center justify-center text-brand">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary">
                Ad-Hoc Event Classification & NER Detector
              </h3>
              <p className="text-[11px] font-mono text-text-muted">
                LLM-Behind-A-Schema + spaCy Entity Extractor
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text-primary transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          <form onSubmit={handleDetect} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-text-primary mb-1">
                News Headline / Announcement Text:
              </label>
              <textarea
                rows={3}
                placeholder="Paste news text, regulatory circular, or market bulletin..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="w-full p-3 text-xs font-mono bg-surface-base border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-brand focus:border-brand"
                required
              />
            </div>

            {/* Preset Samples */}
            <div>
              <span className="text-[11px] font-mono text-text-muted block mb-1.5">
                Or pick a curated market shock prompt:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {sampleTexts.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setText(sample)}
                    className="text-[10px] font-mono px-2 py-1 rounded bg-surface-2 hover:bg-surface-3 border border-border text-text-secondary hover:text-text-primary transition-colors text-left"
                  >
                    {sample.slice(0, 48)}...
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !text.trim()}
              className="w-full py-2.5 px-4 rounded-lg bg-brand hover:bg-brand-hover text-white text-xs font-mono font-bold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Classifying Event & Extracting Entities...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Classify Event & Extract NER
                </>
              )}
            </button>
          </form>

          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-lg border border-rose-500/20 bg-rose-500/5 text-xs font-mono text-rose-500 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Results Output */}
          {result && (
            <div className="p-4 rounded-lg border border-border bg-surface-base space-y-3 animate-in fade-in duration-150">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Classification Result
                </span>
                {(() => {
                  const badge = getArchetypeColor(result.detected_event.archetype);
                  return (
                    <span
                      className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${badge.bg} ${badge.text} ${badge.border}`}
                    >
                      {result.detected_event.archetype}
                    </span>
                  );
                })()}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
                <div className="p-2 rounded bg-surface-1 border border-border text-center">
                  <span className="text-[10px] font-mono text-text-muted block">MAGNITUDE</span>
                  <span className="font-mono text-xs font-bold text-text-primary">
                    {(result.detected_event.magnitude * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="p-2 rounded bg-surface-1 border border-border text-center">
                  <span className="text-[10px] font-mono text-text-muted block">CONFIDENCE</span>
                  <span className="font-mono text-xs font-bold text-text-primary">
                    {(result.detected_event.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="p-2 rounded bg-surface-1 border border-border text-center">
                  <span className="text-[10px] font-mono text-text-muted block">COMMODITY</span>
                  <span className="font-mono text-xs font-bold text-text-primary truncate block">
                    {result.detected_event.primary_commodity || "None"}
                  </span>
                </div>
                <div className="p-2 rounded bg-surface-1 border border-border text-center">
                  <span className="text-[10px] font-mono text-text-muted block">SECTOR</span>
                  <span className="font-mono text-xs font-bold text-text-primary truncate block">
                    {result.detected_event.primary_sector || "None"}
                  </span>
                </div>
              </div>

              {result.detected_event.spacy_entities && result.detected_event.spacy_entities.length > 0 && (
                <div className="pt-2">
                  <span className="text-[11px] font-mono text-text-muted block mb-1">
                    Extracted spaCy NER Entities:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.detected_event.spacy_entities.map((ent, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-surface-2 border border-border text-[11px] font-mono text-text-secondary"
                      >
                        <strong>{ent.text}</strong> ({ent.label})
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {result.detected_event.reasoning && (
                <div className="pt-2 border-t border-border">
                  <span className="text-[11px] font-mono text-text-muted block mb-0.5">
                    LLM Structural Reasoning:
                  </span>
                  <p className="text-xs font-mono text-text-secondary bg-surface-1 p-2.5 rounded border border-border">
                    {result.detected_event.reasoning}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
