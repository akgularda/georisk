export type RiskCategory = "Watch" | "Elevated" | "High" | "Critical";
export type ConfidenceBand = "Low" | "Moderate" | "High";
export type ForecastHorizon = "7d" | "30d" | "90d";
export type FreshnessTier = "fresh" | "aging" | "stale" | "critical" | "missing";
export type LiveSnapshotSourceKind = "preferred" | "fallback" | "missing";
export type OperationalAlertStatus = "below_threshold" | "operating" | "warning" | "alert";
export type OperationalAlertType = "Onset Watch" | "Escalation Watch" | "Monitoring Only" | "No Clear Leader";
export type OperationalModelStatus = "promoted" | "monitoring_only";

export type CountryShapeKey = "iran" | "israel" | "sudan" | "ukraine" | "syria" | "colombia" | "taiwan" | "lebanon";

export interface LiveSnapshotRunProvenance {
  run_name: string;
  artifact_path: string;
  completed_at: string;
  model_name: string | null;
}

export interface LiveSnapshotTargetProvenance {
  training: LiveSnapshotRunProvenance;
  calibration: LiveSnapshotRunProvenance;
  backtest: LiveSnapshotRunProvenance;
}

export interface LiveSnapshotProvenance {
  onset: LiveSnapshotTargetProvenance | null;
  escalation: LiveSnapshotTargetProvenance | null;
  structural: LiveSnapshotTargetProvenance | null;
}

export interface LiveSnapshotManifest {
  schema_version: string;
  snapshot_id: string;
  published_at: string;
  fresh_until: string;
  stale_after: string;
  baseline_used: boolean;
  forecast_as_of: string;
  generated_at: string;
  coverage_count: number;
  top_country_iso3: string | null;
  top_country_name: string | null;
  predicted_conflict: LiveSnapshotPredictedConflict;
  primary_target: string;
  alert_type: OperationalAlertType;
  model_status: OperationalModelStatus;
  no_clear_leader: boolean;
  provenance: LiveSnapshotProvenance;
}

export interface LiveSnapshotConflictCountry {
  iso3: string | null;
  country_name: string;
}

export interface LiveSnapshotPredictedConflict {
  label: string;
  countries: LiveSnapshotConflictCountry[];
  summary: string | null;
  report_slug: string | null;
  reason_source: "report_inputs" | "lead_country" | "fallback";
  target_name: string;
  horizon_days: number;
}

export interface LiveSnapshotForecastCountry {
  iso3: string;
  country_name: string;
  region_name: string | null;
  score: number;
  delta: number;
  forecast_as_of: string;
  freshness_tier: FreshnessTier;
  rank: number;
}

export interface LiveSnapshotForecastSnapshot {
  forecast_as_of: string;
  lead_country_iso3: string | null;
  lead_country_name: string | null;
  predicted_conflict: LiveSnapshotPredictedConflict;
  primary_target: string;
  alert_type: OperationalAlertType;
  no_clear_leader: boolean;
  coverage_count: number;
  countries: LiveSnapshotForecastCountry[];
}

export interface LiveSnapshotModelMetrics {
  brier_score: number;
  roc_auc: number;
  precision_at_10: number;
  recall_at_5: number | null;
  recall_at_10: number | null;
  episode_recall: number | null;
  false_alerts_per_true_alert: number | null;
  no_clear_leader_rate: number | null;
}

export interface LiveSnapshotThresholdPolicy {
  publish_top_n: number;
  publish_threshold: number | null;
  alert_threshold: number;
  warning_threshold: number;
  operating_threshold: number;
}

export interface LiveSnapshotModelCard {
  model_name: string;
  model_version: string;
  target_name: string;
  horizon_days: number;
  published_at: string;
  stale_after: string;
  baseline_used: boolean;
  primary_target: string;
  alert_type: OperationalAlertType;
  model_status: OperationalModelStatus;
  metrics: LiveSnapshotModelMetrics;
  threshold_policy: LiveSnapshotThresholdPolicy;
  provenance: LiveSnapshotProvenance;
}

