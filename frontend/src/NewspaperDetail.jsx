import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function NewspaperDetail({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [newspaper, setNewspaper] = useState(null);
  const [attached, setAttached] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loggedIn, setLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState(null);
  const [menuCollapsed, setMenuCollapsed] = useState(false);

  const id = (() => {
    if (typeof window === "undefined") return null;
    const match = window.location.pathname.match(/^\/newspapers\/(\d+)$/);
    return match ? match[1] : null;
  })();

  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const [creatingArticle, setCreatingArticle] = useState(false);
  const [aTitle, setATitle] = useState("");
  const [aContent, setAContent] = useState("");
  const [aUrl, setAUrl] = useState("");
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

  function authHeaders(includeJson = false) {
    try {
      const token = localStorage.getItem("access_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      if (includeJson) headers["Content-Type"] = "application/json";
      return headers;
    } catch {
      return includeJson ? { "Content-Type": "application/json" } : {};
    }
  }

  useEffect(() => {
    if (!id) return;
    let mounted = true;
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiBase}/v1/newspapers/${id}`, {
          headers: authHeaders(),
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Failed to load newspaper (${res.status})`);
        const j = await res.json();
        if (mounted) setNewspaper(j);

        const articlesRes = await fetch(`${apiBase}/v1/newspapers/${id}/articles`, {
          headers: authHeaders(),
          signal: controller.signal,
        });
        if (articlesRes.ok) {
          const items = await articlesRes.json();
          if (mounted) setAttached(items || []);
        }
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
      controller.abort();
    };
  }, [apiBase, id]);
  // search existing articles to attach
  useEffect(() => {
    let t = null;
    if (!searchQ) {
      setSearchResults([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    t = setTimeout(async () => {
      try {
        const res = await fetch(
          `${apiBase}/v1/articles/?q=${encodeURIComponent(searchQ)}`,
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
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}/articles/${articleId}`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b.detail || `Attach failed (${res.status})`);
      }
      const j = await res.json();
      setAttached((prev) => [j, ...prev.filter((p) => p.id !== j.id)]);
    } catch (err) {
      setError(err.message);
    }
  }

  async function createArticle(e) {
    e.preventDefault();
    if (!id) return;
    setCreatingArticle(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}/articles`, {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({ title: aTitle, content: aContent, url: aUrl }),
      });
      const body = await res.json();
      if (!res.ok)
        throw new Error(body.detail || `Create article failed (${res.status})`);
      setAttached((prev) => [body, ...prev]);
      setATitle("");
      setAContent("");
      setAUrl("");
    } catch (err) {
      setError(err.message);
    } finally {
      setCreatingArticle(false);
    }
  }

  async function deleteArticle(articleId) {
    // in the newspaper detail context, "delete" means detach from this newspaper
    if (!window.confirm("Remove this article from the newspaper?")) return;
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}/articles/${articleId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`Failed to remove article (${res.status})`);
      const body = await res.json().catch(() => null);
      console.error("Failed to remove article:", body);
      // update attached list: remove the article from attachments
      setAttached((prev) => prev.filter((a) => a.id !== articleId));
    } catch (err) {
      setError(err.message);
    }
  }

  async function patchArticle(articleId, patch) {
    try {
      const res = await fetch(`${apiBase}/v1/articles/${articleId}`, {
        method: "PATCH",
        headers: authHeaders(true),
        body: JSON.stringify(patch),
      });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b.detail || `Update failed (${res.status})`);
      }
      const updated = await res.json();
      setAttached((prev) => prev.map((a) => (a.id === articleId ? updated : a)));
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteArticlePermanently(articleId) {
    if (!window.confirm("Delete this article permanently? This cannot be undone."))
      return;
    try {
      const res = await fetch(`${apiBase}/v1/articles/${articleId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`Delete failed (${res.status})`);
      // remove from attached
      setAttached((prev) => prev.filter((a) => a.id !== articleId));
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleShare(makePublic) {
    if (!id) return;
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}/share`, {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({ public: !!makePublic }),
      });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b.detail || `Share failed (${res.status})`);
      }
      const j = await res.json();
      setNewspaper(j);
    } catch (err) {
      setError(err.message);
    }
  }

  if (!id)
    return (
      <div style={styles.appShell}>
        <div style={styles.appSurface}>
          <div style={styles.panelCard}>Invalid newspaper id.</div>
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
                  <div style={{ marginTop: 6, color: "var(--muted)" }}>
                    Newspaper details
                  </div>
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
                  <h3>Attached articles</h3>
                  {attached.length === 0 ? (
                    <div style={{ color: "var(--muted)" }}>No articles attached.</div>
                  ) : (
                    <div style={{ display: "grid", gap: 12 }}>
                      {attached.map((a) => (
                        <ArticleEditor
                          key={a.id}
                          article={a}
                          onDelete={deleteArticle}
                          onSave={patchArticle}
                          onDeletePermanent={deleteArticlePermanently}
                        />
                      ))}
                    </div>
                  )}
                </section>

                <section style={{ marginTop: 24 }}>
                  <h3>Create a new article in this newspaper</h3>
                  <form onSubmit={createArticle} style={{ maxWidth: 800 }}>
                    <label style={{ display: "block", marginBottom: 8 }}>
                      <div style={{ fontSize: 13, marginBottom: 6 }}>Title</div>
                      <input
                        required
                        value={aTitle}
                        onChange={(e) => setATitle(e.target.value)}
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
                  <h3>Attach existing articles</h3>
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      marginBottom: 12,
                      flexWrap: "wrap",
                    }}
                  >
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
                        style={{
                          ...styles.panelCard,
                          display: "flex",
                          flexDirection: "column",
                          gap: 8,
                        }}
                      >
                        <div style={{ fontWeight: 600 }}>{a.title}</div>
                        <div style={{ color: "var(--muted)", marginTop: 6 }}>
                          {a.content
                            ? a.content.slice(0, 140) +
                              (a.content.length > 140 ? "…" : "")
                            : ""}
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
                  <h3>Share</h3>
                  {Number(localStorage.getItem("user_id")) === newspaper.owner_id ? (
                    <div>
                      <div style={{ marginBottom: 8 }}>
                        {newspaper.is_public ? (
                          <span style={{ color: "#10b981" }}>
                            This newspaper is public.
                          </span>
                        ) : (
                          <span style={{ color: "#f59e0b" }}>
                            This newspaper is private.
                          </span>
                        )}
                      </div>
                      <div
                        style={{
                          display: "flex",
                          gap: 8,
                          alignItems: "center",
                          flexWrap: "wrap",
                        }}
                      >
                        <button
                          onClick={() => toggleShare(!newspaper.is_public)}
                          style={styles.createButton}
                        >
                          {newspaper.is_public ? "Unshare" : "Make public"}
                        </button>
                        {newspaper.is_public && newspaper.public_token && (
                          <>
                            <a
                              href={`/public/newspapers/${newspaper.public_token}`}
                              target="_blank"
                              rel="noreferrer"
                              style={styles.link}
                            >
                              View public page
                            </a>
                            <button
                              onClick={() =>
                                navigator.clipboard?.writeText(
                                  `${window.location.origin}/public/newspapers/${newspaper.public_token}`,
                                )
                              }
                              style={styles.registerButton}
                            >
                              Copy public URL
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div style={{ color: "var(--muted)" }}>
                      Only the owner can change sharing settings.
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

NewspaperDetail.propTypes = {
  apiBase: PropTypes.string,
};

function ArticleEditor({ article, onDelete, onSave, onDeletePermanent }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(article.title);
  const [content, setContent] = useState(article.content || "");
  const [url, setUrl] = useState(article.url || "");
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await onSave(article.id, { title, content, url });
      setEditing(false);
    } catch (e) {
      console.error("Failed to save article:", e);
      // onSave sets error state in parent
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ ...styles.panelCard }}>
      {editing ? (
        <div>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={{ ...styles.textInput, maxWidth: 1110 }}
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={4}
            style={{ ...styles.textArea, marginTop: 8, maxWidth: 1110 }}
          />
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={{ ...styles.textInput, marginTop: 8, maxWidth: 1110 }}
          />
          <div
            style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}
          >
            <button onClick={save} disabled={saving} style={styles.addThemeButton}>
              {saving ? "Saving…" : "Save"}
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setTitle(article.title);
                setContent(article.content || "");
                setUrl(article.url || "");
              }}
              style={styles.registerButton}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div>
          <div style={{ fontWeight: 700 }}>{article.title}</div>
          <div style={{ color: "var(--muted)", marginTop: 6 }}>
            {previewText(article.content, 160, "No description")}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
            <button onClick={() => setEditing(true)} style={styles.registerButton}>
              Edit
            </button>
            <button onClick={() => onDelete(article.id)} style={styles.logoutButton}>
              Remove
            </button>
            {Number(localStorage.getItem("user_id")) === article.owner_id &&
              onDeletePermanent && (
                <button
                  onClick={() => onDeletePermanent(article.id)}
                  style={styles.logoutButton}
                >
                  Delete permanently
                </button>
              )}
          </div>
        </div>
      )}
    </div>
  );
}

ArticleEditor.propTypes = {
  article: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    title: PropTypes.string,
    content: PropTypes.string,
    url: PropTypes.string,
    owner_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }).isRequired,
  onDelete: PropTypes.func,
  onSave: PropTypes.func,
  onDeletePermanent: PropTypes.func,
};
