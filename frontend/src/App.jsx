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
import { ArticleCard } from "./ArticleCard.jsx";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

function resolveApiBase() {
  const envBase =
    import.meta.env.VITE_API_BASE_URL || import.meta.env.REACT_APP_API_BASE_URL;

  // If env points to localhost but the user visits from another host/IP, swap the hostname.
  if (envBase) {
    try {
      const url = new URL(envBase);
      const isLocalEnv = ["localhost", "127.0.0.1", "0.0.0.0"].includes(url.hostname);
      const isBrowserLocal = ["localhost", "127.0.0.1", "0.0.0.0"].includes(
        window.location.hostname,
      );
      if (isLocalEnv && !isBrowserLocal) {
        url.hostname = window.location.hostname;
        return url.toString().replace(/\/$/, "");
      }
      return envBase.replace(/\/$/, "");
    } catch (e) {
      console.warn("Invalid API base URL; falling back to window location", e);
    }
  }

  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const apiBase = resolveApiBase();

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
function Header({ onSearch }) {
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

  return (
    <header style={styles.headerMain}>
      <div style={styles.headerTopRow}>
        <h1 style={{ margin: 0 }}>CringeBoard</h1>
        {loggedIn && (
          <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
            {email ? `Hi, ${email}` : "Logged in"}
          </div>
        )}
      </div>

      <input
        placeholder="Search articles..."
        aria-label="Search articles"
        onChange={(e) => onSearch(e.target.value)}
        style={styles.searchInput}
      />
    </header>
  );
}

export default function App() {
  const pathname = typeof window !== "undefined" ? window.location.pathname : "";
  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPopular, setShowPopular] = useState(false);
  const [menuCollapsed, setMenuCollapsed] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
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

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token");
      setLoggedIn(!!token);
    } catch {
      setLoggedIn(false);
    }
  }, []);

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
    <div style={styles.appShell}>
      <div style={styles.appSurface}>
        <div style={styles.pageLayout}>
          <SideMenu
            collapsed={menuCollapsed}
            onToggleCollapse={() => setMenuCollapsed((prev) => !prev)}
            loggedIn={loggedIn}
            showPopularButton
            showPopular={showPopular}
            onPopularToggle={() => setShowPopular((v) => !v)}
            showNotificationsButton
            notifications={notifications}
            showNotifications={showNotifications}
            onToggleNotifications={handleToggleNotifications}
            unreadCount={unreadCount}
          />

          <div style={styles.pageContent}>
            <Header
              onSearch={(q) => {
                setQuery(q);
                setShowPopular(false);
              }}
            />

            <main style={styles.storeLayout}>
              <aside style={styles.storeSidebar}>
                <div style={styles.sidebarSection}>
                  <div style={styles.sidebarTitle}>Preferred themes</div>
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
                      placeholder="Add a theme"
                      aria-label="Add custom theme"
                      style={styles.themeInput}
                    />
                    <button
                      onClick={handleAddCustomTheme}
                      style={styles.addThemeButton}
                    >
                      Add
                    </button>
                  </div>
                </div>

                <div style={styles.sidebarSection}>
                  <div style={styles.sidebarTitle}>Preferred sources</div>
                  <div style={styles.themeChips}>
                    {sourceSuggestions.map((source) => {
                      const label = source?.name || source;
                      const active = selectedSources.includes(label);
                      return (
                        <button
                          key={label}
                          onClick={() => toggleSourcePreference(label)}
                          style={{
                            ...styles.themeChip,
                            background: active ? "#2563eb" : "var(--card-bg)",
                            color: active ? "white" : "var(--text)",
                            borderColor: active ? "#2563eb" : "var(--border)",
                          }}
                        >
                          {label}
                        </button>
                      );
                    })}
                    {sourceSuggestions.length === 0 && (
                      <span style={{ color: "var(--muted)" }}>
                        No sources loaded yet.
                      </span>
                    )}
                  </div>
                  <div style={styles.customThemeRow}>
                    <input
                      value={customSource}
                      onChange={(e) => setCustomSource(e.target.value)}
                      placeholder="Add a source"
                      aria-label="Add custom source"
                      style={styles.themeInput}
                    />
                    <button
                      onClick={handleAddCustomSource}
                      style={styles.addThemeButton}
                    >
                      Add
                    </button>
                  </div>
                </div>
              </aside>

              <section style={styles.storeContent}>
                <div style={styles.sectionHeader}>
                  <h2 style={{ margin: 0 }}>
                    {showPopular ? "Popular right now" : "Latest updates"}
                  </h2>
                </div>

                <div style={styles.updatesList}>
                  {loading ? (
                    <div style={{ color: "var(--muted)" }}>Loading articles…</div>
                  ) : articles.length === 0 ? (
                    <div style={{ color: "var(--muted)" }}>No articles found.</div>
                  ) : (
                    articles.slice(0, 5).map((article) => (
                      <div key={article.id || article.title} style={styles.updateRow}>
                        <div style={styles.updateIcon} />
                        <div style={styles.updateMeta}>
                          <div style={{ fontWeight: 600 }}>{article.title}</div>
                          <div style={{ color: "var(--muted)", fontSize: 13 }}>
                            {previewText(article.content, 110)}
                          </div>
                          <div style={styles.updateTags}>
                            {extractHostname(article.url) && (
                              <span style={styles.tagPill}>
                                {extractHostname(article.url)}
                              </span>
                            )}
                            <span style={styles.tagPill}>News</span>
                          </div>
                        </div>
                        {article.url && (
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noreferrer"
                            style={styles.updateButton}
                          >
                            Open
                          </a>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </section>
            </main>

            <section style={{ marginTop: 18 }}>
              <h3 style={{ margin: "0 0 8px 0" }}>Browse Articles</h3>
              {error && (
                <div style={{ marginBottom: 12, color: "#ef4444" }}>
                  <strong>Warning:</strong> Failed to fetch articles: {error}.
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
                      apiBase={apiBase}
                      isFavorited={article.id != null && favoriteIds.has(article.id)}
                      onFavoriteToggle={handleFavoriteStateChange}
                    />
                  ))
                )}
              </div>
            </section>

            <footer style={{ marginTop: 24, color: "var(--muted)" }}>
              <small>API base: {apiBase}</small>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
}

Header.propTypes = {
  onSearch: PropTypes.func,
};
