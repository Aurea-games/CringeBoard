import React, { useEffect, useState, useCallback } from "react";
import PropTypes from "prop-types";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function NewspaperList({
  apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
}) {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);
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
      return token ? { Authorization: `Bearer ${token}` } : {};
    } catch {
      return {};
    }
  }

  const load = useCallback(
    async (query) => {
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
    },
    [apiBase],
  );

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
      const res = await fetch(`${apiBase}/v1/newspapers/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
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
                    My newspapers
                  </div>
                </div>
                {loggedIn && (
                  <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
                    {userEmail ? `Hi, ${userEmail}` : "Logged in"}
                  </div>
                )}
              </div>
            </header>

            <div style={{ marginBottom: 12, marginTop: 12 }}>
              <input
                placeholder="Search newspapers..."
                value={q}
                onChange={(e) => setQ(e.target.value)}
                style={{ ...styles.textInput, minWidth: 300, maxWidth: 520 }}
              />
              <span style={{ marginLeft: 8, color: "var(--muted)" }}>
                {searching ? "Searching…" : ""}
              </span>
            </div>

            {error && <div style={{ color: "#ef4444", marginBottom: 12 }}>{error}</div>}

            {loading ? (
              <div>Loading…</div>
            ) : list.length === 0 ? (
              <div style={{ color: "var(--muted)" }}>
                No newspapers found. Create one using the &quot;New newspaper&quot;
                button.
              </div>
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {list.map((n) => (
                  <NewspaperCard
                    key={n.id}
                    newspaper={n}
                    onDelete={handleDelete}
                    onPatch={handlePatch}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
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
    <div
      style={{
        ...styles.panelCard,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <div style={{ flex: 1 }}>
        {editing ? (
          <div>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{ ...styles.textInput, maxWidth: 1000 }}
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              style={{ ...styles.textArea, marginTop: 8, maxWidth: 1000 }}
            />
          </div>
        ) : (
          <div>
            <div style={{ fontWeight: 700 }}>{newspaper.title}</div>
            <div style={{ color: "var(--muted)" }}>{newspaper.description}</div>
            <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 6 }}>
              Created: {new Date(newspaper.created_at).toLocaleDateString()}
            </div>
          </div>
        )}
      </div>

      <div
        style={{
          display: "flex",
          gap: 8,
          marginLeft: 12,
          flexDirection: editing ? "column" : "row",
          alignItems: editing ? "stretch" : "center",
        }}
      >
        {editing ? (
          <>
            <button
              onClick={() => {
                onPatch(newspaper.id, { title, description });
                setEditing(false);
              }}
              style={styles.addThemeButton}
            >
              Save
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setTitle(newspaper.title);
                setDescription(newspaper.description || "");
              }}
              style={styles.registerButton}
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <a
              href={`/newspapers/${newspaper.id}`}
              style={{ ...styles.registerButton, textDecoration: "none" }}
            >
              Details
            </a>
            <button onClick={() => setEditing(true)} style={styles.registerButton}>
              Edit
            </button>
            <button onClick={() => onDelete(newspaper.id)} style={styles.logoutButton}>
              Delete
            </button>
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