export interface LiveSnapshotCountryForecast {
  score: number;
  delta: number;
  rank: number;
  forecast_as_of: string;
  freshness_tier: FreshnessTier;
  model_name: string;
  model_version: string;
  target_name: string;
  horizon_days: number;
}

export interface LiveSnapshotCountryDetail {
  iso3: string;
  country_name: string;
  region_name: string | null;
  report_slug: string;
  summary: string;
  chronology: string[];
  top_drivers: string[];
  forecast: LiveSnapshotCountryForecast;
  source_snapshot_hash: string | null;
}

export interface LiveSnapshotBacktestDelta {
  model_name: string;
  delta_pr_auc: number | null;
  delta_roc_auc: number | null;
  delta_f1: number | null;
  delta_brier_score: number | null;
}

export interface LiveSnapshotBacktestSummary {
  primary_model: string;
  baseline_model: string | null;
  top_model_name: string | null;
  primary_target: string | null;
  alert_type: OperationalAlertType | null;
  model_status: OperationalModelStatus | null;
  no_clear_leader: boolean | null;
  publish_threshold: number | null;
  alert_threshold: number | null;
  episode_recall: number | null;
  false_alerts_per_true_alert: number | null;
  recall_at_5: number | null;
  recall_at_10: number | null;
  no_clear_leader_rate: number | null;
  false_alert_burden: number | null;
  new_alert_count: number | null;
  true_alert_count: number | null;
  false_alert_count: number | null;
  calibration_method: string | null;
  baseline_deltas: LiveSnapshotBacktestDelta[];
  plots: {
    probability_distribution: string | null;
    precision_recall: string | null;
  } | null;
}

export interface LiveSnapshotStatus {
  status: "ok" | "fallback" | "missing";
  freshness_tier: FreshnessTier;
  published_at: string | null;
  forecast_as_of: string | null;
  baseline_used: boolean | null;
  coverage_count: number | null;
  lead_country_iso3: string | null;
  lead_country_name: string | null;
  primary_target: string | null;
  alert_type: OperationalAlertType | null;
  model_status: OperationalModelStatus | null;
  no_clear_leader: boolean | null;
  predicted_conflict: LiveSnapshotPredictedConflict | null;
  publish_threshold: number | null;
  alert_threshold: number | null;
  prediction_file: string | null;
  lead_tie_count: number | null;
  source_kind: LiveSnapshotSourceKind;
  source_path: string | null;
  message: string | null;
}

export interface LiveSnapshotBundle {
  manifest: LiveSnapshotManifest;
  forecast_snapshot: LiveSnapshotForecastSnapshot;
  model_card: LiveSnapshotModelCard;
  backtest_summary: LiveSnapshotBacktestSummary;
  status: LiveSnapshotStatus;
  country_details: Record<string, LiveSnapshotCountryDetail>;
  source_kind: LiveSnapshotSourceKind;
  source_path: string;
}

export interface LiveSnapshotLoadResult {
  bundle: LiveSnapshotBundle | null;
  status: LiveSnapshotStatus;
  source_kind: LiveSnapshotSourceKind;
  source_path: string | null;
}

export interface DriverItem {
  title: string;
  detail: string;
  intensity: "Primary" | "Secondary";
}

export interface ScenarioItem {
  label: "Base case" | "Escalation case" | "Tail risk";
  summary: string;
  probabilityNote: string;
}

export interface MarketSignal {
  label: string;
  value: string;
  change: string;
  note: string;
}

export interface TimelineEvent {
  date: string;
  label: string;
  summary: string;
  signalType: string;
}

export interface SignalStat {
  label: string;
  value: string;
  note: string;
}

export interface TrendPoint {
  label: string;
  score: number;
}

export interface CountryOutlook {
  horizon: ForecastHorizon;
  target: string;
  riskCategory: RiskCategory;
  score: number;
  delta: number;
  confidenceBand: ConfidenceBand;
  drivers: string[];
}

