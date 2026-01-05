import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";

export default function PublicNewspapers({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiBase}/v1/newspapers`);
        if (!res.ok) throw new Error(`Failed to load newspapers (${res.status})`);
        const j = await res.json();
        const pubs = Array.isArray(j) ? j.filter((n) => n && n.is_public) : [];
        if (mounted) setItems(pubs);
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => (mounted = false);
  }, [apiBase]);

  return (
    <div style={{ padding: 20 }}>
      <button onClick={() => (window.location.href = "/")} style={{ marginBottom: 12 }}>
        ← Home
      </button>
      <h2 style={{ marginTop: 0 }}>Public Newspapers</h2>

      {loading ? (
        <div>Loading…</div>
      ) : error ? (
        <div style={{ color: "#b02a37" }}>{error}</div>
      ) : (
        <div>
          {items.length === 0 ? (
            <div style={{ color: "#666" }}>No public newspapers found.</div>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              {items.map((n) => (
                <div
                  key={n.id}
                  style={{ border: "1px solid #eee", padding: 12, borderRadius: 8 }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700 }}>{n.title}</div>
                      <div style={{ color: "#555", marginTop: 6 }}>
                        {previewText(n.description, 180, "No description")}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                      {n.public_token ? (
                        <a
                          href={`/public/newspapers/${n.public_token}`}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: "#2563eb" }}
                        >
                          Open
                        </a>
                      ) : (
                        <a href={`/newspapers/${n.id}`} style={{ color: "#2563eb" }}>
                          Open
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

PublicNewspapers.propTypes = {
  apiBase: PropTypes.string,
};
