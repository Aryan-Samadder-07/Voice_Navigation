export type SupportedLang = "en" | "mr" | "hi";

export interface LanguageOption {
  code: SupportedLang;
  locale: string;
  name: string;
  native_name: string;
}

export interface RouteMetadata {
  route_id: string;
  path: string;
  name_en: string;
  name_mr: string;
  description: string;
  keywords_en: string[];
  keywords_mr: string[];
  utterances_en: string[];
  utterances_mr: string[];
}

export interface TelemetryData {
  rpm_used: number;
  rpm_limit: number;
  rpm_available: number;
  daily_used: number;
  daily_limit: number;
  daily_available: number;
  total_lifetime_requests: number;
  last_latency_ms: number;
  avg_latency_ms: number;
  rate_limit_status: "NORMAL" | "WARNING" | "EXCEEDED" | "RATE_LIMITED";
  window_reset_seconds: number;
}

export interface ProcessResult {
  intent: "NAVIGATE" | "PROBLEM_SOLVING" | "UNKNOWN" | "RATE_LIMITED";
  action: "NAVIGATE" | "NONE";
  transcript: string;
  language: string;
  route_id?: string;
  target_path?: string | null;
  target_name?: string;
  confidence?: number;
  match_type?: string;
  model?: string;
  latency_ms?: number;
  response_text: string;
  status?: string;
  telemetry?: TelemetryData;
}

export interface ApiResponse {
  status: string;
  result: ProcessResult;
  tts?: {
    success: boolean;
    audio_base64?: string | null;
    provider: string;
    text: string;
    language: string;
    locale?: string;
    voice_hints?: string[];
  };
}
