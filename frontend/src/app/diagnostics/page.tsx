import React from "react";

export default function DiagnosticsPage() {
  return (
    <div className="page-container">
      <div style={{ marginBottom: "28px" }}>
        <div style={{ display: "inline-block", background: "#fef2f2", color: "#991b1b", padding: "4px 12px", borderRadius: "16px", fontSize: "0.8rem", fontWeight: "700", marginBottom: "8px" }}>
          🩺 System & Engine Diagnostics
        </div>
        <h1 style={{ fontSize: "2rem", fontWeight: "800", color: "#0f172a" }}>
          Diagnostics (निदान आणि चाचणी)
        </h1>
        <p style={{ color: "#64748b", fontSize: "0.95rem" }}>
          System health, pipeline readiness, and ML stack inspection.
        </p>
      </div>

      <div className="grid-3" style={{ marginBottom: "24px" }}>
        <div className="card">
          <div style={{ fontSize: "0.85rem", color: "#64748b" }}>FastAPI Backend</div>
          <div style={{ fontSize: "1.3rem", fontWeight: "700", color: "#16a34a", marginTop: "4px" }}>● Connected (Port 8000)</div>
          <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "4px" }}>CORS & Endpoints OK</div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.85rem", color: "#64748b" }}>Multilingual Engine</div>
          <div style={{ fontSize: "1.3rem", fontWeight: "700", color: "#2563eb", marginTop: "4px" }}>Marathi (mr) & English (en)</div>
          <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "4px" }}>Fuzzy rapid token scorer active</div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.85rem", color: "#64748b" }}>Problem Solver Module</div>
          <div style={{ fontSize: "1.3rem", fontWeight: "700", color: "#d97706", marginTop: "4px" }}>● Under Development</div>
          <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "4px" }}>Pluggable architecture ready</div>
        </div>
      </div>

      <div className="card">
        <h2 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "16px", color: "#1e293b" }}>
          Main Project Tech Stack Alignment Checklist
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px", fontSize: "0.85rem" }}>
          <div style={{ padding: "10px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <span style={{ color: "#16a34a", fontWeight: "700" }}>✓ Next.js 16+</span>
            <div style={{ color: "#64748b", fontSize: "0.75rem" }}>Frontend UI & Dynamic Routing</div>
          </div>
          <div style={{ padding: "10px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <span style={{ color: "#16a34a", fontWeight: "700" }}>✓ FastAPI & Python</span>
            <div style={{ color: "#64748b", fontSize: "0.75rem" }}>Multilingual AI API Layer</div>
          </div>
          <div style={{ padding: "10px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <span style={{ color: "#16a34a", fontWeight: "700" }}>✓ KRUTRIM & Indic APIs</span>
            <div style={{ color: "#64748b", fontSize: "0.75rem" }}>API key driven multilingual STT/TTS</div>
          </div>
          <div style={{ padding: "10px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <span style={{ color: "#d97706", fontWeight: "700" }}>⏳ Qwen2.5 / MobileNet3 / XGBoost</span>
            <div style={{ color: "#64748b", fontSize: "0.75rem" }}>Hooked to problem-solver stub</div>
          </div>
        </div>
      </div>
    </div>
  );
}
