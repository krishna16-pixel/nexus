import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { useAuth } from "../context/AuthContext";
import { circleApi } from "@shared/circle";
import type { CircleClaim, CircleListing } from "@shared/types";

export function Circle() {
  const { user } = useAuth();
  const [open, setOpen] = useState<CircleListing[]>([]);
  const [mine, setMine] = useState<CircleListing[]>([]);
  const [filter, setFilter] = useState({ type: "", city: "", campus: "", q: "" });
  const [form, setForm] = useState({ title: "", author: "", offer_type: "sell", price: "", rent_fee: "", rent_days: "1", rent_hours: "0", rent_mins: "0", city: "", campus: "", description: "" });
  const [msg, setMsg] = useState("");
  const [claims, setClaims] = useState<Record<string, CircleClaim[]>>({});
  const [swapOffers, setSwapOffers] = useState<Record<string, Array<{ id: string; status: string; proposer_id: string; message?: string | null }>>>({});
  const [swapMine, setSwapMine] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try {
      const f: Record<string, string> = {};
      if (filter.type) f.type = filter.type;
      if (filter.city) f.city = filter.city;
      if (filter.campus) f.campus = filter.campus;
      if (filter.q) f.q = filter.q;
      const [o, m] = await Promise.all([circleApi.openListings(f), circleApi.myListings()]);
      setOpen(o.listings.filter((l) => l.owner_id !== user?.id));
      setMine(m.listings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setNotice("");
    try {
      await circleApi.createListing({
        title: form.title,
        author: form.author || undefined,
        offer_type: form.offer_type,
        price: form.offer_type === "sell" ? form.price : undefined,
        rent_fee: form.offer_type === "rent" ? form.rent_fee : undefined,
        rent_days: form.offer_type === "rent" ? parseInt(form.rent_days || "0", 10) : undefined,
        rent_hours: form.offer_type === "rent" ? parseInt(form.rent_hours || "0", 10) : undefined,
        rent_mins: form.offer_type === "rent" ? parseInt(form.rent_mins || "0", 10) : undefined,
        city: form.city || undefined,
        campus: form.campus || undefined,
        description: form.description || undefined,
      });
      setForm({ title: "", author: "", offer_type: "sell", price: "", rent_fee: "", rent_days: "1", rent_hours: "0", rent_mins: "0", city: "", campus: "", description: "" });
      setNotice("Listed in BookCircle.");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  };

  const claim = async (id: string) => {
    setError("");
    setNotice("");
    try {
      await circleApi.claim(id, msg || undefined);
      setNotice("Claim sent to owner.");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim failed");
    }
  };

  const viewClaims = async (id: string) => {
    try {
      const r = await circleApi.claimsFor(id);
      setClaims((p) => ({ ...p, [id]: r.claims }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load claims");
    }
  };

  const viewSwaps = async (id: string) => {
    try {
      const r = await circleApi.swapsFor(id);
      setSwapOffers((p) => ({ ...p, [id]: r.swaps }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load swaps");
    }
  };

  const myExchange = mine.filter((l) => l.offer_type === "exchange" && l.status === "open");

  return (
    <>
      <PageHeader title="BookCircle" subtitle="Sell, rent, donate or swap read books with the next reader" />
      <div className="page-body">
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}
        <p className="muted" style={{ marginBottom: "1rem" }}>
          <Link to="/price">Fair Price Calculator →</Link> · <Link to="/passport">Book Passport →</Link>
        </p>

        <div className="card form-card" style={{ maxWidth: 640, marginBottom: "1.5rem" }}>
          <h3>List a read book</h3>
          <form onSubmit={create}>
            <div className="form-row">
              <div className="form-group"><label>Title</label><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></div>
              <div className="form-group"><label>Author</label><input value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} /></div>
            </div>
            <div className="form-row">
              <div className="form-group"><label>Type</label>
                <select value={form.offer_type} onChange={(e) => setForm({ ...form, offer_type: e.target.value })}>
                  <option value="sell">Sell</option>
                  <option value="rent">Rent</option>
                  <option value="donate">Donate</option>
                  <option value="exchange">Exchange (swap)</option>
                </select>
              </div>
              {form.offer_type === "sell" && <div className="form-group"><label>Price ₹</label><input value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required /></div>}
              {form.offer_type === "rent" && (
                <>
                  <div className="form-group"><label>Rent fee ₹</label><input value={form.rent_fee} onChange={(e) => setForm({ ...form, rent_fee: e.target.value })} required /></div>
                  <div className="form-group"><label>Days</label><input type="number" min={0} max={365} value={form.rent_days} onChange={(e) => setForm({ ...form, rent_days: e.target.value })} required /></div>
                  <div className="form-group"><label>Hours</label><input type="number" min={0} max={23} value={form.rent_hours} onChange={(e) => setForm({ ...form, rent_hours: e.target.value })} /></div>
                  <div className="form-group"><label>Mins</label><input type="number" min={0} max={59} value={form.rent_mins} onChange={(e) => setForm({ ...form, rent_mins: e.target.value })} /></div>
                </>
              )}
            </div>
            <div className="form-row">
              <div className="form-group"><label>City</label><input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></div>
              <div className="form-group"><label>Campus (for campus exchange)</label><input value={form.campus} onChange={(e) => setForm({ ...form, campus: e.target.value })} /></div>
            </div>
            <div className="form-group"><label>Description</label><textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            <button type="submit" className="btn btn-primary">List book</button>
          </form>
        </div>

        <form className="search-bar" onSubmit={(e) => { e.preventDefault(); load(); }}>
          <input placeholder="Search title/author…" value={filter.q} onChange={(e) => setFilter({ ...filter, q: e.target.value })} />
          <input placeholder="City…" value={filter.city} onChange={(e) => setFilter({ ...filter, city: e.target.value })} style={{ maxWidth: 140 }} />
          <input placeholder="Campus…" value={filter.campus} onChange={(e) => setFilter({ ...filter, campus: e.target.value })} style={{ maxWidth: 140 }} />
          <select value={filter.type} onChange={(e) => setFilter({ ...filter, type: e.target.value })} style={{ maxWidth: 130 }}>
            <option value="">All types</option>
            <option value="sell">Sell</option>
            <option value="rent">Rent</option>
            <option value="donate">Donate</option>
            <option value="exchange">Exchange</option>
          </select>
          <button type="submit" className="btn btn-primary">Search</button>
        </form>

        <div className="form-group" style={{ marginTop: "1rem" }}>
          <label>Claim / swap message</label>
          <input value={msg} onChange={(e) => setMsg(e.target.value)} placeholder="Hi, I want this book…" />
        </div>

        <h2 style={{ fontSize: "1.1rem", margin: "1.5rem 0 0.75rem" }}>Open circle listings</h2>
        {open.length === 0 ? (
          <div className="empty-state card"><p>No open listings. Be the first to list a read book.</p></div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Book</th><th>Offer</th><th>Where</th><th></th></tr></thead>
              <tbody>
                {open.map((l) => (
                  <tr key={l.id}>
                    <td><strong>{l.title}</strong><br /><span className="muted">{l.author || ""} {l.price ? `· ₹${l.price}` : ""} {l.rent_fee ? `· ₹${l.rent_fee}/${[l.rent_days ? `${l.rent_days}d` : "", l.rent_hours ? `${l.rent_hours}h` : "", l.rent_mins ? `${l.rent_mins}m` : ""].filter(Boolean).join(" ") || "rent"}` : ""}</span></td>
                    <td>{l.offer_type}</td>
                    <td>{l.campus || l.city || "—"}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => claim(l.id)}>Claim</button>
                      {l.offer_type === "exchange" && myExchange.length > 0 && (
                        <select value={swapMine} onChange={(e) => setSwapMine(e.target.value)} style={{ marginLeft: "0.5rem", maxWidth: 150 }}>
                          <option value="">Swap with…</option>
                          {myExchange.map((m) => <option key={m.id} value={m.id}>{m.title}</option>)}
                        </select>
                      )}
                      {l.offer_type === "exchange" && swapMine && (
                        <button type="button" className="btn btn-secondary btn-sm" style={{ marginLeft: "0.5rem" }}
                          onClick={async () => {
                            try {
                              await circleApi.proposeSwap({ wanted_listing_id: l.id, offered_listing_id: swapMine, message: msg || undefined });
                              setNotice("Swap proposed — no money involved.");
                            } catch (err) {
                              setError(err instanceof Error ? err.message : "Swap failed");
                            }
                          }}>
                          Propose swap
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <h2 style={{ fontSize: "1.1rem", margin: "2rem 0 0.75rem" }}>My listings</h2>
        {mine.map((l) => (
          <div key={l.id} className="card" style={{ marginBottom: "1rem" }}>
            <p><strong>{l.title}</strong> · {l.offer_type} · {l.status}</p>
            {l.offer_type === "rent" && l.status === "claimed" && (
              <p><Link to="/rentals" className="btn btn-primary btn-sm">Manage return →</Link></p>
            )}
            <div className="page-actions">
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => viewClaims(l.id)}>View claims</button>
              {l.offer_type === "exchange" && <button type="button" className="btn btn-secondary btn-sm" onClick={() => viewSwaps(l.id)}>Swap offers</button>}
              {l.status === "open" && <button type="button" className="btn btn-ghost btn-sm" onClick={() => circleApi.closeListing(l.id).then(load)}>Close</button>}
            </div>
            {(claims[l.id] || []).map((c) => (
              <div key={c.id} style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center" }}>
                <span className="muted">{c.requester_id.slice(0, 8)}… · {c.status}</span>
                {c.status === "pending" && (
                  <>
                    <button type="button" className="btn btn-primary btn-sm" onClick={() => circleApi.acceptClaim(c.id).then(() => { setNotice("Claim accepted — passport stamped."); load(); })}>Accept</button>
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => circleApi.declineClaim(c.id).then(load)}>Decline</button>
                  </>
                )}
              </div>
            ))}
            {(swapOffers[l.id] || []).map((s) => (
              <div key={s.id} style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center" }}>
                <span className="muted">swap {s.proposer_id.slice(0, 8)}… · {s.status}</span>
                {s.status === "pending" && (
                  <>
                    <button type="button" className="btn btn-primary btn-sm" onClick={() => circleApi.acceptSwap(s.id).then(() => { setNotice("Swap accepted — both books claimed."); load(); })}>Accept swap</button>
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => circleApi.declineSwap(s.id).then(load)}>Decline</button>
                  </>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </>
  );
}
