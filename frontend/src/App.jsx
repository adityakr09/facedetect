import React, { useState, useEffect } from "react";
import { useCamera } from "./hooks/useCamera";
import { useStreaming } from "./hooks/useStreaming";
import { VideoPanel } from "./components/VideoPanel";
import { StatsPanel } from "./components/StatsPanel";
import { ROITable } from "./components/ROITable";

const css = {
  root: {
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    background: "var(--bg-void)",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    height: 52,
    borderBottom: "1px solid var(--border)",
    background: "var(--bg-panel)",
    flexShrink: 0,
  },
  logo: {
    fontFamily: "var(--font-mono)",
    fontSize: 18,
    color: "var(--accent)",
    letterSpacing: 4,
    textTransform: "uppercase",
  },
  logoSub: { color: "var(--muted)", fontSize: 10, letterSpacing: 2 },
  body: {
    flex: 1,
    display: "grid",
    gridTemplateColumns: "1fr 280px",
    gap: 1,
    overflow: "hidden",
  },
  left: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
    padding: 16,
    overflow: "hidden",
  },
  right: {
    borderLeft: "1px solid var(--border)",
    background: "var(--bg-panel)",
    display: "flex",
    flexDirection: "column",
    gap: 12,
    padding: 16,
    overflow: "auto",
  },
  controls: {
    display: "flex",
    gap: 10,
    alignItems: "center",
  },
  btn: (variant) => ({
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    letterSpacing: 2,
    textTransform: "uppercase",
    padding: "8px 20px",
    borderRadius: 2,
    cursor: "pointer",
    border: "none",
    transition: "all 0.15s",
    ...(variant === "start"
      ? { background: "var(--accent)", color: "#000", fontWeight: 700 }
      : variant === "stop"
      ? { background: "var(--warn)", color: "#fff" }
      : { background: "var(--bg-card)", color: "var(--text-secondary)", border: "1px solid var(--border-bright)" }),
  }),
  error: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    color: "var(--warn)",
    padding: "6px 12px",
    background: "rgba(255,107,53,0.1)",
    border: "1px solid rgba(255,107,53,0.3)",
    borderRadius: 2,
  },
};

export default function App() {
  const { videoRef, canvasRef, ready, error: camErr, start: startCam, stop: stopCam, captureJpeg } = useCamera();
  const { phase, sessionId, stats, streamFrame, errorMsg, start: startStream, stop: stopStream } = useStreaming(captureJpeg);
  const [roiRefresh, setRoiRefresh] = useState(0);

  // Periodically trigger ROI table refresh while live
  useEffect(() => {
    if (phase !== "live") return;
    const t = setInterval(() => setRoiRefresh((n) => n + 1), 3000);
    return () => clearInterval(t);
  }, [phase]);

  const handleStart = async () => {
    await startCam();
    await startStream();
  };

  const handleStop = async () => {
    await stopStream();
    stopCam();
    setRoiRefresh((n) => n + 1);
  };

  const canStart = phase === "idle" || phase === "error";
  const canStop = phase === "live" || phase === "starting";

  return (
    <div style={css.root}>
      {/* Header */}
      <header style={css.header}>
        <div>
          <div style={css.logo}>FaceDetect</div>
          <div style={css.logoSub}>Real-Time Face Detection System</div>
        </div>
        <div style={css.controls}>
          {(camErr || errorMsg) && (
            <div style={css.error}>{camErr || errorMsg}</div>
          )}
          <button
            style={css.btn("start")}
            onClick={handleStart}
            disabled={!canStart}
          >
            ▶ Start
          </button>
          <button
            style={css.btn("stop")}
            onClick={handleStop}
            disabled={!canStop}
          >
            ■ Stop
          </button>
        </div>
      </header>

      {/* Body */}
      <div style={css.body}>
        {/* Left: video + ROI table */}
        <div style={css.left}>
          <VideoPanel streamFrame={streamFrame} phase={phase} />
          <ROITable sessionId={sessionId} triggerRefresh={roiRefresh} />
        </div>

        {/* Right: stats + hidden camera elements */}
        <div style={css.right}>
          <StatsPanel stats={stats} sessionId={sessionId} phase={phase} />

          <div style={{ marginTop: "auto", fontSize: 10, color: "var(--muted)", fontFamily: "var(--font-mono)", lineHeight: 1.8 }}>
            <div>● Face detection via dlib HOG</div>
            <div>● No OpenCV used</div>
            <div>● PostgreSQL ROI persistence</div>
            <div>● WebSocket annotated stream</div>
          </div>
        </div>
      </div>

      {/* Hidden camera elements */}
      <video ref={videoRef} style={{ display: "none" }} muted playsInline />
      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
}
