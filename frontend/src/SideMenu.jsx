import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { styles } from "./styles.js";

export default function SideMenu({
  collapsed,
  onToggleCollapse,
  loggedIn,
  showPopularButton,
  showPopular,
  onPopularToggle,
  showNotificationsButton,
  notifications,
  showNotifications,
  onToggleNotifications,
  unreadCount,
}) {
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved === "dark") document.body.classList.add("dark");
  }, []);

  function toggleTheme() {
    const isDark = document.body.classList.toggle("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
  }

  function handleLogout() {
    try {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_email");
    } catch (err) {
      console.error("Failed to clear auth tokens", err);
    }
    window.location.href = "/";
  }

  function goHome() {
    window.location.href = "/";
  }

  function goLogin() {
    window.location.href = "/login";
  }

  function goRegister() {
    window.location.href = "/register";
  }

  function goCreateNewspaper() {
    window.location.href = "/newspapers/create";
  }

  function goNewspapers() {
    window.location.href = "/newspapers";
  }

  function goFavorites() {
    window.location.href = "/favorites";
  }

  function goPublicNewspapers() {
    window.location.href = "/public/newspapers";
  }

  const buttonBase = collapsed
    ? { ...styles.sideMenuButton, ...styles.sideMenuButtonCollapsed }
    : styles.sideMenuButton;

  const labelStyle = collapsed ? styles.sideMenuLabelCollapsed : styles.sideMenuLabel;

  return (
    <aside
      style={{
        ...styles.sideMenu,
        ...(collapsed ? styles.sideMenuCollapsed : null),
      }}
    >
      <button
        onClick={onToggleCollapse}
        style={styles.sideMenuToggle}
        aria-label="Toggle menu"
      >
        <span style={styles.sideMenuIcon}>{collapsed ? "➡️" : "⬅️"}</span>
        <span style={labelStyle}>Menu</span>
      </button>

      <div style={styles.sideMenuGroup}>
        <button onClick={goHome} style={buttonBase}>
          <span style={styles.sideMenuIcon}>🏠</span>
          <span style={labelStyle}>Home</span>
        </button>

        {showPopularButton && (
          <button
            onClick={onPopularToggle}
            style={{
              ...buttonBase,
              background: showPopular ? "#2563eb" : buttonBase.background,
              color: showPopular ? "white" : buttonBase.color,
            }}
          >
            <span style={styles.sideMenuIcon}>🔥</span>
            <span style={labelStyle}>Popular</span>
          </button>
        )}

        <button onClick={toggleTheme} style={buttonBase}>
          <span style={styles.sideMenuIcon}>🌓</span>
          <span style={labelStyle}>Toggle theme</span>
        </button>

        {showNotificationsButton && (
          <div style={styles.sideMenuItemWrapper}>
            <button
              onClick={onToggleNotifications}
              style={buttonBase}
              aria-label="Notifications"
            >
              <span style={styles.sideMenuIcon}>🔔</span>
              <span style={labelStyle}>Notifications</span>
              {unreadCount > 0 && (
                <span style={styles.notificationBadge}>{unreadCount}</span>
              )}
            </button>
            {showNotifications && (
              <div style={styles.notificationDropdown}>
                {notifications.length === 0 ? (
                  <div style={{ color: "var(--muted)", fontSize: 13 }}>
                    No notifications
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div key={n.id} style={styles.notificationItem}>
                      <div style={{ fontWeight: n.is_read ? "normal" : "600" }}>
                        {n.message}
                      </div>
                      <div style={{ color: "var(--muted)", fontSize: 11 }}>
                        {n.created_at || ""}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {loggedIn ? (
        <div style={styles.sideMenuGroup}>
          <button onClick={goCreateNewspaper} style={buttonBase}>
            <span style={styles.sideMenuIcon}>📰</span>
            <span style={labelStyle}>New newspaper</span>
          </button>
          <button onClick={goNewspapers} style={buttonBase}>
            <span style={styles.sideMenuIcon}>📚</span>
            <span style={labelStyle}>My newspapers</span>
          </button>
          <button onClick={goFavorites} style={buttonBase}>
            <span style={styles.sideMenuIcon}>⭐</span>
            <span style={labelStyle}>Favorites</span>
          </button>
          <button onClick={goPublicNewspapers} style={buttonBase}>
            <span style={styles.sideMenuIcon}>🌍</span>
            <span style={labelStyle}>Public newspapers</span>
          </button>
          <button onClick={handleLogout} style={buttonBase}>
            <span style={styles.sideMenuIcon}>🚪</span>
            <span style={labelStyle}>Logout</span>
          </button>
        </div>
      ) : (
        <div style={styles.sideMenuGroup}>
          <button onClick={goLogin} style={buttonBase}>
            <span style={styles.sideMenuIcon}>🔐</span>
            <span style={labelStyle}>Login</span>
          </button>
          <button onClick={goRegister} style={buttonBase}>
            <span style={styles.sideMenuIcon}>🧾</span>
            <span style={labelStyle}>Register</span>
          </button>
        </div>
      )}
    </aside>
  );
}

SideMenu.propTypes = {
  collapsed: PropTypes.bool,
  onToggleCollapse: PropTypes.func,
  loggedIn: PropTypes.bool,
  showPopularButton: PropTypes.bool,
  showPopular: PropTypes.bool,
  onPopularToggle: PropTypes.func,
  showNotificationsButton: PropTypes.bool,
  notifications: PropTypes.array,
  showNotifications: PropTypes.bool,
  onToggleNotifications: PropTypes.func,
  unreadCount: PropTypes.number,
};

SideMenu.defaultProps = {
  collapsed: false,
  onToggleCollapse: () => {},
  loggedIn: false,
  showPopularButton: false,
  showPopular: false,
  onPopularToggle: () => {},
  showNotificationsButton: false,
  notifications: [],
  showNotifications: false,
  onToggleNotifications: () => {},
  unreadCount: 0,
};
