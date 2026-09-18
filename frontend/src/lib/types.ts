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

export interface ProcessResult {
  intent: "NAVIGATE" | "PROBLEM_SOLVING" | "UNKNOWN";
  action: "NAVIGATE" | "NONE";
  transcript: string;
  language: string;
  route_id?: string;
  target_path?: string | null;
  target_name?: string;
  confidence?: number;
  match_type?: string;
  response_text: string;
  status?: string;
  hook_metadata?: {
    engine: string;
    ready_for_integration: boolean;
    supported_ml_models: string[];
  };
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
