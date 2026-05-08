import React from "react";

const s = {
  wrap: {
    position: "relative",
    width: "100%",
    aspectRatio: "4/3",
    background: "#000",
    borderRadius: 4,
    overflow: "hidden",
    border: "1px solid var(--border)",
  },
  img: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
    display: "block",
  },
  placeholder: {
    position: "absolute",
    inset: 0,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    color: "var(--muted)",
    fontFamily: "var(--font-mono)",
    fontSize: 12,
  },
  camIcon: { fontSize: 40, opacity: 0.3 },
  corner: {
    position: "absolute",
    width: 16,
    height: 16,
    borderColor: "var(--accent)",
    borderStyle: "solid",
    opacity: 0.6,
  },
  badge: {
    position: "absolute",
    top: 12,
    left: 12,
    fontFamily: "var(--font-mono)",
    fontSize: 10,
    padding: "2px 8px",
    borderRadius: 2,
    letterSpacing: 2,
    textTransform: "uppercase",
  },
};

export function VideoPanel({ streamFrame, phase }) {
  const live = phase === "live";

  return (
    <div style={s.wrap}>
      {streamFrame ? (
        <img src={streamFrame} alt="Annotated stream" style={s.img} />
      ) : (
        <div style={s.placeholder}>
          <span style={s.camIcon}>◉</span>
          <span>{phase === "starting" ? "Initialising..." : "No signal"}</span>
        </div>
      )}

      {/* Corner decorations */}
      {[
        { top: 0, left: 0, borderWidth: "2px 0 0 2px" },
        { top: 0, right: 0, borderWidth: "2px 2px 0 0" },
        { bottom: 0, left: 0, borderWidth: "0 0 2px 2px" },
        { bottom: 0, right: 0, borderWidth: "0 2px 2px 0" },
      ].map((pos, i) => (
        <div key={i} style={{ ...s.corner, ...pos }} />
      ))}

      {/* Live badge */}
      <div
        style={{
          ...s.badge,
          background: live ? "var(--accent)" : "var(--muted)",
          color: live ? "#000" : "var(--text-secondary)",
        }}
      >
        {live ? "● LIVE" : phase === "starting" ? "INIT" : "IDLE"}
      </div>
    </div>
  );
}
