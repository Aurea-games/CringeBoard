import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { previewText } from "./utils.js";
import { styles } from "./styles.js";

const defaultApiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function ArticleCard({
  article,
  apiBase = defaultApiBase,
  isFavorited = false,
  onFavoriteToggle,
}) {
  const [flipped, setFlipped] = useState(false);
  const [favorited, setFavorited] = useState(isFavorited);
  const [related, setRelated] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);
  const [relatedError, setRelatedError] = useState(null);
  const [showRelated, setShowRelated] = useState(false);
  const [centerPos, setCenterPos] = useState(null);

  useEffect(() => {
    setFavorited(isFavorited);
  }, [isFavorited]);

  useEffect(() => {
    if (!flipped) return;
    const updateCenter = () => {
      setCenterPos({
        top: window.scrollY + window.innerHeight / 2,
        left: window.scrollX + window.innerWidth / 2,
      });
    };
    updateCenter();
    window.addEventListener("scroll", updateCenter, { passive: true });
    window.addEventListener("resize", updateCenter);
    return () => {
      window.removeEventListener("scroll", updateCenter);
      window.removeEventListener("resize", updateCenter);
    };
  }, [flipped]);

  function toggleFlip() {
    setFlipped((v) => !v);
  }

  function handleKey(e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleFlip();
    }
  }

  async function handleFavorite(e) {
    e.stopPropagation();
    const token = localStorage.getItem("access_token");
    if (!token) return alert("Login to favorite articles");

    const previousState = favorited;
    const nextState = !previousState;
    setFavorited(nextState);

    try {
      const headers = { Authorization: `Bearer ${token}` };
      let response;

      if (nextState) {
        headers["Content-Type"] = "application/json";
        response = await fetch(`${apiBase}/v1/me/favorites`, {
          method: "POST",
          headers,
          body: JSON.stringify({ article_id: article.id }),
        });
      } else {
        response = await fetch(`${apiBase}/v1/me/favorites/${article.id}`, {
          method: "DELETE",
          headers,
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to ${nextState ? "favorite" : "unfavorite"} article`);
      }

      if (onFavoriteToggle) onFavoriteToggle(article.id, nextState);
    } catch (err) {
      console.error(err);
      setFavorited(previousState);
      alert("Could not update favorite status");
    }
  }

  async function fetchRelated(e) {
    e.stopPropagation();
    if (!article?.id) return;
    if (related.length > 0) {
      setShowRelated((v) => !v);
      return;
    }
    setRelatedLoading(true);
    setRelatedError(null);
    try {
      const res = await fetch(`${apiBase}/v1/articles/${article.id}/related`);
      if (!res.ok) throw new Error("Failed to load related articles");
      const data = await res.json();
      setRelated(Array.isArray(data) ? data.slice(0, 5) : []);
      setShowRelated(true);
    } catch (err) {
      console.warn(err);
      setRelatedError("Could not load related articles");
    } finally {
      setRelatedLoading(false);
    }
  }

  const frontStyle = {
    ...styles.card,
    ...styles.front,
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backfaceVisibility: "hidden",
    opacity: flipped ? 0 : 1,
    visibility: flipped ? "hidden" : "visible",
    transition: "opacity 0.25s ease",
  };

  const backStyle = {
    ...styles.card,
    ...styles.back,
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    overflowY: "auto",
    backfaceVisibility: "hidden",
    transform: "rotateY(180deg)",
    opacity: flipped ? 1 : 0,
    visibility: flipped ? "visible" : "hidden",
    transition: "opacity 0.25s ease",
    color: "var(--text)",
  };

  const flippedHeight = "60vh";

  const containerStyle = flipped
    ? {
        ...styles.flipContainer,
        position: "absolute",
        top: centerPos?.top ? `${centerPos.top}px` : "50%",
        left: centerPos?.left ? `${centerPos.left}px` : "50%",
        transform: "translate(-50%, -50%)",
        width: "70vw",
        maxWidth: 760,
        minWidth: 360,
        height: flippedHeight,
        zIndex: 999,
      }
    : {
        ...styles.flipContainer,
        width: "100%",
        display: "block",
      };

  return (
    <div
      style={containerStyle}
      onClick={toggleFlip}
      onKeyDown={handleKey}
      role="button"
      tabIndex={0}
      aria-pressed={flipped}
    >
      <div
        style={{
          ...styles.flipper,
          transform: flipped ? "rotateY(180deg) scale(1.2)" : "rotateY(0deg) scale(1)",
          transition: "transform 0.4s ease",
          transformOrigin: "center",
          minHeight: flipped ? flippedHeight : 110,
        }}
      >
        <article style={frontStyle}>
          <h3 style={{ margin: 0, textAlign: "left", color: "var(--text)" }}>
            {article.title}
          </h3>
          <div
            onClick={handleFavorite}
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              fontSize: 20,
              color: favorited ? "#facc15" : "#aaa",
              cursor: "pointer",
            }}
            title={favorited ? "Favorited" : "Add to favorites"}
          >
            ★
          </div>
        </article>

        <article style={backStyle}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <button
              onClick={fetchRelated}
              style={{ ...styles.pillButton, opacity: article?.id ? 1 : 0.5 }}
              disabled={!article?.id || relatedLoading}
            >
              {relatedLoading ? "Loading…" : showRelated ? "Hide similar" : "Similar"}
            </button>
          </div>
          <p style={{ margin: 0, color: "var(--muted)", marginTop: 10 }}>
            {previewText(article.content, 160, "No description")}
          </p>

          {showRelated && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Similar articles</div>
              {relatedError && (
                <div style={{ color: "#ef4444", fontSize: 13 }}>{relatedError}</div>
              )}
              {related.length === 0 && !relatedError && !relatedLoading && (
                <div style={{ color: "var(--muted)", fontSize: 13 }}>
                  No related articles found.
                </div>
              )}
              <ul style={{ paddingLeft: 16, margin: 0, display: "grid", gap: 6 }}>
                {related.map((item) => (
                  <li key={item.id || item.title} style={{ lineHeight: 1.3 }}>
                    <a
                      href={item.url || "#"}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      style={{ color: "#2563eb" }}
                    >
                      {item.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ marginTop: 10 }}>
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noreferrer"
                style={{ color: "#3b82f6" }}
                onClick={(e) => e.stopPropagation()}
              >
                Read original
              </a>
            )}
          </div>
        </article>
      </div>
    </div>
  );
}

ArticleCard.propTypes = {
  article: PropTypes.object.isRequired,
  apiBase: PropTypes.string,
  isFavorited: PropTypes.bool,
  onFavoriteToggle: PropTypes.func,
};
