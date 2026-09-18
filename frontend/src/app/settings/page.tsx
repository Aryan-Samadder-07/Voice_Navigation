import React from "react";

export default function SettingsPage() {
  return (
    <div className="page-container">
      <div style={{ marginBottom: "28px" }}>
        <div style={{ display: "inline-block", background: "#e0e7ff", color: "#3730a3", padding: "4px 12px", borderRadius: "16px", fontSize: "0.8rem", fontWeight: "700", marginBottom: "8px" }}>
          ⚙️ Preferences & Configuration
        </div>
        <h1 style={{ fontSize: "2rem", fontWeight: "800", color: "#0f172a" }}>
          Settings (सेटिंग्ज)
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.95rem" }}>
          Configuration page for Voice STT/TTS settings, API Keys, and Multilingual settings.
        </p>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "16px", color: "#1e293b" }}>
            🎙️ Speech & Voice Engine Configuration
          </h2>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", fontSize: "0.88rem" }}>
            <div>
              <label style={{ display: "block", fontWeight: "600", color: "#334155", marginBottom: "4px" }}>
                Primary STT Engine
              </label>
              <select defaultValue="browser" style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", background: "#f8fafc" }}>
                <option value="browser">Browser Web Speech API (Zero Latency, Native)</option>
                <option value="groq">Groq Cloud Whisper API</option>
                <option value="sarvam">Sarvam Saarika Indic STT</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontWeight: "600", color: "#334155", marginBottom: "4px" }}>
                Primary TTS Engine
              </label>
              <select defaultValue="browser" style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", background: "#f8fafc" }}>
                <option value="browser">Browser SpeechSynthesis (Native Marathi & English)</option>
                <option value="sarvam">Sarvam Bulbul Indic TTS (Marathi)</option>
                <option value="krutrim">Krutrim Indic TTS Cloud</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontWeight: "600", color: "#334155", marginBottom: "4px" }}>
                Fuzzy Match Threshold
              </label>
              <input type="range" min="50" max="95" defaultValue="60" style={{ width: "100%" }} />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#64748b" }}>
                <span>Lenient (50%)</span>
                <span>Default (60%)</span>
                <span>Strict (95%)</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "16px", color: "#1e293b" }}>
            🔑 API Keys & Cloud Connectors
          </h2>
          <p style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "14px" }}>
            Optional API credentials configured in <code>backend/.env</code>. No large local models required.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.85rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span>KRUTRIM API Key</span>
              <span className="badge" style={{ background: "#f1f5f9", color: "#64748b" }}>Optional</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span>GROQ Cloud API Key</span>
              <span className="badge" style={{ background: "#f1f5f9", color: "#64748b" }}>Optional</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span>SARVAM Indic API Key</span>
              <span className="badge" style={{ background: "#f1f5f9", color: "#64748b" }}>Optional</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <span>Local Rule Engine</span>
              <span className="badge" style={{ background: "#dcfce7", color: "#166534" }}>Active (Enabled)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
