import React, { useEffect, useState, useCallback } from "react";
import PropTypes from "prop-types";

export default function NewspaperList({ apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000" }) {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);

  function authHeaders() {
    try {
      const token = localStorage.getItem("access_token");
      return token ? { Authorization: `Bearer ${token}` } : {};
    } catch {
      return {};
    }
  }

  const load = useCallback(async (query) => {
    setLoading(true);
    setError(null);
    try {
      const owner = localStorage.getItem("user_email");
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      if (owner) params.set("owner_email", owner);
      const url = `${apiBase}/v1/newspapers/?${params.toString()}`;
      const res = await fetch(url, { headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed to fetch (${res.status})`);
      const j = await res.json();
      setList(j || []);
    } catch (err) {
      setError(err.message);
      setList([]);
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    let t = null;
    setSearching(true);
    t = setTimeout(() => {
      load(q).finally(() => setSearching(false));
    }, 300);
    return () => clearTimeout(t);
  }, [q, load]);

  useEffect(() => {
    load("");
  }, [load]);

  async function handleDelete(id) {
    if (!window.confirm("Delete this newspaper? This cannot be undone.")) return;
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}`, { method: "DELETE", headers: authHeaders() });
      if (!res.ok) throw new Error(`Delete failed (${res.status})`);
      setList((prev) => prev.filter((n) => n.id !== id));
    } catch (e) {
      setError(e.message);
    }
  }

  async function handlePatch(id, patch) {
    try {
      const res = await fetch(`${apiBase}/v1/newspapers/${id}`, {
        method: "PATCH",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b.detail || `Update failed (${res.status})`);
      }
      const updated = await res.json();
      setList((prev) => prev.map((n) => (n.id === id ? updated : n)));
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div style={{ padding: 20, fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif" }}>
      <h2 style={{ display: "inline-block", marginRight: 12 }}>My Newspapers</h2>
          <button onClick={() => (window.location.href = "/")} style={{ padding: "6px 10px", borderRadius: 6, background: "#2563eb", color: "white", border: "none", cursor: "pointer" }}>Home</button>
          <div style={{ marginBottom: 12, marginTop: 12 }}>
        <input placeholder="Search newspapers..." value={q} onChange={(e) => setQ(e.target.value)} style={{ padding: 8, borderRadius: 6, border: "1px solid #ddd", minWidth: 300 }} />
        <span style={{ marginLeft: 8, color: "#666" }}>{searching ? "Searching…" : ""}</span>
      </div>

      {error && <div style={{ color: "#b02a37", marginBottom: 12 }}>{error}</div>}

      {loading ? (
        <div>Loading…</div>
      ) : list.length === 0 ? (
        <div style={{ color: "#666" }}>No newspapers found. Create one using the &quot;New newspaper&quot; button.</div>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {list.map((n) => (
            <NewspaperCard key={n.id} newspaper={n} onDelete={handleDelete} onPatch={handlePatch} />
          ))}
        </div>
      )}
    </div>
  );
}

NewspaperList.propTypes = {
  apiBase: PropTypes.string,
};

function NewspaperCard({ newspaper, onDelete, onPatch }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(newspaper.title);
  const [description, setDescription] = useState(newspaper.description || "");

  return (
    <div style={{ border: "1px solid #eee", padding: 12, borderRadius: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div style={{ flex: 1 }}>
        {editing ? (
          <div>
            <input value={title} onChange={(e) => setTitle(e.target.value)} style={{ width: "100%", padding: 6, borderRadius: 6, border: "1px solid #ddd" }} />
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} style={{ width: "100%", padding: 6, borderRadius: 6, border: "1px solid #ddd", marginTop: 8 }} />
          </div>
        ) : (
          <div>
            <div style={{ fontWeight: 700 }}>{newspaper.title}</div>
            <div style={{ color: "#555" }}>{newspaper.description}</div>
            <div style={{ color: "#888", fontSize: 12, marginTop: 6 }}>Created: {new Date(newspaper.created_at).toLocaleDateString()}</div>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: 8, marginLeft: 12 }}>
        {editing ? (
          <>
            <button onClick={() => { onPatch(newspaper.id, { title, description }); setEditing(false); }} style={{ padding: "6px 8px", borderRadius: 6, background: "#16a34a", color: "white", border: "none" }}>Save</button>
            <button onClick={() => { setEditing(false); setTitle(newspaper.title); setDescription(newspaper.description || ""); }} style={{ padding: "6px 8px", borderRadius: 6 }}>Cancel</button>
          </>
        ) : (
          <>
            <a href={`/newspapers/${newspaper.id}`} style={{ padding: "6px 8px", borderRadius: 6, background: "#efefef", textDecoration: "none", color: "#111" }}>View</a>
            <button onClick={() => setEditing(true)} style={{ padding: "6px 8px", borderRadius: 6 }}>Edit</button>
            <button onClick={() => onDelete(newspaper.id)} style={{ padding: "6px 8px", borderRadius: 6, background: "#ef4444", color: "white", border: "none" }}>Delete</button>
          </>
        )}
      </div>
    </div>
  );
}

NewspaperCard.propTypes = {
  newspaper: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    title: PropTypes.string,
    description: PropTypes.string,
    created_at: PropTypes.string,
  }).isRequired,
  onDelete: PropTypes.func.isRequired,
  onPatch: PropTypes.func.isRequired,
};
