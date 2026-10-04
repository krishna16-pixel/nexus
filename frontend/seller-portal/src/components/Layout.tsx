import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { IconBooks, IconDashboard, IconOrders, IconPlus, IconStack, IconStar } from "./Icons";
import { circleApi } from "@shared/circle";
import type { NotificationItem } from "@shared/types";

const LANDING_URL = import.meta.env.VITE_LANDING_URL || "http://localhost:5172";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const initials = `${user?.first_name?.[0] || ""}${user?.last_name?.[0] || ""}`.toUpperCase();
  const [unread, setUnread] = useState(0);
  const [toast, setToast] = useState<NotificationItem | null>(null);
  const lastCount = useRef<number | null>(null);

  // Poll every 5s so new notifications appear quickly (local backend, no push server).
  useEffect(() => {
    let stop = false;
    const poll = async () => {
      try {
        const r = await circleApi.unreadCount();
        if (stop) return;
        const prev = lastCount.current;
        lastCount.current = r.unread;
        setUnread(r.unread);
        if (prev !== null && r.unread !== prev) {
          window.dispatchEvent(new Event("notifications-changed"));
        }
        if (prev !== null && r.unread > prev) {
          const latest = await circleApi.notifications({ page: 1 });
          if (!stop && latest.notifications.length > 0) setToast(latest.notifications[0]);
        }
      } catch {
        /* ignore — backend unreachable; retried on the next tick */
      }
    };
    poll();
    const t = setInterval(poll, 5000);
    return () => {
      stop = true;
      clearInterval(t);
    };
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 8000);
    return () => clearTimeout(t);
  }, [toast]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `sidebar-link${isActive ? " active" : ""}`;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a href={LANDING_URL} className="sidebar-brand">
          <span className="sidebar-brand-icon">📚</span>
          <div>
            <div className="sidebar-brand-text">BookVerse</div>
            <div className="sidebar-brand-badge">Seller</div>
          </div>
        </a>

        <nav className="sidebar-nav">
          <NavLink to="/" end className={navClass}>
            <IconDashboard /> Dashboard
          </NavLink>
          <NavLink to="/books" className={navClass}>
            <IconBooks /> My Books
          </NavLink>
          <NavLink to="/books/new" className={navClass}>
            <IconPlus /> Add Book
          </NavLink>
          <NavLink to="/books/bulk" className={navClass}>
            <IconStack /> Bulk Add
          </NavLink>
          <NavLink to="/orders" className={navClass}>
            <IconOrders /> Orders
          </NavLink>
          <NavLink to="/reviews" className={navClass}>
            <IconStar /> Reviews
          </NavLink>
          <NavLink to="/circle" className={navClass}>
            <IconBooks /> Circle
          </NavLink>
          <NavLink to="/buddy" className={navClass}>
            <IconOrders /> Buddies
          </NavLink>
          <NavLink to="/detective" className={navClass}>
            <IconStar /> Detective
          </NavLink>
          <NavLink to="/wishlist" className={navClass}>
            <IconStack /> Wishlist
          </NavLink>
          <NavLink to="/mystery" className={navClass}>
            <IconStar /> Mystery
          </NavLink>
          <NavLink to="/rentals" className={navClass}>
            <IconStack /> Rentals
          </NavLink>
          <NavLink to="/notifications" className={navClass}>
            <span aria-hidden>🔔</span> Notifications
            {unread > 0 && <span className="badge badge-placed" style={{ marginLeft: 6 }}>{unread}</span>}
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div>
              <div className="sidebar-user-name">{user?.first_name} {user?.last_name}</div>
              <div className="sidebar-user-role">{user?.email}</div>
            </div>
          </div>
          <button type="button" className="btn btn-ghost btn-sm" style={{ width: "100%", color: "#a8a29e" }} onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>

      {toast && (
        <div className="notify-toast" role="status" aria-live="polite">
          <div>
            <strong>🔔 {toast.title}</strong>
            {toast.message && <div className="notify-toast-body">{toast.message.split("\n").slice(0, 4).join("\n")}</div>}
          </div>
          <div className="notify-toast-actions">
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => { setToast(null); navigate("/notifications"); }}>Open</button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setToast(null)}>✕</button>
          </div>
        </div>
      )}

      <div className="main-content">
        <Outlet />
      </div>
    </div>
  );
}
