export type EventArchetype = 
  | 'COMMODITY_SHOCK'
  | 'POLICY_TAX_CHANGE'
  | 'SUPPLY_DISRUPTION'
  | 'MACRO_RATE_SHIFT';

export type PredictionDirection = 'BULLISH' | 'BEARISH' | 'NEUTRAL';
export type RiskLabel = 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE';

export interface EventItem {
  id: string;
  timestamp: string;
  title: string;
  archetype: EventArchetype;
  source_headline: string;
  source_url?: string;
  origin_node_id: string;
  origin_node_type: string;
  magnitude: number;
  confidence: number;
  sentiment_score: number;
  touched_sectors: string[];
  touched_commodities: string[];
}

export interface EventListResponse {
  total: number;
  limit: number;
  offset: number;
  items: EventItem[];
}

export interface ExtractedEntity {
  name: string;
  entity_type: string;
  node_id: string;
}

export interface EventDetailResponse {
  id: string;
  timestamp: string;
  title: string;
  raw_text: string;
  archetype: EventArchetype;
  magnitude: number;
  confidence: number;
  sentiment_score: number;
  extracted_entities: ExtractedEntity[];
  downstream_impact_count: number;
  top_impacted_ticker?: string;
}

export interface DetectEventRequest {
  text: string;
  publish_timestamp?: string;
  source_name?: string;
}

export interface DetectEventResponse {
  detected_event: {
    archetype: EventArchetype;
    magnitude: number;
    confidence: number;
    primary_commodity?: string;
    primary_sector?: string;
    reasoning: string;
    spacy_entities: Array<{ text: string; label: string }>;
  };
}

export interface RippleGraphNode {
  id: string;
  label: string;
  type: 'Sector' | 'Company' | 'Commodity' | 'Macro' | 'Entity';
  initial_shock?: number;
  sector?: string;
  net_ripple_score?: number;
}

export interface RippleGraphEdge {
  source: string;
  target: string;
  relation: string;
  strength: number;
  source_tag: 'manual_seed' | 'inferred';
  hop: number;
  path_shock: number;
}

export interface ImpactSummaryItem {
  ticker: string;
  net_ripple_score: number;
  hop_distance: number;
  path_description: string;
}

export interface RippleGraphResponse {
  event_id: string;
  hop_decay_alpha: number;
  nodes: RippleGraphNode[];
  edges: RippleGraphEdge[];
  impact_summary: ImpactSummaryItem[];
}

export interface CompanyItem {
  ticker: string;
  name: string;
  sector_id: string;
  isin?: string;
  market_cap_category?: string;
  summary?: string;
}

export interface ShapAttribution {
  feature: string;
  value: number;
  shap_contribution: number;
}

export interface StructuredReport {
  summary: string;
  bull_case: string;
  bear_case: string;
  uncertainty_analysis: string;
  transmission_narrative?: string;
}

export interface CompanyAnalysisResponse {
  ticker: string;
  company_name: string;
  sector: string;
  score_timestamp: string;
  prediction: {
    direction: PredictionDirection;
    impact_score: number;
    confidence: number;
    horizon_days: number;
    risk_label: RiskLabel;
  };
  shap_attributions: ShapAttribution[];
  structured_report: StructuredReport;
}

export interface TimeSeriesPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rolling_sentiment: number;
  associated_events: string[];
}

export interface CompanyTimeSeriesResponse {
  ticker: string;
  points: TimeSeriesPoint[];
}

export interface PredictionItem {
  id: string;
  created_at: string;
  ticker: string;
  event_id?: string;
  horizon_days: number;
  predicted_direction: PredictionDirection;
  predicted_score: number;
  confidence: number;
  actual_price_at_prediction: number;
  actual_price_at_horizon?: number;
  actual_return_pct?: number;
  is_correct?: boolean;
  evaluated_at?: string;
}

export interface AccuracySummary {
  horizon_1d_directional_acc: number;
  horizon_7d_directional_acc: number;
  horizon_30d_directional_acc: number;
  brier_score_7d: number;
}

export interface PredictionsListResponse {
  total: number;
  accuracy_summary: AccuracySummary;
  predictions: PredictionItem[];
}

export interface BacktestRunRequest {
  train_start_date: string;
  train_end_date: string;
  val_start_date: string;
  val_end_date: string;
  test_start_date: string;
  test_end_date: string;
  embargo_window_days: number;
  model_type?: string;
}

export interface BacktestJobResponse {
  job_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  estimated_seconds: number;
}
