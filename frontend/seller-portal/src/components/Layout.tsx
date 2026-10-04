import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { IconBooks, IconDashboard, IconOrders, IconPlus, IconStack, IconStar } from "./Icons";
import { circleApi } from "@shared/circle";

const LANDING_URL = import.meta.env.VITE_LANDING_URL || "http://localhost:5172";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const initials = `${user?.first_name?.[0] || ""}${user?.last_name?.[0] || ""}`.toUpperCase();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let stop = false;
    const fetchCount = async () => {
      try {
        const r = await circleApi.unreadCount();
        if (!stop) setUnread(r.unread);
      } catch {
        /* ignore — notifications unavailable */
      }
    };
    fetchCount();
    const t = setInterval(fetchCount, 30000);
    return () => {
      stop = true;
      clearInterval(t);
    };
  }, []);

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

      <div className="main-content">
        <Outlet />
      </div>
    </div>
  );
}
