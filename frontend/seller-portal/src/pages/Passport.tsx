import { useState, type FormEvent } from "react";
import { PageHeader } from "../components/PageHeader";
import { circleApi } from "@shared/circle";
import type { Book, PassportStamp } from "@shared/types";

export function Passport() {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [stamps, setStamps] = useState<PassportStamp[]>([]);
  const [book, setBook] = useState<Book | null>(null);
  const [readerCount, setReaderCount] = useState(0);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  const search = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const r = await circleApi.passport({ title, author: author || undefined });
      setStamps(r.stamps);
      setBook(r.book);
      setReaderCount(r.reader_count);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  };

  return (
    <>
      <PageHeader title="Book Passport" subtitle="Previous owners and readers of every second-hand book" />
      <div className="page-body">
        <form className="search-bar" onSubmit={search}>
          <input placeholder="Book title…" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <input placeholder="Author…" value={author} onChange={(e) => setAuthor(e.target.value)} style={{ maxWidth: 180 }} />
          <button type="submit" className="btn btn-primary">Trace passport</button>
        </form>
        {error && <div className="alert alert-error" style={{ marginTop: "1rem" }}>{error}</div>}
        {searched && (
          <div className="card" style={{ marginTop: "1.5rem" }}>
            <h3>{book?.title || title} {book ? "" : "(second-hand)"}</h3>
            <p className="muted">{readerCount} reader{readerCount !== 1 ? "s" : ""} in this passport · {stamps.length} transfers</p>
            {stamps.length === 0 ? (
              <p className="muted">No stamps yet — this book has not travelled in BookCircle.</p>
            ) : (
              <ul className="order-items-list">
                {stamps.map((s, i) => (
                  <li key={s.id}>
                    <span>#{i + 1} {s.from_user_id ? s.from_user_id.slice(0, 8) : "origin"} → {s.to_user_id.slice(0, 8)} <span className="muted">· {s.note || ""}</span></span>
                    <span className="muted">{new Date(s.created_at).toLocaleDateString()}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </>
  );
}
