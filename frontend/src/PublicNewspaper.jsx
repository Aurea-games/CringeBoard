import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";

export default function PublicNewspaper({ apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000" }) {
  const [newspaper, setNewspaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const token = (() => {
    try {
      const m = window.location.pathname.match(/^\/public\/newspapers\/(.+)$/);
      return m ? decodeURIComponent(m[1]) : null;
    } catch {
      return null;
    }
  })();

  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!token) return;
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiBase}/v1/public/newspapers/${token}`);
        if (!res.ok) throw new Error(`Failed to load public newspaper (${res.status})`);
        const j = await res.json();
        if (mounted) setNewspaper(j);
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => (mounted = false);
  }, [apiBase, token]);

  if (!token) return <div style={{ padding: 20 }}>Invalid public token.</div>;

  return (
    <div style={{ padding: 20 }}>
      <button onClick={() => (window.location.href = "/")}>← Home</button>
      {loading ? (
        <div>Loading…</div>
      ) : error ? (
        <div style={{ color: "#b02a37" }}>{error}</div>
      ) : (
        <div>
          <h2 style={{ marginTop: 0 }}>{newspaper.title}</h2>
          <p>{newspaper.description}</p>

          <section style={{ marginTop: 18 }}>
            <h3>Articles</h3>
            {(!newspaper.articles || newspaper.articles.length === 0) ? (
              <div style={{ color: "#666" }}>No articles published.</div>
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {newspaper.articles.map((a) => (
                  <div key={a.id} style={{ border: "1px solid #eee", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontWeight: 700 }}>{a.title}</div>
                    <div style={{ color: "#555", marginTop: 6 }}>{previewText(a.content, 160, "No description")}</div>
                    <div style={{ marginTop: 8 }}>
                      {a.url && (
                        <a href={a.url} target="_blank" rel="noreferrer" style={{ color: "#2563eb" }}>Read original</a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

PublicNewspaper.propTypes = {
  apiBase: PropTypes.string,
};
