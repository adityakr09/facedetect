import React, { useEffect, useState, useCallback } from "react";
import { fetchROI } from "../utils/api";

export function ROITable({ sessionId, triggerRefresh }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const result = await fetchROI(sessionId, 0, 100);
      setData(result);
    } catch (_) {
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { load(); }, [load, triggerRefresh]);

  if (!sessionId) return null;

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 4, overflow: "hidden" }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "10px 16px", borderBottom: "1px solid var(--border)",
        background: "var(--bg-panel)",
      }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--accent-dim)", letterSpacing: 3 }}>
          ROI DATABASE
        </span>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          {data && (
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-secondary)" }}>
              {data.total} frames
            </span>
          )}
          <button
            onClick={load}
            style={{
              background: "none", border: "1px solid var(--border-bright)",
              color: "var(--text-secondary)", fontFamily: "var(--font-mono)",
              fontSize: 10, padding: "3px 10px", borderRadius: 2, cursor: "pointer",
              letterSpacing: 1,
            }}
          >
            REFRESH
          </button>
        </div>
      </div>

      <div style={{ maxHeight: 220, overflowY: "auto" }}>
        {loading && (
          <div style={{ padding: 20, textAlign: "center", color: "var(--muted)", fontFamily: "var(--font-mono)", fontSize: 11 }}>
            Loading...
          </div>
        )}
        {data && data.items.length === 0 && (
          <div style={{ padding: 20, textAlign: "center", color: "var(--muted)", fontFamily: "var(--font-mono)", fontSize: 11 }}>
            No frames yet
          </div>
        )}
        {data && data.items.length > 0 && (
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-mono)", fontSize: 11 }}>
            <thead>
              <tr style={{ background: "var(--bg-panel)" }}>
                {["#", "TIME", "FACE", "X", "Y", "W", "H"].map((h) => (
                  <th key={h} style={{ padding: "5px 10px", textAlign: "left", color: "var(--text-secondary)", fontWeight: 400, fontSize: 10, letterSpacing: 1, borderBottom: "1px solid var(--border)" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.items.slice(-30).reverse().map((f) => (
                <tr key={f.frame_index} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "5px 10px", color: "var(--muted)" }}>{f.frame_index}</td>
                  <td style={{ padding: "5px 10px", color: "var(--text-secondary)" }}>
                    {new Date(f.captured_at).toLocaleTimeString()}
                  </td>
                  <td style={{ padding: "5px 10px", color: f.face_detected ? "var(--accent)" : "var(--muted)" }}>
                    {f.face_detected ? "✓" : "—"}
                  </td>
                  {f.roi ? (
                    <>
                      <td style={{ padding: "5px 10px", color: "var(--text-mono)" }}>{f.roi.x}</td>
                      <td style={{ padding: "5px 10px", color: "var(--text-mono)" }}>{f.roi.y}</td>
                      <td style={{ padding: "5px 10px", color: "var(--text-mono)" }}>{f.roi.width}</td>
                      <td style={{ padding: "5px 10px", color: "var(--text-mono)" }}>{f.roi.height}</td>
                    </>
                  ) : (
                    <td colSpan={4} style={{ padding: "5px 10px", color: "var(--muted)" }}>—</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
