import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { ArticleCard } from "./ArticleCard.jsx";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function PopularArticles({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState([]);
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
    const controller = new AbortController();
    let timer = null;

    async function load(q) {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem("access_token");
        const headers = token ? { Authorization: `Bearer ${token}` } : {};

        const url = `${apiBase}/v1/articles/popular${q ? `?q=${encodeURIComponent(q)}` : ""}`;
        const res = await fetch(url, { headers, signal: controller.signal });

        if (!res.ok) throw new Error("Network error");

        const j = await res.json();
        if (mounted) setArticles(j || []);
      } catch (e) {
        if (mounted) {
          setError(e.message);
          setArticles([]);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    timer = setTimeout(() => load(query), 300);

    return () => {
      mounted = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [apiBase, query]);

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
                <h1 style={{ margin: 0 }}>CringeBoard - Popular Articles</h1>
                {loggedIn && (
                  <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
                    {userEmail ? `Hi, ${userEmail}` : "Logged in"}
                  </div>
                )}
              </div>
              <input
                placeholder="Search popular articles..."
                aria-label="Search popular articles"
                onChange={(e) => setQuery(e.target.value)}
                style={styles.searchInput}
              />
            </header>

            <main>
              <section style={{ margin: "20px 0" }}>
                {loading ? (
                  <p>Loading popular articles…</p>
                ) : (
                  <>
                    {error && (
                      <div style={{ marginBottom: 12, color: "#ef4444" }}>
                        <strong>Warning:</strong> Failed to fetch articles: {error}.
                      </div>
                    )}

                    <div style={styles.grid}>
                      {articles.length === 0 ? (
                        <div style={{ gridColumn: "1/-1", color: "var(--muted)" }}>
                          No popular articles found.
                        </div>
                      ) : (
                        articles.map((article) => (
                          <ArticleCard
                            key={article.id || article.title}
                            article={article}
                            apiBase={apiBase}
                          />
                        ))
                      )}
                    </div>
                  </>
                )}
              </section>
            </main>

            <footer style={{ marginTop: 36, color: "var(--muted)" }}>
              <small>API base: {apiBase}</small>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
}

PopularArticles.propTypes = {
  apiBase: PropTypes.string,
};

