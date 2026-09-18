"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { DEMO_ROUTES } from "../lib/routesConfig";

export const Navbar: React.FC = () => {
  const pathname = usePathname();

  return (
    <header style={{
      background: "#ffffff",
      borderBottom: "1px solid #e2e8f0",
      position: "sticky",
      top: 0,
      zIndex: 50,
      boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)"
    }}>
      <div style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "0 20px",
        height: "64px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
      }}>
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            background: "linear-gradient(135deg, #2563eb, #7c3aed)",
            color: "#ffffff",
            width: "36px",
            height: "36px",
            borderRadius: "8px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "800",
            fontSize: "1.1rem"
          }}>
            🎙️
          </div>
          <div>
            <div style={{ fontWeight: "700", fontSize: "1rem", color: "#0f172a" }}>
              VoiceNav AI
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
              English & मराठी Multilingual Assistant
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {DEMO_ROUTES.map((route) => {
            const isActive = pathname === route.path;
            return (
              <Link
                key={route.route_id}
                href={route.path}
                style={{
                  padding: "8px 14px",
                  borderRadius: "6px",
                  fontSize: "0.85rem",
                  fontWeight: isActive ? "700" : "500",
                  color: isActive ? "#2563eb" : "#475569",
                  background: isActive ? "#eff6ff" : "transparent",
                  textDecoration: "none",
                  transition: "all 0.15s ease",
                  border: isActive ? "1px solid #bfdbfe" : "1px solid transparent"
                }}
              >
                {route.name_en} <span style={{ fontSize: "0.75rem", opacity: 0.75 }}>({route.name_mr})</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
