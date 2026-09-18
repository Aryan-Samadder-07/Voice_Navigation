import { ApiResponse, SupportedLang } from "./types";

const rawApiUrl = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api").trim().replace(/\/+$/, "");
export const API_BASE_URL = rawApiUrl.endsWith("/api") ? rawApiUrl : `${rawApiUrl}/api`;

// Speech Recognition Type Definitions
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export class SpeechClient {
  private recognition: any = null;
  private isListening: boolean = false;
  private currentLang: SupportedLang = "en";
  private onTranscriptCallback?: (transcript: string, isFinal: boolean) => void;
  private onStatusChangeCallback?: (isListening: boolean, error?: string) => void;

  constructor() {
    if (typeof window !== "undefined") {
      const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognitionClass) {
        this.recognition = new SpeechRecognitionClass();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
          this.isListening = true;
          this.onStatusChangeCallback?.(true);
        };

        this.recognition.onresult = (event: any) => {
          let interimTranscript = "";
          let finalTranscript = "";

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcript;
            } else {
              interimTranscript += transcript;
            }
          }

          if (finalTranscript) {
            this.onTranscriptCallback?.(finalTranscript, true);
          } else if (interimTranscript) {
            this.onTranscriptCallback?.(interimTranscript, false);
          }
        };

        this.recognition.onerror = (event: any) => {
          console.warn("Speech recognition event error:", event.error);
          this.isListening = false;
          this.onStatusChangeCallback?.(false, event.error);
        };

        this.recognition.onend = () => {
          this.isListening = false;
          this.onStatusChangeCallback?.(false);
        };
      }
    }
  }

  public isSupported(): boolean {
    if (typeof window === "undefined") return false;
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  public setLanguage(lang: SupportedLang) {
    this.currentLang = lang;
    if (this.recognition) {
      this.recognition.lang = lang === "mr" ? "mr-IN" : "en-IN";
    }
  }

  public startListening(
    onTranscript: (transcript: string, isFinal: boolean) => void,
    onStatusChange: (isListening: boolean, error?: string) => void
  ) {
    this.onTranscriptCallback = onTranscript;
    this.onStatusChangeCallback = onStatusChange;

    if (!this.recognition) {
      onStatusChange(false, "Speech recognition not supported in this browser.");
      return;
    }

    try {
      this.recognition.lang = this.currentLang === "mr" ? "mr-IN" : "en-IN";
      this.recognition.start();
    } catch (err: any) {
      console.warn("Failed to start speech recognition:", err);
      onStatusChange(false, err?.message || "Recognition start error");
    }
  }

  public stopListening() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (err) {
        console.warn("Error stopping recognition:", err);
      }
    }
    this.isListening = false;
    this.onStatusChangeCallback?.(false);
  }

  public async sendCommandToBackend(text: string, lang: SupportedLang, currentPath: string): Promise<ApiResponse> {
    const res = await fetch(`${API_BASE_URL}/assistant/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        language: lang,
        current_path: currentPath
      })
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.statusText}`);
    }

    return await res.json();
  }

  public speak(text: string, lang: SupportedLang, audioBase64?: string | null) {
    if (typeof window === "undefined") return;

    // 1. If backend provided base64 audio (e.g. Sarvam Bulbul / Cloud TTS)
    if (audioBase64) {
      try {
        const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
        audio.play().catch(e => console.warn("Audio element play error:", e));
        return;
      } catch (err) {
        console.warn("Audio playback error:", err);
      }
    }

    // 2. Web Speech API SpeechSynthesis
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel(); // Stop any active speech

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      if (lang === "mr") {
        utterance.lang = "mr-IN";
      } else {
        utterance.lang = "en-IN";
      }

      // Find best matching voice
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        const targetLocale = lang === "mr" ? "mr" : "en";
        const matchedVoice = voices.find(
          v => v.lang.toLowerCase().includes(targetLocale) || (lang === "mr" && (v.name.includes("Marathi") || v.name.includes("मराठी")))
        );
        if (matchedVoice) {
          utterance.voice = matchedVoice;
        }
      }

      window.speechSynthesis.speak(utterance);
    }
  }
}

export const speechClient = new SpeechClient();
