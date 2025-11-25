import React, { useState } from "react";
import PropTypes from "prop-types";

export default function Login({ apiBase = "http://localhost:8000" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const body = await res.json();
      if (!res.ok) {
        setError(body.detail || body.error || JSON.stringify(body));
        setLoading(false);
        return;
      }

      // expected: { access_token, refresh_token, token_type }
      if (body.access_token) {
        try {
          localStorage.setItem("access_token", body.access_token);
          localStorage.setItem("user_email", email);
          if (body.refresh_token) localStorage.setItem("refresh_token", body.refresh_token);
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
        // redirect to home
        window.location.href = "/";
      } else {
        setError("Login succeeded but no token received.");
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif", padding: 20 }}>
      <div style={{ maxWidth: 480, margin: "40px auto", padding: 20, border: "1px solid #eee", borderRadius: 8 }}>
        <h2 style={{ marginTop: 0 }}>Login</h2>
        <form onSubmit={handleSubmit}>
          <label style={{ display: "block", marginBottom: 8 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Email</div>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd" }}
            />
          </label>

          <label style={{ display: "block", marginBottom: 12 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Password</div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd" }}
            />
          </label>

          {error && (
            <div style={{ color: "#b02a37", marginBottom: 12 }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="submit"
              disabled={loading}
              style={{ padding: "8px 12px", borderRadius: 6, background: "#2563eb", color: "white", border: "none" }}
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>

            <button
              type="button"
              onClick={() => (window.location.href = "/")}
              style={{ padding: "8px 12px", borderRadius: 6, background: "#f3f4f6", border: "1px solid #e5e7eb" }}
            >
              Cancel
            </button>
          </div>
        </form>

        <div style={{ marginTop: 14, fontSize: 13, color: "#555" }}>
          <div>Don&apos;t have an account? <a href="/register">Register</a></div>
          <div style={{ marginTop: 6 }}>
            Development note: form posts to <code>{apiBase}/v1/auth/login</code>
          </div>
        </div>
      </div>
    </div>
  );
}

Login.propTypes = {
  apiBase: PropTypes.string,
};
