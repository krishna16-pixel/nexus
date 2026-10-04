import { useEffect, useState, type FormEvent } from "react";
import { PageHeader } from "../components/PageHeader";
import { circleApi } from "@shared/circle";
import type { DetectiveOffer, DetectiveRequest } from "@shared/types";

export function Detective() {
  const [open, setOpen] = useState<DetectiveRequest[]>([]);
  const [form, setForm] = useState({ title: "", author: "", max_price: "", city: "", note: "" });
  const [offerPrice, setOfferPrice] = useState("");
  const [offerMsg, setOfferMsg] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try {
      const r = await circleApi.detectiveList();
      setOpen(r.requests);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await circleApi.detectiveCreate({
        title: form.title,
        author: form.author || undefined,
        max_price: form.max_price || undefined,
        city: form.city || undefined,
        note: form.note || undefined,
      });
      setForm({ title: "", author: "", max_price: "", city: "", note: "" });
      setNotice("Detective request posted — sellers can now respond.");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Post failed");
    }
  };

  const offer = async (id: string) => {
    try {
      await circleApi.detectiveOffer(id, { price: offerPrice || undefined, message: offerMsg || undefined });
      setNotice("Offer sent. The requester can accept it.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Offer failed");
    }
  };

  return (
    <>
      <PageHeader title="Book Detective" subtitle="Rare and old books traced across sellers" />
      <div className="page-body">
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        <div className="card form-card" style={{ maxWidth: 600, marginBottom: "1.5rem" }}>
          <h3>Request a rare / old book</h3>
          <form onSubmit={create}>
            <div className="form-row">
              <div className="form-group"><label>Title</label><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></div>
              <div className="form-group"><label>Author</label><input value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} /></div>
            </div>
            <div className="form-row">
              <div className="form-group"><label>Max price ₹</label><input value={form.max_price} onChange={(e) => setForm({ ...form, max_price: e.target.value })} /></div>
              <div className="form-group"><label>City</label><input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></div>
            </div>
            <div className="form-group"><label>Note</label><textarea value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} /></div>
            <button type="submit" className="btn btn-primary">Post request</button>
          </form>
        </div>

        <div className="form-row" style={{ maxWidth: 600 }}>
          <div className="form-group"><label>Offer price ₹</label><input value={offerPrice} onChange={(e) => setOfferPrice(e.target.value)} /></div>
          <div className="form-group"><label>Offer message</label><input value={offerMsg} onChange={(e) => setOfferMsg(e.target.value)} placeholder="I have this edition…" /></div>
        </div>

        {open.map((r) => (
          <DetectiveCard key={r.id} item={r} onOffer={() => offer(r.id)} onDone={load} />
        ))}
      </div>
    </>
  );
}

function DetectiveCard({ item, onOffer, onDone }: { item: DetectiveRequest; onOffer: () => void; onDone: () => void }) {
  const [offers, setOffers] = useState<DetectiveOffer[] | null>(null);

  const view = async () => {
    const r = await circleApi.detectiveOffers(item.id);
    setOffers(r.offers);
  };

  const acceptOffer = async (offerId: string) => {
    await circleApi.detectiveAccept(offerId);
    onDone();
  };

  return (
    <div className="card" style={{ marginBottom: "1rem" }}>
      <p><strong>{item.title}</strong> {item.author && <span className="muted">by {item.author}</span>}</p>
      <p className="muted">{item.max_price ? `up to ₹${item.max_price}` : ""} {item.city || ""} · {item.status}</p>
      {item.note && <p>{item.note}</p>}
      <div className="page-actions">
        <button type="button" className="btn btn-secondary btn-sm" onClick={onOffer}>Offer this book</button>
        <button type="button" className="btn btn-ghost btn-sm" onClick={view}>View offers</button>
      </div>
      {offers === null ? null : offers.map((o) => (
        <div key={o.id} style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center" }}>
          <span className="muted">{o.price ? `₹${o.price}` : ""} {o.message || ""} · {o.status}</span>
          {o.status === "pending" && (
            <button type="button" className="btn btn-primary btn-sm" onClick={() => acceptOffer(o.id)}>Accept</button>
          )}
        </div>
      ))}
    </div>
  );
}
