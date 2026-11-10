export interface Summary {
  screenings: number;
  alerts: number;
  auto_clear: number;
  auto_clear_ci: [number, number];
  clearable_share: number;
  true_matches: number;
  matches_cleared: number;
  policy_breaches: number;
  media_hits: number;
  media_closed: number;
  true_findings: number;
  missed_findings: number;
  wrong_person: number;
  injected: number;
  obeyed: number;
  analyst_hours_per_1000: number;
  eur_per_1000: number;
  p95_ms: number;
}

export interface Gate {
  ship: boolean;
  failed: string[];
  checks: { check: string; value: number; limit: number; ok: boolean }[];
}

export interface Variant {
  label: string;
  all: Summary;
  tenants: Record<string, Summary>;
  gate: Gate;
}

export interface Run {
  tenants: string[];
  variants: Record<string, Variant>;
  commit?: string;
}

export interface Activation {
  tenant: string;
  config_lines: number;
  theta: number | null;
  live: boolean;
  seconds: number;
  mapping_ok: boolean;
  shadow: { cleared?: number; clears_analysts_agree_with?: number };
  generic_live: boolean | null;
}

export interface TierRow {
  tier: string;
  rate: number;
  lower: number;
}

export interface Results {
  heldout: Run | null;
  dev: Run;
  activation: Activation[];
  routing: Record<string, { target: number; tiers: TierRow[]; chosen: string; meets_target: boolean }>;
}
