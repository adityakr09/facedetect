import React from "react";

function Row({ label, value, accent }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
      <span style={{ color: "var(--text-secondary)", fontSize: 11, fontFamily: "var(--font-mono)", letterSpacing: 1 }}>
        {label}
      </span>
      <span style={{
        fontFamily: "var(--font-mono)",
        fontSize: 13,
        color: accent ? "var(--accent)" : "var(--text-mono)",
        fontWeight: accent ? 700 : 400,
      }}>
        {value}
      </span>
    </div>
  );
}

export function StatsPanel({ stats, sessionId, phase }) {
  const { fps, frames, faces, lastRoi } = stats;

  return (
    <div style={{
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: 4,
      padding: 16,
    }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--accent-dim)", letterSpacing: 3, marginBottom: 12, textTransform: "uppercase" }}>
        System Stats
      </div>

      <Row label="STATUS" value={phase.toUpperCase()} accent={phase === "live"} />
      <Row label="FPS" value={fps} />
      <Row label="FRAMES" value={frames.toLocaleString()} />
      <Row label="DETECTIONS" value={faces.toLocaleString()} accent={faces > 0} />
      <Row label="DETECT RATE" value={frames > 0 ? `${((faces / frames) * 100).toFixed(1)}%` : "—"} />

      {lastRoi && (
        <>
          <div style={{ marginTop: 12, marginBottom: 6, fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--accent-dim)", letterSpacing: 3 }}>
            Last ROI
          </div>
          <Row label="X" value={lastRoi.x} />
          <Row label="Y" value={lastRoi.y} />
          <Row label="W" value={lastRoi.width} />
          <Row label="H" value={lastRoi.height} />
        </>
      )}

      {sessionId && (
        <div style={{ marginTop: 12, fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)", wordBreak: "break-all" }}>
          SID: {sessionId}
        </div>
      )}
    </div>
  );
}
