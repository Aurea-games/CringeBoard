import React, { useEffect, useMemo, useState } from "react";
import Login from "./Login.jsx";
import Register from "./Register.jsx";
import CreateNewspaper from "./CreateNewspaper.jsx";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function Header({ onSearch }) {
  const [loggedIn, setLoggedIn] = useState(false);
  const [email, setEmail] = useState(null);

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token");
      const e = localStorage.getItem("user_email");
      setLoggedIn(!!token);
      setEmail(e || null);
    } catch (e) {
      setLoggedIn(false);
    }
  }, []);

  function handleLogout() {
    try {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_email");
    } catch (e) {
      // ignore
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
        {loggedIn ? (
          <>
            <div style={{ fontSize: 13, color: "#333" }}>{email ? `Hi, ${email}` : "Logged in"}</div>
            <button onClick={goCreateNewspaper} style={styles.createButton}>
              New newspaper
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

function ArticleCard({ article }) {
  return (
    <article style={styles.card}>
      <h3 style={{ margin: "0 0 8px 0" }}>{article.title}</h3>
      <p style={{ margin: 0, color: "#444" }}>
        {article.content ? article.content.slice(0, 220) + (article.content.length > 220 ? "…" : "") : "No summary"}
      </p>
      <div style={{ marginTop: 10 }}>
        {article.url && (
          <a href={article.url} target="_blank" rel="noreferrer" style={{ color: "#2563eb" }}>
            Read original
          </a>
        )}
      </div>
      <div style={styles.cardFooter}>
        <small>{article.owner_id ? `owner:${article.owner_id}` : ""}</small>
        <small>{article.created_at ? new Date(article.created_at).toLocaleDateString() : ""}</small>
      </div>
    </article>
  );
}

export default function App() {
  // simple route handling: if the path is /login or /register render the auth pages
  if (typeof window !== "undefined") {
    if (window.location.pathname === "/login") return <Login apiBase={apiBase} />;
    if (window.location.pathname === "/register") return <Register apiBase={apiBase} />;
    if (window.location.pathname === "/newspapers/create") return <CreateNewspaper apiBase={apiBase} />;
  }
  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch articles from server with optional server-side search (debounced)
  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();
    let timer = null;

    async function load(q) {
      setLoading(true);
      setError(null);
      try {
        // prefer the backend aggregator endpoint
        const token = (() => {
          try {
            return localStorage.getItem("access_token");
          } catch (e) {
            return null;
          }
        })();
        const headers = token ? { Authorization: `Bearer ${token}` } : {};

        const url = `${apiBase}/v1/articles/${q ? `?q=${encodeURIComponent(q)}` : ""}`;
        const res = await fetch(url, { headers, signal: controller.signal });
        if (!res.ok) {
          // if backend doesn't provide the v1/articles endpoint, try older paths (preserve query)
          if (res.status === 404) {
            const qparam = q ? `?q=${encodeURIComponent(q)}` : "";
            const alt = await fetch(`${apiBase}/articles${qparam}`, { signal: controller.signal });
            if (alt.ok) {
              const j = await alt.json();
              if (mounted) setArticles(j || []);
            } else {
              const alt2 = await fetch(`${apiBase}/api/articles${qparam}`, { signal: controller.signal });
              if (alt2.ok) {
                const j = await alt2.json();
                if (mounted) setArticles(j || []);
              } else {
                throw new Error(`articles endpoints not found (404)`);
              }
            }
          } else {
            throw new Error(`Network response was not ok: ${res.status}`);
          }
        } else {
          const j = await res.json();
          if (mounted) setArticles(j || []);
        }
      } catch (e) {
        if (mounted) {
          // fallback: provide mock data so the UI can be built/tested without a backend
          setError(e.message);
          setArticles(mockArticles);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    // debounce to avoid hammering server while the user types
    timer = setTimeout(() => load(query), 300);

    return () => {
      mounted = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  // server-side search is used; displayed articles come directly from the server
  const filtered = articles;

  return (
    <div style={{ fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif", padding: 20 }}>
      <Header onSearch={setQuery} />

      <main>
        <section style={{ margin: "20px 0" }}>
          {loading ? (
            <p>Loading articles…</p>
          ) : (
            <>
              {error && (
                <div style={{ marginBottom: 12, color: "#b02a37" }}>
                  <strong>Warning:</strong> Failed to fetch articles from API: {error}. Showing sample data.
                </div>
              )}

              <div style={styles.grid}>
                {filtered.length === 0 ? (
                  <div style={{ gridColumn: "1/-1", color: "#666" }}>No articles found.</div>
                ) : (
                  filtered.map((article) => <ArticleCard key={article.id || article.title} article={article} />)
                )}
              </div>
            </>
          )}
        </section>
      </main>

      <footer style={{ marginTop: 36, color: "#666" }}>
        <small>API base: {apiBase}</small>
      </footer>
    </div>
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
  searchInput: {
    padding: "8px 10px",
    borderRadius: 6,
    border: "1px solid #ddd",
    minWidth: 220,
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
    border: "1px solid #e5e7eb",
    background: "#f8fafc",
    color: "#111827",
    cursor: "pointer",
  },
  createButton: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid #e5e7eb",
    background: "#06b6d4",
    color: "white",
    cursor: "pointer",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: 16,
  },
  card: {
    padding: 16,
    borderRadius: 8,
    boxShadow: "0 1px 3px rgba(16,24,40,0.05)",
    border: "1px solid #eee",
    background: "white",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    minHeight: 110,
  },
  cardFooter: {
    marginTop: 12,
    display: "flex",
    justifyContent: "space-between",
    color: "#888",
    fontSize: 12,
  },
};

const mockArticles = [
  {
    id: "1",
    title: "Welcome to CringeBoard",
    summary: "A playful first article to demonstrate the front page layout.",
    author: "Team",
    published_at: new Date().toISOString(),
  },
  {
    id: "2",
    title: "How to post your first cringe",
    content: "This guide helps you create your first cringe content and share it with the world.",
    author: "Moderator",
    published_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
  {
    id: "3",
    title: "Community guidelines",
    summary: "Be kind, stay safe, and embrace the cringe.",
    author: "CringeBoard",
    published_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
  },
];
