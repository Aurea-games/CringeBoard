import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function PublicNewspapers({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loggedIn, setLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState(null);
  const [menuCollapsed, setMenuCollapsed] = useState(false);

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token");
      const e = localStorage.getItem("user_email");
      setLoggedIn(!!token);
      setUserEmail(e || null);
    } catch {
      setLoggedIn(false);
    }
  }, []);

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
    <div style={styles.appShell}>
      <div style={styles.appSurface}>
        <div style={styles.pageLayout}>
          <SideMenu
            collapsed={menuCollapsed}
            onToggleCollapse={() => setMenuCollapsed((prev) => !prev)}
            loggedIn={loggedIn}
          />

          <div style={styles.pageContent}>
            <header style={{ ...styles.headerMain, marginBottom: 20 }}>
              <div style={styles.headerTopRow}>
                <div>
                  <h1 style={{ margin: 0 }}>CringeBoard</h1>
                  <div style={{ marginTop: 6, color: "var(--muted)" }}>
                    Public newspapers
                  </div>
                </div>
                {loggedIn && (
                  <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
                    {userEmail ? `Hi, ${userEmail}` : "Logged in"}
                  </div>
                )}
              </div>
            </header>

            {loading ? (
              <div>Loading…</div>
            ) : error ? (
              <div style={{ color: "#ef4444" }}>{error}</div>
            ) : (
              <div>
                {items.length === 0 ? (
                  <div style={{ color: "var(--muted)" }}>
                    No public newspapers found.
                  </div>
                ) : (
                  <div style={{ display: "grid", gap: 12 }}>
                    {items.map((n) => (
                      <div
                        key={n.id}
                        style={{
                          ...styles.panelCard,
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 700 }}>{n.title}</div>
                          <div style={{ color: "var(--muted)", marginTop: 6 }}>
                            {previewText(n.description, 180, "No description")}
                          </div>
                        </div>
                        <div style={{ display: "flex", gap: 8 }}>
                          {n.public_token ? (
                            <a
                              href={`/public/newspapers/${n.public_token}`}
                              target="_blank"
                              rel="noreferrer"
                              style={styles.link}
                            >
                              Open
                            </a>
                          ) : (
                            <a href={`/newspapers/${n.id}`} style={styles.link}>
                              Open
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

PublicNewspapers.propTypes = {
  apiBase: PropTypes.string,
};
