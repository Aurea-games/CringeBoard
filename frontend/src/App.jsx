import React, { useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import Login from "./Login.jsx";
import Register from "./Register.jsx";
import CreateNewspaper from "./CreateNewspaper.jsx";
import NewspaperList from "./NewspaperList.jsx";
import NewspaperDetail from "./NewspaperDetail.jsx";
import FavoriteArticle from "./FavoriteArticle.jsx";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function Header({ onSearch, onPopularToggle, showPopular }) {
  const [loggedIn, setLoggedIn] = useState(false);
  const [email, setEmail] = useState(null);

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token");
      const e = localStorage.getItem("user_email");
      setLoggedIn(!!token);
      setEmail(e || null);
    } catch (err) {
      console.error("Failed to read auth tokens", err);
      setLoggedIn(false);
    }

    const saved = localStorage.getItem("theme");
    if (saved === "dark") document.body.classList.add("dark");
  }, []);

  function toggleTheme() {
    const isDark = document.body.classList.toggle("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
  }

  function handleLogout() {
    try {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_email");
    } catch (err) {
      console.error("Failed to clear auth tokens", err);
    }
    window.location.href = "/";
  }

  function goLogin() {
    window.location.href = "/login";
  }

  function goRegister() {
    window.location.href = "/register";
  }

  function goCreateNewspaper() {
    window.location.href = "/newspapers/create";
  }

  function goNewspapers() {
    window.location.href = "/newspapers";
  }

  function goFavorites() {
    window.location.href = "/favorites";
  }

  return (
    <header style={styles.header}>
      <h1 style={{ margin: 0 }}>CringeBoard</h1>

      <div style={styles.headerRight}>
        <input
          placeholder="Search articles..."
          aria-label="Search articles"
          onChange={(e) => onSearch(e.target.value)}
          style={styles.searchInput}
        />

        <button
          onClick={onPopularToggle}
          style={{
            ...styles.registerButton,
            background: showPopular ? "#2563eb" : "var(--card-bg)",
            color: showPopular ? "white" : "var(--text)",
          }}
        >
          Popular
        </button>

        <button onClick={toggleTheme} style={styles.registerButton}>
          Toggle theme
        </button>

        {loggedIn ? (
          <>
            <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
              {email ? `Hi, ${email}` : "Logged in"}
            </div>

            <button onClick={goCreateNewspaper} style={styles.createButton}>
              New newspaper
            </button>

            <button onClick={goNewspapers} style={styles.createButton}>
              My newspapers
            </button>

            <button onClick={goFavorites} style={styles.createButton}>
              Favorites
            </button>

            <button onClick={handleLogout} style={styles.logoutButton}>
              Logout
            </button>
          </>
        ) : (
          <>
            <button onClick={goLogin} style={styles.loginButton}>
              Login
            </button>
            <button onClick={goRegister} style={styles.registerButton}>
              Register
            </button>
          </>
        )}
      </div>
    </header>
  );
}

