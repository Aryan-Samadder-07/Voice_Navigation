"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { speechClient } from "../lib/speechClient";
import { ProcessResult, SupportedLang } from "../lib/types";
import { IntentTrainer } from "./IntentTrainer";

export const VoiceAssistant: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();

  const [language, setLanguage] = useState<SupportedLang>("en");
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>("");
  const [lastResult, setLastResult] = useState<ProcessResult | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [showTrainer, setShowTrainer] = useState<boolean>(false);
  const [manualText, setManualText] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [audioFeedback, setAudioFeedback] = useState<boolean>(true);

  // Set language in speech client
  useEffect(() => {
    speechClient.setLanguage(language);
  }, [language]);

  const handleToggleListening = () => {
    setErrorMessage(null);
    if (isListening) {
      speechClient.stopListening();
    } else {
      setTranscript("");
      speechClient.startListening(
        (text, isFinal) => {
          setTranscript(text);
          if (isFinal) {
            handleProcessCommand(text);
          }
        },
        (listening, error) => {
          setIsListening(listening);
          if (error) {
            setErrorMessage(`Mic Error: ${error}`);
          }
        }
      );
    }
  };

  const handleProcessCommand = async (commandText: string) => {
    if (!commandText.trim()) return;

    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const response = await speechClient.sendCommandToBackend(commandText, language, pathname);
      const res = response.result;
      setLastResult(res);

      // 1. Play TTS feedback if enabled
      if (audioFeedback && res.response_text) {
        speechClient.speak(res.response_text, language, response.tts?.audio_base64);
      }

      // 2. Perform Navigation if intent is NAVIGATE
      if (res.intent === "NAVIGATE" && res.target_path) {
        // Subtle delay for speech feedback start
        setTimeout(() => {
          router.push(res.target_path!);
        }, 350);
      }
    } catch (err: any) {
      console.error("Assistant command processing error:", err);
      setErrorMessage("Failed to process command. Make sure the FastAPI backend is running on port 8000.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualText.trim()) return;
    setTranscript(manualText);
    handleProcessCommand(manualText);
    setManualText("");
  };

  return (
    <>
      {/* Training Modal Drawer */}
      {showTrainer && (
        <div style={{
          position: "fixed",
          bottom: "140px",
          right: "24px",
          width: "480px",
          maxWidth: "calc(100vw - 48px)",
          zIndex: 9999,
        }}>
          <IntentTrainer currentLang={language} onClose={() => setShowTrainer(false)} />
        </div>
      )}

      {/* Main Bottom Docked Assistant Bar */}
      <aside
        aria-label="AI Voice Assistant"
        style={{
        position: "fixed",
        bottom: "16px",
        left: "50%",
        transform: "translateX(-50%)",
        width: "92%",
        maxWidth: "960px",
        background: "#0f172a",
        borderRadius: "16px",
        boxShadow: "0 20px 30px -10px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1)",
        color: "#f8fafc",
        padding: "14px 20px",
        zIndex: 9990,
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        backdropFilter: "blur(8px)"
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "10px" }}>
          
          {/* Left: Assistant Identity & Language Switcher */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "rgba(255, 255, 255, 0.08)",
              padding: "4px 10px",
              borderRadius: "20px"
            }}>
              <span style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: isListening ? "#ef4444" : isProcessing ? "#eab308" : "#22c55e",
                boxShadow: isListening ? "0 0 8px #ef4444" : "none"
              }} />
              <span style={{ fontSize: "0.85rem", fontWeight: "700", letterSpacing: "0.5px" }}>
                AI VOICE ASSISTANT
              </span>
            </div>

            {/* Language Selector */}
            <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "2px" }}>
              <button
                type="button"
                onClick={() => setLanguage("en")}
                style={{
                  background: language === "en" ? "#3b82f6" : "transparent",
                  color: "#ffffff",
                  border: "none",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "0.78rem",
                  fontWeight: "600",
                  cursor: "pointer"
                }}
              >
                EN (English)
              </button>
              <button
                type="button"
                onClick={() => setLanguage("mr")}
                style={{
                  background: language === "mr" ? "#3b82f6" : "transparent",
                  color: "#ffffff",
                  border: "none",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "0.78rem",
                  fontWeight: "600",
                  cursor: "pointer"
                }}
              >
                MR (मराठी)
              </button>
            </div>
          </div>

          {/* Center: Controls & Voice Mic Action */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              type="button"
              onClick={handleToggleListening}
              style={{
                background: isListening ? "#dc2626" : "#2563eb",
                color: "#ffffff",
                border: "none",
                borderRadius: "50px",
                padding: "8px 18px",
                fontWeight: "700",
                fontSize: "0.88rem",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                cursor: "pointer",
                boxShadow: isListening ? "0 0 15px rgba(220, 38, 38, 0.6)" : "0 4px 12px rgba(37, 99, 235, 0.4)",
                transition: "all 0.2s ease"
              }}
            >
              <span>{isListening ? "🛑 Stop" : "🎙️ Speak"}</span>
              {isListening && <span style={{ fontSize: "0.75rem", opacity: 0.9 }}>Listening...</span>}
            </button>

            {/* Quick Text Command Input */}
            <form onSubmit={handleManualSubmit} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <input
                type="text"
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                placeholder={language === "mr" ? "किंवा येथे मराठीत टाइप करा..." : "or type a command (e.g. 'go to settings')..."}
                style={{
                  background: "rgba(255, 255, 255, 0.08)",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  color: "#f8fafc",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  fontSize: "0.82rem",
                  width: "220px"
                }}
              />
              <button
                type="submit"
                disabled={!manualText.trim() || isProcessing}
                style={{
                  background: "rgba(255, 255, 255, 0.15)",
                  border: "none",
                  color: "#f8fafc",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  fontSize: "0.82rem",
                  cursor: "pointer",
                  fontWeight: "600"
                }}
              >
                Send
              </button>
            </form>

            {/* Train & Audio Options */}
            <button
              type="button"
              onClick={() => setShowTrainer(!showTrainer)}
              style={{
                background: showTrainer ? "rgba(255, 255, 255, 0.25)" : "rgba(255, 255, 255, 0.1)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                color: "#f8fafc",
                borderRadius: "6px",
                padding: "6px 10px",
                fontSize: "0.8rem",
                cursor: "pointer",
                fontWeight: "600"
              }}
              title="Open Trainable Intents Engine"
            >
              🎓 Train Intents
            </button>

            <button
              type="button"
              onClick={() => setAudioFeedback(!audioFeedback)}
              style={{
                background: "transparent",
                border: "none",
                color: audioFeedback ? "#38bdf8" : "#64748b",
                fontSize: "1.1rem",
                cursor: "pointer",
                padding: "4px"
              }}
              title={audioFeedback ? "TTS Audio Feedback On" : "TTS Audio Feedback Muted"}
            >
              {audioFeedback ? "🔊" : "🔇"}
            </button>
          </div>
        </div>

        {/* Live Status, STT Transcript, and AI Action Feedback */}
        <div style={{
          background: "rgba(0, 0, 0, 0.3)",
          borderRadius: "8px",
          padding: "8px 12px",
          display: "grid",
          gridTemplateColumns: "1fr auto",
          gap: "12px",
          alignItems: "center",
          fontSize: "0.82rem"
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "3px" }}>
              <span style={{ color: "#94a3b8", fontWeight: "600" }}>Transcript (STT):</span>
              <span style={{ color: transcript ? "#38bdf8" : "#64748b", fontStyle: transcript ? "normal" : "italic" }}>
                {transcript || (language === "mr" ? "आवाज ऐकण्यासाठी 'Speak' वर क्लिक करा..." : "Click 'Speak' and give a voice command...")}
              </span>
            </div>

            {lastResult && (
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span style={{ color: "#a855f7", fontWeight: "600" }}>Assistant:</span>
                <span style={{ color: "#e2e8f0" }}>{lastResult.response_text}</span>
              </div>
            )}

            {errorMessage && (
              <div style={{ color: "#f87171", marginTop: "2px" }}>
                ⚠️ {errorMessage}
              </div>
            )}
          </div>

          {/* Action Badge */}
          {lastResult && (
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              {lastResult.intent === "NAVIGATE" && (
                <span style={{
                  background: "#15803d",
                  color: "#dcfce7",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontWeight: "700",
                  fontSize: "0.75rem",
                  letterSpacing: "0.3px"
                }}>
                  ➔ NAVIGATED: {lastResult.target_path}
                </span>
              )}
              {lastResult.intent === "PROBLEM_SOLVING" && (
                <span style={{
                  background: "#854d0e",
                  color: "#fef08a",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontWeight: "700",
                  fontSize: "0.75rem"
                }}>
                  ⚙️ QA / ML: Under Development
                </span>
              )}
              {lastResult.confidence !== undefined && (
                <span style={{
                  background: "rgba(255, 255, 255, 0.1)",
                  color: "#cbd5e1",
                  padding: "4px 6px",
                  borderRadius: "4px",
                  fontSize: "0.7rem"
                }}>
                  Conf: {Math.round((lastResult.confidence || 0) * 100)}%
                </span>
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
