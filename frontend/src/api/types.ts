export type Reason = {
  feature: string;
  value: number;
  /** SHAP value in log odds; positive pushes toward phishing. */
  contribution: number;
};

export type UrlPart = {
  text: string;
  kind: string;
};

export type Prediction = {
  url: string;
  score: number;
  is_phishing: boolean;
  model_version: string;
  threshold: number;
  latency_ms: number;
  reasons: Reason[] | null;
  parts: UrlPart[] | null;
};

export type MonthlyMetrics = {
  run_date: string;
  model_version: string;
  openphish_n: number;
  openphish_recall: number;
  openphish_https_recall: number | null;
  legit_n: number;
  legit_fpr: number;
  api_urls: number;
  drifted_columns: number | null;
};

export type Stats = {
  months: MonthlyMetrics[];
  latest_by_scheme: Partial<Record<"http" | "https", { n: number; recall: number }>>;
  live_predictions: number;
  batch_predictions: number;
  updated_at: string;
  model_version: string;
};