export function ArticleCard({ article, isFavorited = false, onFavoriteToggle }) {
  const [flipped, setFlipped] = useState(false);

  const [favorited, setFavorited] = useState(isFavorited);

  useEffect(() => {
    setFavorited(isFavorited);
  }, [isFavorited]);

  function toggleFlip() {
    setFlipped((v) => !v);
  }

  function handleKey(e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleFlip();
    }
  }

  async function handleFavorite(e) {
    e.stopPropagation();
    const token = localStorage.getItem("access_token");
    if (!token) return alert("Login to favorite articles");

    const previousState = favorited;
    const nextState = !previousState;
    setFavorited(nextState);

    try {
      const headers = { Authorization: `Bearer ${token}` };
      let response;

      if (nextState) {
        headers["Content-Type"] = "application/json";
        response = await fetch(`${apiBase}/v1/me/favorites`, {
          method: "POST",
          headers,
          body: JSON.stringify({ article_id: article.id }),
        });
      } else {
        response = await fetch(`${apiBase}/v1/me/favorites/${article.id}`, {
          method: "DELETE",
          headers,
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to ${nextState ? "favorite" : "unfavorite"} article`);
      }

      if (onFavoriteToggle) onFavoriteToggle(article.id, nextState);
    } catch (err) {
      console.error(err);
      setFavorited(previousState);
      alert("Could not update favorite status");
    }
  }

  const frontStyle = {
    ...styles.card,
    ...styles.front,
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backfaceVisibility: "hidden",
    opacity: flipped ? 0 : 1,
    visibility: flipped ? "hidden" : "visible",
    transition: "opacity 0.25s ease",
  };

  const backStyle = {
    ...styles.card,
    ...styles.back,
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backfaceVisibility: "hidden",
    transform: "rotateY(180deg)",
    opacity: flipped ? 1 : 0,
    visibility: flipped ? "visible" : "hidden",
    transition: "opacity 0.25s ease",
    color: "var(--text)",
  };

  return (
    <div
      style={{ ...styles.flipContainer, width: "100%", display: "block" }}
      onClick={toggleFlip}
      onKeyDown={handleKey}
      role="button"
      tabIndex={0}
      aria-pressed={flipped}
    >
      <div
        style={{
          ...styles.flipper,
          transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
          minHeight: 110,
        }}
      >
        <article style={frontStyle}>
          <h3 style={{ margin: 0, textAlign: "left", color: "var(--text)" }}>
            {article.title}
          </h3>
          <div
            onClick={handleFavorite}
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              fontSize: 20,
              color: favorited ? "#facc15" : "#aaa",
              cursor: "pointer",
            }}
            title={favorited ? "Favorited" : "Add to favorites"}
          >
            ★
          </div>
        </article>

        <article style={backStyle}>
          <p style={{ margin: 0, color: "var(--muted)" }}>
            {previewText(article.content, 160, "No description")}
          </p>

          <div style={{ marginTop: 10 }}>
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noreferrer"
                style={{ color: "#3b82f6" }}
                onClick={(e) => e.stopPropagation()}
              >
                Read original
              </a>
            )}
          </div>
        </article>
      </div>
    </div>
  );
}

ArticleCard.propTypes = {
  article: PropTypes.object.isRequired,
  isFavorited: PropTypes.bool,
  onFavoriteToggle: PropTypes.func,
};

export default function App() {
  const pathname = typeof window !== "undefined" ? window.location.pathname : "";
  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPopular, setShowPopular] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState(() => new Set());

  const syncFavoritesFromList = useCallback((items = []) => {
    const safeItems = Array.isArray(items) ? items : [];
    const ids = safeItems
      .map((item) => item && item.id)
      .filter((id) => id !== undefined && id !== null);
    setFavoriteIds(new Set(ids));
  }, []);

  const handleFavoriteStateChange = useCallback((articleId, shouldBeFavorite) => {
    if (articleId === undefined || articleId === null) return;
    setFavoriteIds((prev) => {
      const next = new Set(prev);
      if (shouldBeFavorite) {
        next.add(articleId);
      } else {
        next.delete(articleId);
      }
      return next;
    });
  }, []);

  const refreshFavoriteIds = useCallback(async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setFavoriteIds(new Set());
        return;
      }

      const response = await fetch(`${apiBase}/v1/me/favorites`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401) {
        setFavoriteIds(new Set());
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to load favorites");
      }

      const data = await response.json();
      syncFavoritesFromList(data);
    } catch (err) {
      console.error("Failed to refresh favorites", err);
    }
  }, [syncFavoritesFromList]);

  useEffect(() => {
    refreshFavoriteIds();
  }, [refreshFavoriteIds]);

  async function loadPopular() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/v1/articles/popular`);
      if (!res.ok) throw new Error("Failed to load popular articles");
      const j = await res.json();
      setArticles(j || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (showPopular) return;
    let mounted = true;
    const controller = new AbortController();
    let timer = null;

    async function load(q) {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem("access_token");
        const headers = token ? { Authorization: `Bearer ${token}` } : {};

        const url = `${apiBase}/v1/articles/${q ? `?q=${encodeURIComponent(q)}` : ""}`;
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
  }, [query, showPopular]);

  useEffect(() => {
    if (showPopular) loadPopular();
  }, [showPopular]);

  if (pathname === "/login") return <Login apiBase={apiBase} />;
  if (pathname === "/register") return <Register apiBase={apiBase} />;
  if (pathname === "/newspapers/create") return <CreateNewspaper apiBase={apiBase} />;
  if (pathname === "/newspapers") return <NewspaperList apiBase={apiBase} />;
  if (/^\/newspapers\/\d+$/.test(pathname)) return <NewspaperDetail apiBase={apiBase} />;
  // FIX: Change the route path to "/favorites" (plural) to match the header and API
  if (pathname === "/favorites") {
    return (
      <FavoriteArticle
        apiBase={apiBase}
        onFavoritesLoaded={syncFavoritesFromList}
        onFavoriteChange={handleFavoriteStateChange}
      />
    );
  }

  return (
    <div
      style={{
        fontFamily: "Inter, system-ui, sans-serif",
        padding: 20,
        color: "var(--text)",
      }}
    >
      <Header onSearch={(q) => {
          setQuery(q);
          setShowPopular(false);
        }}
        onPopularToggle={() => setShowPopular((v) => !v)}
        showPopular={showPopular}
      />

      <main>
        <section style={{ margin: "20px 0" }}>
          {loading ? (
            <p>Loading articles…</p>
          ) : (
            <>
              {error && (
                <div style={{ marginBottom: 12, color: "#ef4444" }}>
                  <strong>Warning:</strong> Failed to fetch articles: {error}.
                  Showing sample data.
                </div>
              )}

              <div style={styles.grid}>
                {articles.length === 0 ? (
                  <div style={{ gridColumn: "1/-1", color: "var(--muted)" }}>
                    No articles found.
                  </div>
                ) : (
                  articles.map((article) => (
                    <ArticleCard
                      key={article.id || article.title}
                      article={article}
                      isFavorited={article.id != null && favoriteIds.has(article.id)}
                      onFavoriteToggle={handleFavoriteStateChange}
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
  );
}

Header.propTypes = {
  onSearch: PropTypes.func,
  onPopularToggle: PropTypes.func,
  showPopular: PropTypes.bool,
};

const styles = {
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  searchInput: {
    padding: "8px 10px",
    borderRadius: 6,
    border: "1px solid var(--border)",
    minWidth: 220,
    background: "var(--card-bg)",
    color: "var(--text)",
  },
  loginButton: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "none",
    background: "#2563eb",
    color: "white",
    cursor: "pointer",
  },
  logoutButton: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "none",
    background: "#ef4444",
    color: "white",
    cursor: "pointer",
  },
  registerButton: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid var(--border)",
    background: "var(--card-bg)",
    color: "var(--text)",
    cursor: "pointer",
  },
  createButton: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid var(--border)",
    background: "#06b6d4",
    color: "white",
    cursor: "pointer",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: "24px 40px",
  },
  flipContainer: {
    perspective: "1000px",
    cursor: "pointer",
    display: "block",
    position: "relative",
    minHeight: 140,
  },
  flipper: {
    position: "relative",
    transformStyle: "preserve-3d",
    transition: "transform 0.6s",
  },
  front: {
    backfaceVisibility: "hidden",
    position: "relative",
    zIndex: 2,
  },
  back: {
    transform: "rotateY(180deg)",
    backfaceVisibility: "hidden",
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
  },
  card: {
    padding: 16,
    borderRadius: 8,
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    border: "1px solid var(--border)",
    background: "var(--card-bg)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    minHeight: 110,
    cursor: "pointer",
    width: "100%",
    color: "var(--text)",
  },
};