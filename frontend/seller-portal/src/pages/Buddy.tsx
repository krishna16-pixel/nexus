import { useEffect, useState, type FormEvent } from "react";
import { PageHeader } from "../components/PageHeader";
import { useAuth } from "../context/AuthContext";
import { circleApi } from "@shared/circle";
import type { BuddyMatch, BuddyRequestItem, ReadingEntry } from "@shared/types";

export function Buddy() {
  const { user } = useAuth();
  const [mine, setMine] = useState<ReadingEntry[]>([]);
  const [matches, setMatches] = useState<Record<string, BuddyMatch[]>>({});
  const [inbox, setInbox] = useState<BuddyRequestItem[]>([]);
  const [form, setForm] = useState({ title: "", author: "", city: "", campus: "" });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try {
      const [m, inboxRes] = await Promise.all([circleApi.myReading(), circleApi.buddyInbox()]);
      setMine(m.reading);
      setInbox(inboxRes.requests);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mark = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await circleApi.markReading({ title: form.title, author: form.author || undefined, city: form.city || undefined, campus: form.campus || undefined, state: "reading" });
      setForm({ title: "", author: "", city: "", campus: "" });
      setNotice("Marked as currently reading — same-book readers appear below.");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  };

  const findBuddies = async (id: string) => {
    try {
      const r = await circleApi.buddies(id);
      setMatches((p) => ({ ...p, [id]: r.buddies }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  };

  return (
    <>
      <PageHeader title="Study Buddies" subtitle="Connect with users reading the same book" />
      <div className="page-body">
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        <div className="card form-card" style={{ maxWidth: 560, marginBottom: "1.5rem" }}>
          <h3>What are you reading?</h3>
          <form onSubmit={mark}>
            <div className="form-row">
              <div className="form-group"><label>Title</label><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></div>
              <div className="form-group"><label>Author</label><input value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} /></div>
            </div>
            <div className="form-row">
              <div className="form-group"><label>City</label><input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></div>
              <div className="form-group"><label>Campus</label><input value={form.campus} onChange={(e) => setForm({ ...form, campus: e.target.value })} /></div>
            </div>
            <button type="submit" className="btn btn-primary">Mark reading</button>
          </form>
        </div>

        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>My books + matches</h2>
        {mine.map((r) => (
          <div key={r.id} className="card" style={{ marginBottom: "1rem" }}>
            <p><strong>{r.title}</strong> {r.author && <span className="muted">by {r.author}</span>}</p>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => findBuddies(r.id)}>Find study buddies</button>
            {(matches[r.id] || []).map((b) => (
              <div key={b.id} style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center" }}>
                <span>{b.reader?.first_name} {b.reader?.last_name} {b.campus ? `· ${b.campus}` : ""}</span>
                {b.user_id !== user?.id && (
                  <button type="button" className="btn btn-primary btn-sm" onClick={async () => {
                    try {
                      await circleApi.buddyRequest(b.user_id);
                      setNotice("Buddy request sent.");
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Request failed");
                    }
                  }}>
                    Connect
                  </button>
                )}
              </div>
            ))}
          </div>
        ))}

        <h2 style={{ fontSize: "1.1rem", margin: "2rem 0 0.75rem" }}>Buddy inbox</h2>
        {inbox.length === 0 ? (
          <p className="muted">No buddy requests.</p>
        ) : (
          inbox.map((q) => (
            <div key={q.id} className="card" style={{ marginBottom: "0.75rem" }}>
              <p><strong>{q.requester?.first_name} {q.requester?.last_name}</strong> · {q.status}</p>
              {q.status === "pending" && (
                <div className="page-actions">
                  <button type="button" className="btn btn-primary btn-sm" onClick={() => circleApi.buddyDecide(q.id, true).then(load)}>Accept</button>
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => circleApi.buddyDecide(q.id, false).then(load)}>Decline</button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </>
  );
}
