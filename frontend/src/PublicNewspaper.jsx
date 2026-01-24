import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function PublicNewspaper({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [newspaper, setNewspaper] = useState(null);
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

  if (!token)
    return (
      <div style={styles.appShell}>
        <div style={styles.appSurface}>
          <div style={styles.panelCard}>Invalid public token.</div>
        </div>
      </div>
    );

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
                  <div style={{ marginTop: 6, color: "var(--muted)" }}>Public newspaper</div>
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
                <h2 style={{ marginTop: 0 }}>{newspaper.title}</h2>
                <p style={styles.mutedText}>{newspaper.description}</p>

            <section style={{ marginTop: 18 }}>
              <h3>Articles</h3>
              {!newspaper.articles || newspaper.articles.length === 0 ? (
                <div style={{ color: "var(--muted)" }}>No articles published.</div>
              ) : (
                <div style={{ display: "grid", gap: 12 }}>
                  {newspaper.articles.map((a) => (
                    <div
                      key={a.id}
                      style={{ ...styles.panelCard, display: "flex", flexDirection: "column", gap: 8 }}
                    >
                      <div style={{ fontWeight: 700 }}>{a.title}</div>
                      <div style={{ color: "var(--muted)", marginTop: 6 }}>
                        {previewText(a.content, 160, "No description")}
                      </div>
                      <div style={{ marginTop: 8 }}>
                        {a.url && (
                          <a
                            href={a.url}
                            target="_blank"
                            rel="noreferrer"
                            style={styles.link}
                          >
                            Read original
                          </a>
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
        </div>
      </div>
    </div>
  );
}

PublicNewspaper.propTypes = {
  apiBase: PropTypes.string,
};