export interface CountryProfile {
  iso3: string;
  slug: string;
  name: string;
  region: string;
  shapeKey: CountryShapeKey;
  featured: boolean;
  riskCategory: RiskCategory;
  riskScore: number;
  delta: number;
  horizon: ForecastHorizon;
  confidenceBand: ConfidenceBand;
  updatedAt: string;
  forecastVersion: string;
  modelVersion: string;
  summary: string;
  executiveSummary: string;
  sourceNote: string;
  mainDrivers: string[];
  driverItems: DriverItem[];
  scenarios: ScenarioItem[];
  marketSignals: MarketSignal[];
  currentSignals: SignalStat[];
  timeline: TimelineEvent[];
  trend: TrendPoint[];
  outlooks: CountryOutlook[];
  relatedCountries: string[];
  reportSlugs: string[];
}

export interface ForecastRow {
  slug: string | null;
  country: string;
  region: string;
  target: string;
  horizon: ForecastHorizon;
  riskCategory: RiskCategory;
  score: number;
  delta: number;
  confidenceBand: ConfidenceBand;
  drivers: string[];
  updatedAt: string;
}

export interface ReportFrontmatter {
  title: string;
  slug: string;
  date: string;
  updatedAt: string;
  authors: string[];
  summary: string;
  region: string;
  countries: string[];
  targets: string[];
  horizon: ForecastHorizon;
  tags: string[];
  forecastVersion: string;
  confidenceBand: ConfidenceBand;
  sources: string[];
  heroMetric: string;
  draft: boolean;
  toc: { id: string; label: string }[];
}

export interface MethodologyFrontmatter {
  title: string;
  slug: string;
  date: string;
  updatedAt: string;
  summary: string;
  tags: string[];
  draft: boolean;
}

export interface OperationalThresholdPolicy {
  publishTopN: number;
  publishThreshold: number | null;
  operatingThreshold: number;
  warningThreshold: number;
  alertThreshold: number;
}

export interface OperationalCountry {
  iso3: string;
  slug: string;
  name: string;
  region: string;
  shapeKey: CountryShapeKey | null;
  rank: number;
  probability: number;
  delta: number;
  forecastAsOf: string;
  publishedAt: string;
  freshnessTier: FreshnessTier;
  alertStatus: OperationalAlertStatus;
  summary: string;
  executiveSummary: string;
  topDrivers: string[];
  chronology: string[];
  reportSlug: string | null;
  dossierAvailable: boolean;
  relatedCountries: string[];
  sourceNote: string;
  modelName: string;
  modelVersion: string;
  targetName: string;
  horizonDays: number;
  alertType: OperationalAlertType;
  modelStatus: OperationalModelStatus;
}

export interface OperationalForecastRow {
  slug: string;
  iso3: string;
  country: string;
  region: string;
  rank: number;
  probability: number;
  delta: number;
  alertStatus: OperationalAlertStatus;
  freshnessTier: FreshnessTier;
  forecastAsOf: string;
  topDrivers: string[];
  alertType: OperationalAlertType;
}

export interface OperationalStatusSummary {
  sourceKind: LiveSnapshotSourceKind;
  status: LiveSnapshotStatus["status"];
  freshnessTier: FreshnessTier;
  publishedAt: string | null;
  forecastAsOf: string | null;
  baselineUsed: boolean;
  coverageCount: number;
  leadCountryIso3: string | null;
  leadCountryName: string | null;
  leadTieCount: number;
  message: string | null;
  predictionFile: string | null;
  predictedConflict: LiveSnapshotPredictedConflict | null;
  primaryTarget: string;
  alertType: OperationalAlertType;
  modelStatus: OperationalModelStatus;
  noClearLeader: boolean;
  thresholdPolicy: OperationalThresholdPolicy;
  modelName: string;
  modelVersion: string;
  primaryModel: string;
  baselineModel: string | null;
  topModelName: string | null;
  calibrationMethod: string | null;
  deltaPrAuc: number | null;
  deltaRocAuc: number | null;
  deltaF1: number | null;
  deltaBrierScore: number | null;
  publishThreshold: number | null;
  episodeRecall: number | null;
  falseAlertsPerTrueAlert: number | null;
  recallAt5: number | null;
  recallAt10: number | null;
  noClearLeaderRate: number | null;
  structuralPriorActive: boolean;
  structuralPriorRunName: string | null;
  structuralPriorModelName: string | null;
  structuralPriorCompletedAt: string | null;
}
