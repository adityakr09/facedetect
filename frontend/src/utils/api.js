const BASE = import.meta.env.VITE_API_BASE || "";

export async function startSession() {
  const res = await fetch(`${BASE}/api/v1/feed/start`, { method: "POST" });
  if (!res.ok) throw new Error(`startSession: ${res.status}`);
  return res.json();
}

export async function stopSession(sessionId) {
  await fetch(`${BASE}/api/v1/feed/${sessionId}/stop`, { method: "POST" });
}

export async function pushFrame(sessionId, jpegBlob) {
  const form = new FormData();
  form.append("frame_file", jpegBlob, "frame.jpg");
  const res = await fetch(`${BASE}/api/v1/feed/${sessionId}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `pushFrame: ${res.status}`);
  }
  return res.json();
}

export async function fetchROI(sessionId, skip = 0, limit = 50) {
  const res = await fetch(
    `${BASE}/api/v1/roi/${sessionId}?skip=${skip}&limit=${limit}`
  );
  if (!res.ok) throw new Error(`fetchROI: ${res.status}`);
  return res.json();
}

export function makeStreamWsUrl(sessionId) {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const host = BASE ? new URL(BASE).host : location.host;
  return `${proto}://${host}/api/v1/stream/${sessionId}`;
}
