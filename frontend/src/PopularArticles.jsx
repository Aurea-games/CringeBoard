import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";

export default function PopularArticles({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
    <div
      style={{
        fontFamily: "Inter, system-ui, sans-serif",
        padding: 20,
        color: "var(--text)",
      }}
    >
      <Header onSearch={setQuery} />

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
                    <ArticleCard key={article.id || article.title} article={article} />
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

function Header({ onSearch }) {
  const [loggedIn, setLoggedIn] = useState(false);
  const [email, setEmail] = useState(null);

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token");
      const e = localStorage.getItem("user_email");
      setLoggedIn(!!token);
      setEmail(e || null);
    } catch {
      setLoggedIn(false);
    }

    const saved = localStorage.getItem("theme");
    if (saved === "dark") document.body.classList.add("dark");
  }, []);

  function toggleTheme() {
    const isDark = document.body.classList.toggle("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
  }

  function goHome() {
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

  return (
    <header style={styles.header}>
      <h1 style={{ margin: 0 }}>CringeBoard - Popular Articles</h1>

      <div style={styles.headerRight}>
        <input
          placeholder="Search popular articles..."
          aria-label="Search popular articles"
          onChange={(e) => onSearch(e.target.value)}
          style={styles.searchInput}
        />

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

            <button onClick={goHome} style={styles.createButton}>
              Home
            </button>

            <button
              onClick={() => (window.location.href = "/popular")}
              style={styles.createButton}
            >
              Popular Articles
            </button>

            <button
              onClick={() => {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                localStorage.removeItem("user_email");
                window.location.href = "/";
              }}
              style={styles.logoutButton}
            >
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

PopularArticles.propTypes = {
  apiBase: PropTypes.string,
};

Header.propTypes = {
  onSearch: PropTypes.func.isRequired,
};

function ArticleCard({ article }) {
  const [flipped, setFlipped] = useState(false);

  function toggleFlip() {
    setFlipped((v) => !v);
  }

  function handleKey(e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleFlip();
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
