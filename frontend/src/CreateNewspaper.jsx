import React, { useEffect, useState } from "react";
import { previewText } from "./utils.js";

export default function CreateNewspaper({ apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000" }) {
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

  function authHeaders() {
    try {
      const token = localStorage.getItem("access_token");
      return token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
    } catch (e) {
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

  async function loadAttached(id) {
    setLoadingAttached(true);
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}/articles`, { headers: authHeaders() });
      if (!res.ok) return;
      const j = await res.json();
      setAttached(j || []);
    } catch (e) {
      // ignore
    } finally {
      setLoadingAttached(false);
    }
  }

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
        const res = await fetch(`${apiBase}/v1/articles/?q=${encodeURIComponent(searchQ)}`, { headers: authHeaders() });
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
    if (!newspaper) return;
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${newspaper.id}/articles/${articleId}`, {
        method: "POST",
        headers: authHeaders(),
      });
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
  }, [newspaper]);

  return (
    <div style={{ padding: 20, fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif" }}>
      <h2>Create a newspaper</h2>
      {!newspaper ? (
        <form onSubmit={handleCreateNewspaper} style={{ maxWidth: 720, marginBottom: 24 }}>
          <label style={{ display: "block", marginBottom: 12 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Title</div>
            <input required value={title} onChange={(e) => setTitle(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
          </label>
          <label style={{ display: "block", marginBottom: 12 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Description</div>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
          </label>
          {error && <div style={{ color: "#b02a37", marginBottom: 12 }}>{error}</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <button type="submit" disabled={creating} style={{ padding: "8px 12px", background: "#06b6d4", color: "white", border: "none", borderRadius: 6 }}>
              {creating ? "Creating…" : "Create newspaper"}
            </button>
            <button type="button" onClick={() => (window.location.href = "/")} style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #e5e7eb" }}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div style={{ maxWidth: 980 }}>
          <h3 style={{ marginTop: 0 }}>{newspaper.title}</h3>
          <p style={{ color: "#444" }}>{newspaper.description}</p>

          <section style={{ marginTop: 18 }}>
            <h4>Attach existing articles</h4>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <input placeholder="Search articles to attach" value={searchQ} onChange={(e) => setSearchQ(e.target.value)} style={{ flex: 1, padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              <div style={{ alignSelf: "center", color: "#666" }}>{searching ? "Searching…" : ""}</div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
              {searchResults.map((a) => (
                <div key={a.id} style={{ border: "1px solid #eee", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontWeight: 600 }}>{a.title}</div>
                  <div style={{ color: "#555", marginTop: 6 }}>{previewText(a.content, 140, "No description")}</div>
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

          <section style={{ marginTop: 24 }}>
            <h4>Create a new article in this newspaper</h4>
            <form onSubmit={handleCreateArticle} style={{ maxWidth: 720 }}>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Title</div>
                <input value={aTitle} onChange={(e) => setATitle(e.target.value)} required style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              </label>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Content</div>
                <textarea value={aContent} onChange={(e) => setAContent(e.target.value)} rows={6} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              </label>
              <label style={{ display: "block", marginBottom: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Original URL (optional)</div>
                <input value={aUrl} onChange={(e) => setAUrl(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd" }} />
              </label>
              {error && <div style={{ color: "#b02a37", marginBottom: 12 }}>{error}</div>}
              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" disabled={creatingArticle} style={{ padding: "8px 12px", background: "#16a34a", color: "white", border: "none", borderRadius: 6 }}>
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
              <div style={{ color: "#666" }}>No articles attached yet.</div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
                {attached.map((a) => (
                  <div key={a.id} style={{ border: "1px solid #eee", padding: 10, borderRadius: 8 }}>
                    <div style={{ fontWeight: 600 }}>{a.title}</div>
                    <div style={{ color: "#555", marginTop: 6 }}>{previewText(a.content, 140, "No description")}</div>
                    <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                      <a href={a.url || "#"} target="_blank" rel="noreferrer" style={{ color: "#2563eb", alignSelf: "center" }}>
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
  );
}
