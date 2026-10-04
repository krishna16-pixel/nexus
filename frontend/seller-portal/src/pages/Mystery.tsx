import { useState, type FormEvent } from "react";
import { PageHeader } from "../components/PageHeader";
import { circleApi } from "@shared/circle";
import type { Book } from "@shared/types";

export function Mystery() {
  const [form, setForm] = useState({ genres: "", favorite_authors: "", note: "" });
  const [pick, setPick] = useState<{ book: Book; reason: string; matched_terms: string[] } | null>(null);
  const [error, setError] = useState("");

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await circleApi.saveInterests({
        genres: form.genres || undefined,
        favorite_authors: form.favorite_authors || undefined,
        note: form.note || undefined,
      });
      const r = await circleApi.mystery();
      setPick(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Match failed");
    }
  };

  const surprise = async () => {
    setError("");
    try {
      const r = await circleApi.mystery();
      setPick(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Match failed");
    }
  };

  return (
    <>
      <PageHeader title="Mystery Book Match" subtitle="A surprise book from your interests" />
      <div className="page-body">
        <div className="card form-card" style={{ maxWidth: 560 }}>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={save}>
            <div className="form-group"><label>Favourite genres (comma separated)</label><input value={form.genres} onChange={(e) => setForm({ ...form, genres: e.target.value })} placeholder="mystery, history, python" /></div>
            <div className="form-group"><label>Favourite authors (comma separated)</label><input value={form.favorite_authors} onChange={(e) => setForm({ ...form, favorite_authors: e.target.value })} placeholder="Agatha Christie" /></div>
            <div className="page-actions">
              <button type="submit" className="btn btn-primary">Save + reveal match</button>
              <button type="button" className="btn btn-secondary" onClick={surprise}>Surprise me again</button>
            </div>
          </form>
        </div>
        {pick && (
          <div className="card" style={{ marginTop: "1.5rem", textAlign: "center", padding: "2rem" }}>
            <div style={{ fontSize: "3rem" }}>🎁</div>
            <h2>{pick.book.title}</h2>
            <p className="muted">by {pick.book.author} · ₹{pick.book.price}</p>
            <p>{pick.reason}</p>
          </div>
        )}
      </div>
    </>
  );
}
