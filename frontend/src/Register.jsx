import React, { useState } from "react";

export default function Register({ apiBase = "http://localhost:8000" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
          if (body.refresh_token) localStorage.setItem("refresh_token", body.refresh_token);
        } catch (e) {
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
        } catch (e) {
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
    <div style={{ fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif", padding: 20 }}>
      <div style={{ maxWidth: 520, margin: "40px auto", padding: 20, border: "1px solid #eee", borderRadius: 8 }}>
        <h2 style={{ marginTop: 0 }}>Register</h2>
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

          <label style={{ display: "block", marginBottom: 8 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Password</div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd" }}
            />
          </label>

          <label style={{ display: "block", marginBottom: 12 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>Confirm Password</div>
            <input
              type="password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
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
              style={{ padding: "8px 12px", borderRadius: 6, background: "#16a34a", color: "white", border: "none" }}
            >
              {loading ? "Creating…" : "Create account"}
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
          <div>Already have an account? <a href="/login">Sign in</a></div>
          <div style={{ marginTop: 6 }}>
            Development note: form posts to <code>{apiBase}/v1/auth/register</code>
          </div>
        </div>
      </div>
    </div>
  );
}
