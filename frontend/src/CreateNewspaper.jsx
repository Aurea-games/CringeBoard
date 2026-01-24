import React, { useEffect, useState, useCallback } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function CreateNewspaper({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [newspaper, setNewspaper] = useState(null);

  // attached / current articles for this newspaper
  const [attached, setAttached] = useState([]);
  const [loadingAttached, setLoadingAttached] = useState(false);

  // search existing articles to attach
  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // create new article within newspaper
  const [aTitle, setATitle] = useState("");
  const [aContent, setAContent] = useState("");
  const [aUrl, setAUrl] = useState("");
  const [creatingArticle, setCreatingArticle] = useState(false);
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

  function authHeaders() {
    try {
      const token = localStorage.getItem("access_token");
      return token
        ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
        : { "Content-Type": "application/json" };
    } catch {
      return { "Content-Type": "application/json" };
    }
  }

  async function handleCreateNewspaper(e) {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title, description }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.detail || JSON.stringify(body));
        return;
      }
      setNewspaper(body);
      // load attached articles (should be empty)
      await loadAttached(body.id);
    } catch (e) {
      setError(e.message);
    } finally {
      setCreating(false);
    }
  }

  const loadAttached = useCallback(
    async (id) => {
      setLoadingAttached(true);
      try {
        const res = await fetch(`${apiBase}/v1/newspapers/${id}/articles`, {
          headers: authHeaders(),
        });
        if (!res.ok) return;
        const j = await res.json();
        setAttached(j || []);
      } catch {
        // ignore
      } finally {
        setLoadingAttached(false);
      }
    },
    [apiBase],
  );

  // search existing articles (debounced)
  useEffect(() => {
    const t = setTimeout(async () => {
      if (!searchQ) {
        setSearchResults([]);
        setSearching(false);
        return;
      }
      setSearching(true);
      try {
        const res = await fetch(
          `${apiBase}/v1/articles/?q=${encodeURIComponent(searchQ)}`,
          { headers: authHeaders() },
        );
        if (!res.ok) {
          setSearchResults([]);
        } else {
          const j = await res.json();
          setSearchResults(j || []);
        }
      } catch (e) {
        console.error("Failed to search articles:", e);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [searchQ, apiBase]);

  async function attachArticle(articleId) {
    if (!newspaper) return;
    try {
      const res = await fetch(
        `${apiBase}/v1/newspapers/${newspaper.id}/articles/${articleId}`,
        {
          method: "POST",
          headers: authHeaders(),
        },
      );
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        setError(b.detail || `Failed to attach article (${res.status})`);
        return;
      }
      const j = await res.json();
      // add to attached list if not present
      setAttached((prev) => {
        if (prev.find((a) => a.id === j.id)) return prev;
        return [j, ...prev];
      });
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleCreateArticle(e) {
    e.preventDefault();
    if (!newspaper) return;
    setCreatingArticle(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${newspaper.id}/articles`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title: aTitle, content: aContent, url: aUrl }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.detail || JSON.stringify(body));
        return;
      }
      setAttached((prev) => [body, ...prev]);
      // clear form
      setATitle("");
      setAContent("");
      setAUrl("");
    } catch (e) {
      setError(e.message);
    } finally {
      setCreatingArticle(false);
    }
  }

  // if newspaper created, load its attached articles
  useEffect(() => {
    if (newspaper) loadAttached(newspaper.id);
  }, [newspaper, loadAttached]);

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
                    Create a newspaper
                  </div>
                </div>
                {loggedIn && (
                  <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
                    {userEmail ? `Hi, ${userEmail}` : "Logged in"}
                  </div>
                )}
              </div>
            </header>

            {!newspaper ? (
              <form
                onSubmit={handleCreateNewspaper}
                style={{ ...styles.formCard, maxWidth: 720, marginBottom: 24 }}
              >
          <label style={{ display: "block", marginBottom: 12 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Title</div>
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{ ...styles.textInput, maxWidth: 520 }}
            />
          </label>
          <label style={{ display: "block", marginBottom: 12 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Description</div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              style={{ ...styles.textArea, maxWidth: 520 }}
            />
          </label>
          {error && <div style={{ color: "#ef4444", marginBottom: 12 }}>{error}</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="submit"
              disabled={creating}
              style={styles.createButton}
            >
              {creating ? "Creating…" : "Create newspaper"}
            </button>
            <button
              type="button"
              onClick={() => (window.location.href = "/")}
              style={styles.registerButton}
            >
              Cancel
            </button>
          </div>
            </form>
          ) : (
            <div style={{ maxWidth: 980 }}>
              <h3 style={{ marginTop: 0 }}>{newspaper.title}</h3>
          <p style={styles.mutedText}>{newspaper.description}</p>

          <section style={{ marginTop: 18 }}>
            <h4>Attach existing articles</h4>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <input
                placeholder="Search articles to attach"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                style={{ ...styles.textInput, flex: 1 }}
              />
              <div style={{ alignSelf: "center", color: "var(--muted)" }}>
                {searching ? "Searching…" : ""}
              </div>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
                gap: 12,
              }}
            >
              {searchResults.map((a) => (
                <div
                  key={a.id}
                  style={{ ...styles.panelCard, display: "flex", flexDirection: "column", gap: 8 }}
                >
                  <div style={{ fontWeight: 600 }}>{a.title}</div>
                  <div style={{ color: "var(--muted)", marginTop: 6 }}>
                    {previewText(a.content, 140, "No description")}
                  </div>
                  <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                    <button
                      onClick={() => attachArticle(a.id)}
                      style={styles.loginButton}
                    >
                      Attach
                    </button>
                    <a
                      href={a.url || "#"}
                      target="_blank"
                      rel="noreferrer"
                      style={{ ...styles.link, alignSelf: "center" }}
                    >
                      View
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginTop: 24 }}>
            <h4>Create a new article in this newspaper</h4>
            <form onSubmit={handleCreateArticle} style={{ maxWidth: 720 }}>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Title</div>
                <input
                  value={aTitle}
                  onChange={(e) => setATitle(e.target.value)}
                  required
                  style={styles.textInput}
                />
              </label>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Content</div>
                <textarea
                  value={aContent}
                  onChange={(e) => setAContent(e.target.value)}
                  rows={6}
                  style={styles.textArea}
                />
              </label>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>
                  Original URL (optional)
                </div>
                <input
                  value={aUrl}
                  onChange={(e) => setAUrl(e.target.value)}
                  style={styles.textInput}
                />
              </label>
              {error && (
                <div style={{ color: "#ef4444", marginBottom: 12 }}>{error}</div>
              )}
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="submit"
                  disabled={creatingArticle}
                  style={styles.addThemeButton}
                >
                  {creatingArticle ? "Creating…" : "Create article"}
                </button>
              </div>
            </form>
          </section>

          <section style={{ marginTop: 24 }}>
            <h4>Attached articles</h4>
            {loadingAttached ? (
              <div>Loading…</div>
            ) : attached.length === 0 ? (
              <div style={{ color: "var(--muted)" }}>No articles attached yet.</div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
                  gap: 12,
                }}
              >
                {attached.map((a) => (
                  <div
                    key={a.id}
                    style={{ ...styles.panelCard, display: "flex", flexDirection: "column", gap: 8 }}
                  >
                    <div style={{ fontWeight: 600 }}>{a.title}</div>
                    <div style={{ color: "var(--muted)", marginTop: 6 }}>
                      {previewText(a.content, 140, "No description")}
                    </div>
                    <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                      <a
                        href={a.url || "#"}
                        target="_blank"
                        rel="noreferrer"
                        style={{ ...styles.link, alignSelf: "center" }}
                      >
                        View
                      </a>
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

CreateNewspaper.propTypes = {
  apiBase: PropTypes.string,
};
