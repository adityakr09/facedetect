import { useRef, useState, useCallback, useEffect } from "react";
import { startSession, stopSession, pushFrame, makeStreamWsUrl } from "../utils/api";

const CAPTURE_FPS = 10;

export function useStreaming(captureJpeg) {
  const [phase, setPhase] = useState("idle"); // idle | starting | live | stopping | error
  const [sessionId, setSessionId] = useState(null);
  const [stats, setStats] = useState({ fps: 0, frames: 0, faces: 0, lastRoi: null });
  const [streamFrame, setStreamFrame] = useState(null); // latest annotated JPEG object URL
  const [errorMsg, setErrorMsg] = useState(null);

  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  const frameCountRef = useRef(0);
  const faceCountRef = useRef(0);
  const fpsTimerRef = useRef(null);
  const prevFrameUrlRef = useRef(null);

  const cleanup = useCallback(() => {
    clearInterval(intervalRef.current);
    clearInterval(fpsTimerRef.current);
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const start = useCallback(async () => {
    setPhase("starting");
    setErrorMsg(null);
    try {
      const { session_id } = await startSession();
      setSessionId(session_id);

      // ── WebSocket for annotated stream ────────────────────────────────────
      const ws = new WebSocket(makeStreamWsUrl(session_id));
      ws.binaryType = "arraybuffer";
      ws.onmessage = (ev) => {
        if (typeof ev.data === "string") return; // ping
        const blob = new Blob([ev.data], { type: "image/jpeg" });
        const url = URL.createObjectURL(blob);
        setStreamFrame((prev) => {
          if (prevFrameUrlRef.current) URL.revokeObjectURL(prevFrameUrlRef.current);
          prevFrameUrlRef.current = prev;
          return url;
        });
      };
      ws.onerror = () => setErrorMsg("Stream WebSocket error.");
      wsRef.current = ws;

      // ── Capture & push loop ───────────────────────────────────────────────
      intervalRef.current = setInterval(async () => {
        try {
          const blob = await captureJpeg(0.8);
          if (!blob) { console.warn('captureJpeg returned null'); return; }
          const result = await pushFrame(session_id, blob);
          frameCountRef.current += 1;
          if (result.face_detected) faceCountRef.current += 1;
          setStats((s) => ({
            ...s,
            frames: frameCountRef.current,
            faces: faceCountRef.current,
            lastRoi: result.roi ?? s.lastRoi,
          }));
        } catch (_) {
          // tolerate individual frame failures
        }
      }, 1000 / CAPTURE_FPS);

      // FPS counter
      let prev = 0;
      fpsTimerRef.current = setInterval(() => {
        const delta = frameCountRef.current - prev;
        prev = frameCountRef.current;
        setStats((s) => ({ ...s, fps: delta }));
      }, 1000);

      setPhase("live");
    } catch (err) {
      setErrorMsg(err.message);
      setPhase("error");
    }
  }, [captureJpeg]);

  const stop = useCallback(async () => {
    setPhase("stopping");
    cleanup();
    if (sessionId) {
      await stopSession(sessionId).catch(() => {});
    }
    setPhase("idle");
    setSessionId(null);
  }, [cleanup, sessionId]);

  useEffect(() => () => cleanup(), [cleanup]);

  return { phase, sessionId, stats, streamFrame, errorMsg, start, stop };
}
