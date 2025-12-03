import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import { ArticleCard } from "./App.jsx";

export default function FavoriteArticle({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
}) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

        const url = `${apiBase}/v1/articles/favorite`;
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

    load();

    return () => {
      mounted = false;
      controller.abort();
    };
  }, []);

  return (
    <div
      style={{
        fontFamily: "Inter, system-ui, sans-serif",
        padding: 20,
        color: "var(--text)",
      }}
    >
      <Header />

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
                      onFavoriteToggle={(id) => setArticles(prev => prev.filter(a => a.id !== id))}
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

function Header() {
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

    // Load theme
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
      <h1 style={{ margin: 0 }}>CringeBoard - Favorite Articles</h1>

      <div style={styles.headerRight}>
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
              onClick={() => (window.location.href = "/favorite")}
              style={{ ...styles.createButton, background: "#facc15", color: "black" }}
            >
              Favorites
            </button>

            <button onClick={() => { localStorage.removeItem("access_token"); localStorage.removeItem("refresh_token"); localStorage.removeItem("user_email"); window.location.href = "/"; }} style={styles.logoutButton}>
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
};

Header.propTypes = {};