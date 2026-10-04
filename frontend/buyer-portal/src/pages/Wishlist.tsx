import { useEffect, useState, type FormEvent } from "react";
import { PageHeader } from "../components/PageHeader";
import { circleApi } from "@shared/circle";
import type { WishGroup, WishItem } from "@shared/types";

export function Wishlist() {
  const [groups, setGroups] = useState<WishGroup[]>([]);
  const [mine, setMine] = useState<WishItem[]>([]);
  const [form, setForm] = useState({ title: "", author: "", city: "", campus: "", max_price: "" });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try {
      const [g, m] = await Promise.all([circleApi.wishGroups(), circleApi.wishMine()]);
      setGroups(g.groups);
      setMine(m.wishes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await circleApi.wishAdd({
        title: form.title,
        author: form.author || undefined,
        city: form.city || undefined,
        campus: form.campus || undefined,
        max_price: form.max_price || undefined,
      });
      setForm({ title: "", author: "", city: "", campus: "", max_price: "" });
      setNotice("Wish added — grouped with others wanting the same book for bulk request.");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Add failed");
    }
  };

  return (
    <>
      <PageHeader title="Community Wishlist" subtitle="Same-book wishes grouped for bulk purchase" />
      <div className="page-body">
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        <div className="card form-card" style={{ maxWidth: 600, marginBottom: "1.5rem" }}>
          <h3>Wish for a book</h3>
          <form onSubmit={add}>
            <div className="form-row">
              <div className="form-group"><label>Title</label><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></div>
              <div className="form-group"><label>Author</label><input value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} /></div>
            </div>
            <div className="form-row">
              <div className="form-group"><label>City</label><input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></div>
              <div className="form-group"><label>Campus</label><input value={form.campus} onChange={(e) => setForm({ ...form, campus: e.target.value })} /></div>
            </div>
            <div className="form-group"><label>Max price ₹</label><input value={form.max_price} onChange={(e) => setForm({ ...form, max_price: e.target.value })} /></div>
            <button type="submit" className="btn btn-primary">Add wish</button>
          </form>
        </div>

        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>Bulk groups</h2>
        {groups.length === 0 ? (
          <p className="muted">No open wishes yet.</p>
        ) : (
          groups.map((g, i) => (
            <div key={i} className="card" style={{ marginBottom: "1rem" }}>
              <p><strong>{g.title}</strong> {g.author && <span className="muted">by {g.author}</span>}</p>
              <p>
                <span className={`badge badge-${g.bulk_eligible ? "delivered" : "placed"}`}>
                  {g.count} want this{g.bulk_eligible ? " · bulk eligible" : ` · needs ${g.bulk_min - g.count} more for bulk`}
                </span>
              </p>
              <p className="muted">{g.members.map((m) => `${m.city || "—"}${m.campus ? `/${m.campus}` : ""}`).join(" · ")}</p>
            </div>
          ))
        )}

        <h2 style={{ fontSize: "1.1rem", margin: "2rem 0 0.75rem" }}>My wishes</h2>
        {mine.map((w) => (
          <div key={w.id} className="card" style={{ marginBottom: "0.75rem" }}>
            <p><strong>{w.title}</strong> · {w.status}</p>
            {w.status === "open" && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => circleApi.wishClose(w.id).then(load)}>Close</button>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
