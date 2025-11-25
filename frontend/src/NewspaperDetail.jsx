import React, { useEffect, useState } from "react";
import { previewText } from "./utils.js";

export default function NewspaperDetail({ apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000" }) {
  const [newspaper, setNewspaper] = useState(null);
  const [attached, setAttached] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const [creatingArticle, setCreatingArticle] = useState(false);
  const [aTitle, setATitle] = useState("");
  const [aContent, setAContent] = useState("");
  const [aUrl, setAUrl] = useState("");

  const id = (() => {
    try {
      const m = window.location.pathname.match(/^\/newspapers\/(\d+)$/);
      return m ? Number(m[1]) : null;
    } catch (e) {
      return null;
    }
  })();

  function authHeaders(json = false) {
    try {
      const token = localStorage.getItem("access_token");
      const base = token ? { Authorization: `Bearer ${token}` } : {};
      return json ? { ...base, "Content-Type": "application/json" } : base;
    } catch (e) {
      return json ? { "Content-Type": "application/json" } : {};
    }
  }

  async function load() {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}`);
      if (!res.ok) throw new Error(`Failed to load newspaper (${res.status})`);
      const j = await res.json();
      setNewspaper(j);

      const r2 = await fetch(`${apiBase}/v1/newspapers/${id}/articles`);
      if (!r2.ok) throw new Error(`Failed to load articles (${r2.status})`);
      const a = await r2.json();
      setAttached(a || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

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
        const res = await fetch(`${apiBase}/v1/articles/?q=${encodeURIComponent(searchQ)}`);
        if (!res.ok) {
          setSearchResults([]);
        } else {
          const j = await res.json();
          setSearchResults(j || []);
        }
      } catch (e) {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [searchQ]);

  async function attachArticle(articleId) {
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}/articles/${articleId}`, { method: "POST", headers: authHeaders() });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b.detail || `Attach failed (${res.status})`);
      }
      const j = await res.json();
      setAttached((prev) => [j, ...prev.filter((p) => p.id !== j.id)]);
    } catch (e) {
      setError(e.message);
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
      if (!res.ok) throw new Error(body.detail || `Create article failed (${res.status})`);
      setAttached((prev) => [body, ...prev]);
      setATitle("");
      setAContent("");
      setAUrl("");
    } catch (e) {
      setError(e.message);
    } finally {
      setCreatingArticle(false);
    }
  }

  async function deleteArticle(articleId) {
    // in the newspaper detail context, "delete" means detach from this newspaper
    if (!window.confirm("Remove this article from the newspaper?")) return;
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}/articles/${articleId}`, { method: "DELETE", headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed to remove article (${res.status})`);
      const body = await res.json().catch(() => null);
      // update attached list: remove the article from attachments
      setAttached((prev) => prev.filter((a) => a.id !== articleId));
    } catch (e) {
      setError(e.message);
    }
  }

  async function patchArticle(articleId, patch) {
    try {
      const res = await fetch(`${apiBase}/v1/articles/${articleId}`, { method: "PATCH", headers: authHeaders(true), body: JSON.stringify(patch) });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b.detail || `Update failed (${res.status})`);
      }
      const updated = await res.json();
      setAttached((prev) => prev.map((a) => (a.id === articleId ? updated : a)));
    } catch (e) {
      setError(e.message);
    }
  }

  async function deleteArticlePermanently(articleId) {
    if (!window.confirm("Delete this article permanently? This cannot be undone.")) return;
    try {
      const res = await fetch(`${apiBase}/v1/articles/${articleId}`, { method: "DELETE", headers: authHeaders() });
      if (!res.ok) throw new Error(`Delete failed (${res.status})`);
      // remove from attached
      setAttached((prev) => prev.filter((a) => a.id !== articleId));
    } catch (e) {
      setError(e.message);
    }
  }

  if (!id) return <div style={{ padding: 20 }}>Invalid newspaper id.</div>;

  return (
    <div style={{ padding: 20 }}>
      <button onClick={() => (window.location.href = "/newspapers")} style={{ marginBottom: 12 }}>
        ← Back
      </button>
      {loading ? (
        <div>Loading…</div>
      ) : error ? (
        <div style={{ color: "#b02a37" }}>{error}</div>
      ) : (
        <div>
          <h2 style={{ marginTop: 0 }}>{newspaper.title}</h2>
          <p>{newspaper.description}</p>

          <section style={{ marginTop: 18 }}>
            <h3>Attached articles</h3>
                {attached.length === 0 ? (
              <div style={{ color: "#666" }}>No articles attached.</div>
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {attached.map((a) => (
                  <ArticleEditor key={a.id} article={a} onDelete={deleteArticle} onSave={patchArticle} onDeletePermanent={deleteArticlePermanently} />
                ))}
              </div>
            )}
          </section>

          <section style={{ marginTop: 24 }}>
            <h3>Create a new article in this newspaper</h3>
            <form onSubmit={createArticle} style={{ maxWidth: 800 }}>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Title</div>
                <input required value={aTitle} onChange={(e) => setATitle(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              </label>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Content</div>
                <textarea value={aContent} onChange={(e) => setAContent(e.target.value)} rows={6} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              </label>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Original URL (optional)</div>
                <input value={aUrl} onChange={(e) => setAUrl(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              </label>
              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" disabled={creatingArticle} style={{ padding: "8px 12px", background: "#16a34a", color: "white", border: "none", borderRadius: 6 }}>
                  {creatingArticle ? "Creating…" : "Create article"}
                </button>
              </div>
            </form>
          </section>

          <section style={{ marginTop: 24 }}>
            <h3>Attach existing articles</h3>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <input placeholder="Search articles to attach" value={searchQ} onChange={(e) => setSearchQ(e.target.value)} style={{ flex: 1, padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              <div style={{ alignSelf: "center", color: "#666" }}>{searching ? "Searching…" : ""}</div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
              {searchResults.map((a) => (
                <div key={a.id} style={{ border: "1px solid #eee", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontWeight: 600 }}>{a.title}</div>
                  <div style={{ color: "#555", marginTop: 6 }}>{a.content ? a.content.slice(0, 140) + (a.content.length > 140 ? "…" : "") : ""}</div>
                  <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                    <button onClick={() => attachArticle(a.id)} style={{ padding: "6px 8px", borderRadius: 6, background: "#2563eb", color: "white", border: "none" }}>
                      Attach
                    </button>
                    <a href={a.url || "#"} target="_blank" rel="noreferrer" style={{ color: "#2563eb", alignSelf: "center" }}>
                      View
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

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
      // onSave sets error state in parent
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 8 }}>
      {editing ? (
        <div>
          <input value={title} onChange={(e) => setTitle(e.target.value)} style={{ width: "100%", padding: 6, borderRadius: 6, border: "1px solid #ddd" }} />
          <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={4} style={{ width: "100%", padding: 6, borderRadius: 6, border: "1px solid #ddd", marginTop: 8 }} />
          <input value={url} onChange={(e) => setUrl(e.target.value)} style={{ width: "100%", padding: 6, borderRadius: 6, border: "1px solid #ddd", marginTop: 8 }} />
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button onClick={save} disabled={saving} style={{ padding: "6px 8px", borderRadius: 6, background: "#16a34a", color: "white", border: "none" }}>{saving ? "Saving…" : "Save"}</button>
            <button onClick={() => { setEditing(false); setTitle(article.title); setContent(article.content || ""); setUrl(article.url || ""); }} style={{ padding: "6px 8px", borderRadius: 6 }}>Cancel</button>
          </div>
        </div>
      ) : (
        <div>
          <div style={{ fontWeight: 700 }}>{article.title}</div>
          <div style={{ color: "#555", marginTop: 6 }}>{previewText(article.content, 160, "No description")}</div>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <a href={article.url || "#"} target="_blank" rel="noreferrer" style={{ color: "#2563eb" }}>View</a>
            <button onClick={() => setEditing(true)} style={{ padding: "6px 8px", borderRadius: 6 }}>Edit</button>
            <button onClick={() => onDelete(article.id)} style={{ padding: "6px 8px", borderRadius: 6, background: "#ef4444", color: "white", border: "none" }}>Remove</button>
            {Number(localStorage.getItem("user_id")) === article.owner_id && onDeletePermanent && (
              <button onClick={() => onDeletePermanent(article.id)} style={{ padding: "6px 8px", borderRadius: 6, background: "#b91c1c", color: "white", border: "none" }}>Delete permanently</button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
