import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { styles } from "./styles.js";
import SideMenu from "./SideMenu.jsx";

export default function Register({ apiBase = "http://localhost:8000" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
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

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, confirm_password: confirm }),
      });

      const body = await res.json();
      if (!res.ok) {
        setError(body.detail || body.error || JSON.stringify(body));
        setLoading(false);
        return;
      }

      // expected TokenResponse
      if (body.access_token) {
        try {
          localStorage.setItem("access_token", body.access_token);
          localStorage.setItem("user_email", email);
          if (body.refresh_token)
            localStorage.setItem("refresh_token", body.refresh_token);
        } catch {
          // ignore storage failures
        }
        // fetch authenticated user info to store user id
        try {
          const meRes = await fetch(`${apiBase}/v1/auth/users/me`, {
            headers: { Authorization: `Bearer ${body.access_token}` },
          });
          if (meRes.ok) {
            const me = await meRes.json();
            if (me?.id) localStorage.setItem("user_id", String(me.id));
            if (me?.email) localStorage.setItem("user_email", me.email);
          }
        } catch {
          // ignore
        }
        window.location.href = "/";
      } else {
        setError("Registration succeeded but no token received.");
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
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
                <h1 style={{ margin: 0 }}>CringeBoard</h1>
                {loggedIn && (
                  <div style={{ fontSize: 13, color: "var(--muted-strong)" }}>
                    {userEmail ? `Hi, ${userEmail}` : "Logged in"}
                  </div>
                )}
              </div>
            </header>

            <div style={{ ...styles.formCard, maxWidth: 520, margin: "0 auto" }}>
          <h2 style={{ marginTop: 0 }}>Register</h2>
          <form onSubmit={handleSubmit}>
            <label style={{ display: "block", marginBottom: 8 }}>
              <div style={{ fontSize: 13, marginBottom: 6, ...styles.mutedText }}>
                Email
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ ...styles.textInput, maxWidth: 420 }}
              />
            </label>

            <label style={{ display: "block", marginBottom: 8 }}>
              <div style={{ fontSize: 13, marginBottom: 6, ...styles.mutedText }}>
                Password
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ ...styles.textInput, maxWidth: 420 }}
              />
            </label>

            <label style={{ display: "block", marginBottom: 12 }}>
              <div style={{ fontSize: 13, marginBottom: 6, ...styles.mutedText }}>
                Confirm Password
              </div>
              <input
                type="password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                style={{ ...styles.textInput, maxWidth: 420 }}
              />
            </label>

            {error && (
              <div style={{ color: "#ef4444", marginBottom: 12 }}>
                <strong>Error:</strong> {error}
              </div>
            )}

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="submit" disabled={loading} style={styles.addThemeButton}>
                {loading ? "Creating…" : "Create account"}
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

          <div style={{ marginTop: 14, fontSize: 13, color: "var(--muted)" }}>
            <div>
              Already have an account?{" "}
              <a href="/login" style={styles.link}>
                Sign in
              </a>
            </div>
            <div style={{ marginTop: 6 }}>
              Development note: form posts to <code>{apiBase}/v1/auth/register</code>
            </div>
          </div>
        </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Register.propTypes = {
  apiBase: PropTypes.string,
};
