import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { ArticleCard } from "./ArticleCard.jsx";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function FavoriteArticle({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  onFavoritesLoaded,
  onFavoriteChange,
}) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loggedIn, setLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState(null);
  const [menuCollapsed, setMenuCollapsed] = useState(false);

  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          throw new Error("Authentication required");
        }
        const headers = { Authorization: `Bearer ${token}` };

        const url = `${apiBase}/v1/me/favorites`;
        const res = await fetch(url, { headers, signal: controller.signal });

        if (!res.ok) throw new Error("Network error");

        const j = await res.json();
        const parsed = Array.isArray(j) ? j : [];
        if (mounted) {
          setArticles(parsed);
          onFavoritesLoaded?.(parsed);
        }
      } catch (e) {
        if (mounted) {
          setError(e.message);
          setArticles([]);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();

    return () => {
      mounted = false;
      controller.abort();
    };
  }, [apiBase, onFavoritesLoaded]);

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
                <h1 style={{ margin: 0 }}>CringeBoard - Favorite Articles</h1>
                {loggedIn && (
                  <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
                    {userEmail ? `Hi, ${userEmail}` : "Logged in"}
                  </div>
                )}
              </div>
            </header>
            <main>
              <section style={{ margin: "20px 0" }}>
                {loading ? (
                  <p>Loading favorite articles…</p>
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
                          No favorite articles found.
                        </div>
                      ) : (
                        articles.map((article) => (
                          <ArticleCard
                            key={article.id || article.title}
                            article={article}
                            apiBase={apiBase}
                            isFavorited
                            onFavoriteToggle={(id, shouldBeFavorite) => {
                              if (!shouldBeFavorite) {
                                setArticles((prev) => prev.filter((a) => a.id !== id));
                              }
                              onFavoriteChange?.(id, shouldBeFavorite);
                            }}
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

FavoriteArticle.propTypes = {
  apiBase: PropTypes.string,
  onFavoritesLoaded: PropTypes.func,
  onFavoriteChange: PropTypes.func,
};
