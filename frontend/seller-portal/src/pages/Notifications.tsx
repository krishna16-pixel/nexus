import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { circleApi } from "@shared/circle";
import type { NotificationItem, PaginationMeta } from "@shared/types";

const KIND_ICON: Record<string, string> = {
  rent_request: "📩",
  rent_accepted: "✅",
  claim_received: "📋",
  claim_accepted: "✅",
  claim_declined: "❌",
  swap_proposed: "🔄",
  swap_accepted: "✅",
  swap_declined: "❌",
  detective_offer: "🕵️",
  detective_accepted: "✅",
  buddy_request: "🤝",
  buddy_accepted: "✅",
  buddy_declined: "❌",
  rental_due_soon: "⏰",
  rental_due_1_day: "🗓️",
  rental_due_1_hour: "⏳",
  rental_due: "⏰",
  rental_overdue: "🚨",
  rental_collection_notice: "📞",
  rental_return_requested: "📦",
  rental_return_cancelled: "↩️",
  rental_returned: "🎉",
  rental_returned_with_details: "💰",
  rental_overdue_fined: "💸",
  rental_started: "📚",
  order_placed: "🛒",
  order_placed_buyer: "🛒",
  order_confirmed: "✅",
  order_shipped: "🚚",
  order_delivered: "📦",
  order_cancelled: "❌",
  order_cancelled_by_buyer: "❌",
};

export function Notifications() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [error, setError] = useState("");

  const load = async (p: number, unread: boolean) => {
    try {
      const r = await circleApi.notifications({ page: p, unread_only: unread });
      setItems(r.notifications);
      setMeta(r.meta);
      setPage(r.meta.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  };

  useEffect(() => {
    load(1, unreadOnly);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unreadOnly]);

  const markRead = async (id: string) => {
    await circleApi.markNotificationRead(id);
    load(page, unreadOnly);
  };

  const markAll = async () => {
    await circleApi.markAllNotificationsRead();
    load(page, unreadOnly);
  };

  const fmtTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  return (
    <>
      <PageHeader title="Notifications" subtitle="Rent requests, due reminders, returns and more" />
      <div className="page-body">
        {error && <div className="alert alert-error">{error}</div>}
        <div className="page-actions" style={{ marginBottom: "1rem" }}>
          <button type="button" className={unreadOnly ? "btn btn-primary btn-sm" : "btn btn-ghost btn-sm"} onClick={() => setUnreadOnly((v) => !v)}>
            {unreadOnly ? "Showing unread" : "Show unread only"}
          </button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={markAll}>Mark all read</button>
        </div>

        {items.length === 0 ? (
          <div className="empty-state card"><p>No notifications yet. Rent requests and due reminders will appear here.</p></div>
        ) : (
          items.map((n) => (
            <div key={n.id} className="card" style={{ marginBottom: "0.75rem", opacity: n.is_read ? 0.75 : 1 }}>
              <p>
                <span style={{ marginRight: "0.5rem" }}>{KIND_ICON[n.kind] || "🔔"}</span>
                <strong>{n.title}</strong>
                {!n.is_read && <span className="badge badge-placed" style={{ marginLeft: "0.5rem" }}>new</span>}
              </p>
              {n.message && <p className="text-secondary" style={{ whiteSpace: "pre-line" }}>{n.message}</p>}
              <p className="muted" style={{ fontSize: "0.85rem" }}>{fmtTime(n.created_at)}</p>
              <div className="page-actions">
                {n.link && <Link to={n.link} className="btn btn-secondary btn-sm">Open →</Link>}
                {!n.is_read && <button type="button" className="btn btn-ghost btn-sm" onClick={() => markRead(n.id)}>Mark read</button>}
              </div>
            </div>
          ))
        )}

        {meta && meta.pages > 1 && (
          <div className="page-actions" style={{ marginTop: "1rem" }}>
            <button type="button" className="btn btn-ghost btn-sm" disabled={page <= 1} onClick={() => load(page - 1, unreadOnly)}>← Prev</button>
            <span className="muted">Page {meta.page} of {meta.pages}</span>
            <button type="button" className="btn btn-ghost btn-sm" disabled={page >= meta.pages} onClick={() => load(page + 1, unreadOnly)}>Next →</button>
          </div>
        )}
      </div>
    </>
  );
}
