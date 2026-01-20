import React, { useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import Login from "./Login.jsx";
import Register from "./Register.jsx";
import CreateNewspaper from "./CreateNewspaper.jsx";
import NewspaperList from "./NewspaperList.jsx";
import NewspaperDetail from "./NewspaperDetail.jsx";
import FavoriteArticle from "./FavoriteArticle.jsx";
import PublicNewspaper from "./PublicNewspaper.jsx";
import PublicNewspapers from "./PublicNewspapers.jsx";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const suggestedThemes = [
  "AI",
  "Technology",
  "Security",
  "Business",
  "Science",
  "Finance",
  "Politics",
  "Design",
  "DevOps",
  "Health",
  "Education",
];

function extractHostname(url) {
  if (!url) return "";
  try {
    const { hostname } = new URL(url);
    return hostname.replace(/^www\./, "").toLowerCase();
  } catch {
    const match = String(url).match(/^[a-z]+:\/\/(?:www\.)?([^/]+)/i);
    return match ? match[1].toLowerCase() : "";
  }
}

function normalizeSourceLabel(label) {
  return String(label || "")
    .trim()
    .toLowerCase();
}
function Header({
  onSearch,
  onPopularToggle,
  showPopular,
  notifications,
  onToggleNotifications,
  showNotifications,
  unreadCount,
}) {
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

  function goPublicNewspapers() {
    window.location.href = "/public/newspapers";
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

        <div style={styles.notificationWrapper}>
          <button
            onClick={onToggleNotifications}
            style={styles.registerButton}
            aria-label="Notifications"
          >
            Bell
            {unreadCount > 0 && (
              <span style={styles.notificationBadge}>{unreadCount}</span>
            )}
          </button>
          {showNotifications && (
            <div style={styles.notificationDropdown}>
              {notifications.length === 0 ? (
                <div style={{ color: "var(--muted)", fontSize: 13 }}>
                  No notifications
                </div>
              ) : (
                notifications.map((n) => (
                  <div key={n.id} style={styles.notificationItem}>
                    <div style={{ fontWeight: n.is_read ? "normal" : "600" }}>
                      {n.message}
                    </div>
                    <div style={{ color: "var(--muted)", fontSize: 11 }}>
                      {n.created_at || ""}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

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

            <button onClick={goPublicNewspapers} style={styles.createButton}>
              Public newspapers
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
  const [related, setRelated] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);
  const [relatedError, setRelatedError] = useState(null);
  const [showRelated, setShowRelated] = useState(false);

  // Fetch articles from server with optional server-side search (debounced)
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

  async function fetchRelated(e) {
    e.stopPropagation();
    if (!article?.id) return;
    if (related.length > 0) {
      setShowRelated((v) => !v);
      return;
    }
    setRelatedLoading(true);
    setRelatedError(null);
    try {
      const res = await fetch(`${apiBase}/v1/articles/${article.id}/related`);
      if (!res.ok) throw new Error("Failed to load related articles");
      const data = await res.json();
      setRelated(Array.isArray(data) ? data.slice(0, 5) : []);
      setShowRelated(true);
    } catch (err) {
      console.warn(err);
      setRelatedError("Could not load related articles");
    } finally {
      setRelatedLoading(false);
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
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 6,
            }}
          >
            <button
              onClick={fetchRelated}
              style={{ ...styles.pillButton, opacity: article?.id ? 1 : 0.5 }}
              disabled={!article?.id || relatedLoading}
            >
              {relatedLoading ? "Loading…" : showRelated ? "Hide similar" : "Similar"}
            </button>
          </div>
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

          {showRelated && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Similar articles</div>
              {relatedError && (
                <div style={{ color: "#ef4444", fontSize: 13 }}>{relatedError}</div>
              )}
              {related.length === 0 && !relatedError && !relatedLoading && (
                <div style={{ color: "var(--muted)", fontSize: 13 }}>
                  No related articles found.
                </div>
              )}
              <ul style={{ paddingLeft: 16, margin: 0, display: "grid", gap: 6 }}>
                {related.map((item) => (
                  <li key={item.id || item.title} style={{ lineHeight: 1.3 }}>
                    <a
                      href={item.url || "#"}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      style={{ color: "#2563eb" }}
                    >
                      {item.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

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
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedThemes, setSelectedThemes] = useState(() => {
    try {
      const raw = localStorage.getItem("preferred_themes");
      const parsed = JSON.parse(raw || "null");
      if (Array.isArray(parsed)) return parsed;
    } catch (err) {
      console.warn("Failed to load preferred themes", err);
    }
    return [];
  });
  const [customTheme, setCustomTheme] = useState("");
  const [selectedSources, setSelectedSources] = useState(() => {
    try {
      const raw = localStorage.getItem("preferred_sources");
      const parsed = JSON.parse(raw || "null");
      if (Array.isArray(parsed)) return parsed;
    } catch (err) {
      console.warn("Failed to load preferred sources", err);
    }
    return [];
  });
  const [customSource, setCustomSource] = useState("");
  const [sourceSuggestions, setSourceSuggestions] = useState([]);

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

  const fetchNotifications = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setNotifications([]);
      return;
    }
    try {
      const res = await fetch(`${apiBase}/v1/me/notifications`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load notifications");
      const data = await res.json();
      if (Array.isArray(data)) setNotifications(data);
    } catch (err) {
      console.warn("Failed to fetch notifications", err);
    }
  }, []);

  useEffect(() => {
    refreshFavoriteIds();
  }, [refreshFavoriteIds]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  useEffect(() => {
    const controller = new AbortController();
    async function loadSourceSuggestions() {
      try {
        const token = localStorage.getItem("access_token");
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const res = await fetch(`${apiBase}/v1/sources`, {
          headers,
          signal: controller.signal,
        });
        if (!res.ok) throw new Error("Failed to load sources");
        const data = await res.json();
        if (!Array.isArray(data)) return;
        setSourceSuggestions(data);

        // Merge already-followed sources into selected list so UI matches backend follow state.
        const followedNames = data
          .filter((src) => src && src.is_followed)
          .map((src) => src.name)
          .filter(Boolean)
          .map((name) => String(name).trim());
        if (followedNames.length > 0) {
          setSelectedSources((prev) => {
            const existing = new Set(prev);
            followedNames.forEach((n) => existing.add(n));
            return Array.from(existing);
          });
        }
      } catch (err) {
        console.warn("Could not load sources", err);
      }
    }

    loadSourceSuggestions();
    return () => controller.abort();
  }, []);

  const prioritizeArticles = useCallback(
    (items) => {
      const list = Array.isArray(items) ? items : [];
      const keywords = selectedThemes
        .map((t) =>
          String(t || "")
            .trim()
            .toLowerCase(),
        )
        .filter(Boolean);
      const sourceFilters = selectedSources
        .map((s) =>
          String(s || "")
            .trim()
            .toLowerCase(),
        )
        .filter(Boolean);
      if (keywords.length === 0 && sourceFilters.length === 0) return list;

      const scoreArticle = (article) => {
        const title = String(article?.title || "").toLowerCase();
        const content = String(article?.content || "").toLowerCase();
        const host = extractHostname(article?.url);
        const themeScore = keywords.reduce((score, keyword) => {
          let next = score;
          if (title.includes(keyword)) next += 3;
          if (content.includes(keyword)) next += 2;
          return next;
        }, 0);

        const sourceScore = sourceFilters.reduce((score, source) => {
          let next = score;
          if (host && host.includes(source)) next += 5;
          if (title.includes(source)) next += 2;
          return next;
        }, 0);

        return themeScore + sourceScore;
      };

      return list
        .map((article, idx) => ({ article, idx, score: scoreArticle(article) }))
        .sort((a, b) => {
          if (b.score !== a.score) return b.score - a.score;
          return a.idx - b.idx;
        })
        .map((entry) => entry.article);
    },
    [selectedSources, selectedThemes],
  );

  useEffect(() => {
    try {
      localStorage.setItem("preferred_themes", JSON.stringify(selectedThemes));
    } catch (err) {
      console.warn("Failed to persist preferred themes", err);
    }
    setArticles((prev) => prioritizeArticles(prev));
  }, [prioritizeArticles, selectedThemes]);

  useEffect(() => {
    try {
      localStorage.setItem("preferred_sources", JSON.stringify(selectedSources));
    } catch (err) {
      console.warn("Failed to persist preferred sources", err);
    }
    setArticles((prev) => prioritizeArticles(prev));
  }, [prioritizeArticles, selectedSources]);

  function toggleThemePreference(themeLabel) {
    const label = String(themeLabel || "").trim();
    if (!label) return;
    setSelectedThemes((prev) => {
      if (prev.includes(label)) return prev.filter((t) => t !== label);
      return [...prev, label];
    });
  }

  function handleAddCustomTheme() {
    const label = customTheme.trim();
    if (!label) return;
    toggleThemePreference(label);
    setCustomTheme("");
  }

  function findSourceByName(label) {
    const normalized = normalizeSourceLabel(label);
    return sourceSuggestions.find(
      (src) => normalizeSourceLabel(src?.name) === normalized,
    );
  }

  async function followSourceIfPossible(sourceId) {
    if (!sourceId) return;
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Login to receive notifications from this source");
      return;
    }
    try {
      const res = await fetch(`${apiBase}/v1/sources/${sourceId}/follow`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to follow source");
    } catch (err) {
      console.warn(err);
      alert("Could not follow source");
    }
  }

  async function unfollowSourceIfPossible(sourceId) {
    if (!sourceId) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/v1/sources/${sourceId}/follow`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to unfollow source");
    } catch (err) {
      console.warn(err);
    }
  }

  function toggleSourcePreference(sourceLabel) {
    const label = String(sourceLabel || "").trim();
    if (!label) return;
    const match = findSourceByName(label);

    setSelectedSources((prev) => {
      if (prev.includes(label)) {
        if (match?.id) unfollowSourceIfPossible(match.id);
        return prev.filter((s) => s !== label);
      }
      if (match?.id) followSourceIfPossible(match.id);
      return [...prev, label];
    });
  }

  function handleAddCustomSource() {
    const label = customSource.trim();
    if (!label) return;
    toggleSourcePreference(label);
    setCustomSource("");
  }

  async function markAllNotificationsRead() {
    const unread = notifications.filter((n) => n && !n.is_read);
    if (unread.length === 0) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      await Promise.all(
        unread.map((n) =>
          fetch(`${apiBase}/v1/me/notifications/${n.id}/read`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
          }),
        ),
      );
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.warn("Failed to mark notifications read", err);
    }
  }

  const loadPopular = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/v1/articles/popular`);
      if (!res.ok) throw new Error("Failed to load popular articles");
      const j = await res.json();
      setArticles(prioritizeArticles(j));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [prioritizeArticles]);

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
        if (mounted) setArticles(prioritizeArticles(j));
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
  }, [prioritizeArticles, query, showPopular]);

  useEffect(() => {
    if (showPopular) loadPopular();
  }, [showPopular, loadPopular]);

  const unreadCount = notifications.filter((n) => n && !n.is_read).length;

  async function handleToggleNotifications() {
    const next = !showNotifications;
    setShowNotifications(next);
    if (next) {
      await markAllNotificationsRead();
    }
  }

  if (pathname === "/login") return <Login apiBase={apiBase} />;
  if (pathname === "/register") return <Register apiBase={apiBase} />;
  if (pathname === "/newspapers/create") return <CreateNewspaper apiBase={apiBase} />;
  if (pathname === "/newspapers") return <NewspaperList apiBase={apiBase} />;
  if (/^\/newspapers\/\d+$/.test(pathname))
    return <NewspaperDetail apiBase={apiBase} />;
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
  if (pathname === "/public/newspapers") {
    return <PublicNewspapers apiBase={apiBase} />;
  }

  const publicMatch =
    typeof window !== "undefined"
      ? window.location.pathname.match(/^\/public\/newspapers\/(.+)$/)
      : null;
  if (publicMatch) return <PublicNewspaper apiBase={apiBase} />;

  return (
    <div
      style={{
        fontFamily: "Inter, system-ui, sans-serif",
        padding: 20,
        color: "var(--text)",
      }}
    >
      <Header
        onSearch={(q) => {
          setQuery(q);
          setShowPopular(false);
        }}
        onPopularToggle={() => setShowPopular((v) => !v)}
        showPopular={showPopular}
        notifications={notifications}
        onToggleNotifications={handleToggleNotifications}
        showNotifications={showNotifications}
        unreadCount={unreadCount}
      />

      <main>
        <section style={styles.preferencesPanel}>
          <div
            style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}
          >
            <h2 style={{ margin: 0, fontSize: 18 }}>Preferred themes</h2>
            <span style={{ color: "var(--muted)" }}>
              Pick topics to prioritize matching articles in your feed.
            </span>
          </div>

          <div style={styles.themeChips}>
            {suggestedThemes.map((theme) => {
              const active = selectedThemes.includes(theme);
              return (
                <button
                  key={theme}
                  onClick={() => toggleThemePreference(theme)}
                  style={{
                    ...styles.themeChip,
                    background: active ? "#2563eb" : "var(--card-bg)",
                    color: active ? "white" : "var(--text)",
                    borderColor: active ? "#2563eb" : "var(--border)",
                  }}
                >
                  {theme}
                </button>
              );
            })}
          </div>

          <div style={styles.customThemeRow}>
            <input
              value={customTheme}
              onChange={(e) => setCustomTheme(e.target.value)}
              placeholder="Add your own theme (e.g. Climate)"
              aria-label="Add custom theme"
              style={styles.themeInput}
            />
            <button onClick={handleAddCustomTheme} style={styles.addThemeButton}>
              Add
            </button>
            {selectedThemes.length > 0 && (
              <button
                onClick={() => setSelectedThemes([])}
                style={{
                  ...styles.addThemeButton,
                  background: "var(--card-bg)",
                  color: "var(--text)",
                  border: "1px solid var(--border)",
                }}
              >
                Clear
              </button>
            )}
          </div>

          {selectedThemes.length > 0 && (
            <div style={{ color: "var(--muted)", fontSize: 13 }}>
              Prioritizing articles matching: {selectedThemes.join(", ")}
            </div>
          )}
        </section>

        <section style={styles.preferencesPanel}>
          <div
            style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}
          >
            <h2 style={{ margin: 0, fontSize: 18 }}>Preferred sources</h2>
            <span style={{ color: "var(--muted)" }}>
              Boost articles coming from these domains or names.
            </span>
          </div>

          <div style={styles.themeChips}>
            {sourceSuggestions.map((source) => {
              const active = selectedSources.includes(source);
              return (
                <button
                  key={source}
                  onClick={() => toggleSourcePreference(source)}
                  style={{
                    ...styles.themeChip,
                    background: active ? "#2563eb" : "var(--card-bg)",
                    color: active ? "white" : "var(--text)",
                    borderColor: active ? "#2563eb" : "var(--border)",
                  }}
                >
                  {source}
                </button>
              );
            })}
            {sourceSuggestions.length === 0 && (
              <span style={{ color: "var(--muted)" }}>
                No sources loaded yet. Add your own below.
              </span>
            )}
          </div>

          <div style={styles.customThemeRow}>
            <input
              value={customSource}
              onChange={(e) => setCustomSource(e.target.value)}
              placeholder="Add a domain or source name (e.g. nytimes.com)"
              aria-label="Add custom source"
              style={styles.themeInput}
            />
            <button onClick={handleAddCustomSource} style={styles.addThemeButton}>
              Add
            </button>
            {selectedSources.length > 0 && (
              <button
                onClick={() => setSelectedSources([])}
                style={{
                  ...styles.addThemeButton,
                  background: "var(--card-bg)",
                  color: "var(--text)",
                  border: "1px solid var(--border)",
                }}
              >
                Clear
              </button>
            )}
          </div>

          {selectedSources.length > 0 && (
            <div style={{ color: "var(--muted)", fontSize: 13 }}>
              Prioritizing articles from: {selectedSources.join(", ")}
            </div>
          )}
        </section>

        <section style={{ margin: "20px 0" }}>
          {loading ? (
            <p>Loading articles…</p>
          ) : (
            <>
              {error && (
                <div style={{ marginBottom: 12, color: "#ef4444" }}>
                  <strong>Warning:</strong> Failed to fetch articles: {error}. Showing
                  sample data.
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
  notifications: PropTypes.array,
  onToggleNotifications: PropTypes.func,
  showNotifications: PropTypes.bool,
  unreadCount: PropTypes.number,
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
  preferencesPanel: {
    marginTop: 18,
    marginBottom: 16,
    padding: 16,
    border: "1px solid var(--border)",
    borderRadius: 10,
    background: "var(--card-bg)",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  themeChips: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
  },
  themeChip: {
    padding: "8px 12px",
    borderRadius: 999,
    border: "1px solid var(--border)",
    background: "var(--card-bg)",
    cursor: "pointer",
    fontSize: 14,
  },
  customThemeRow: {
    display: "flex",
    gap: 8,
    alignItems: "center",
    flexWrap: "wrap",
  },
  themeInput: {
    padding: "8px 10px",
    borderRadius: 6,
    border: "1px solid var(--border)",
    background: "var(--card-bg)",
    color: "var(--text)",
    minWidth: 240,
  },
  addThemeButton: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "none",
    background: "#16a34a",
    color: "white",
    cursor: "pointer",
  },
  notificationWrapper: {
    position: "relative",
    display: "inline-block",
  },
  notificationBadge: {
    marginLeft: 6,
    background: "#ef4444",
    color: "white",
    borderRadius: 999,
    padding: "0 6px",
    fontSize: 12,
  },
  notificationDropdown: {
    position: "absolute",
    top: "110%",
    right: 0,
    width: 260,
    maxHeight: 320,
    overflowY: "auto",
    background: "var(--card-bg)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: 10,
    boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
    zIndex: 20,
  },
  notificationItem: {
    padding: "6px 0",
    borderBottom: "1px solid var(--border)",
  },
  pillButton: {
    padding: "6px 10px",
    borderRadius: 999,
    border: "1px solid var(--border)",
    background: "var(--card-bg)",
    color: "var(--text)",
    cursor: "pointer",
    fontSize: 13,
  },
};
