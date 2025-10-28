import React, { useEffect, useState } from "react";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [status, setStatus] = useState("loading...");

  useEffect(() => {
    fetch(`${apiBase}/healthz`)
      .then(async (r) => {
        if (r.ok) {
          const j = await r.json();
          setStatus(`API: ${j.status}`);
        } else {
          setStatus(`API error: ${r.status}`);
        }
      })
      .catch((e) => setStatus(`API fetch failed: ${e.message}`));
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: 24 }}>
      <h1>CringeBoard</h1>
      <p>{status}</p>
      <small>API base: {apiBase}</small>
    </div>
  );
}
