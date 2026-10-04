import { useEffect, useState } from "react";
import { PageHeader } from "../components/PageHeader";
import { circleApi } from "@shared/circle";
import type { Rental } from "@shared/types";

function dueLabel(r: Rental): string {
  if (r.status === "returned") return "Returned";
  if (r.is_overdue) {
    const days = r.days_left !== null && r.days_left !== undefined ? Math.abs(r.days_left) : 0;
    return days <= 0 ? "Overdue — due time passed" : `Overdue by ${days} day${days === 1 ? "" : "s"}`;
  }
  try {
    const ms = new Date(r.due_date).getTime() - Date.now();
    if (ms <= 0) return "Time completed — return now";
    const totalMins = Math.floor(ms / 60000);
    const d = Math.floor(totalMins / 1440);
    const h = Math.floor((totalMins % 1440) / 60);
    const m = totalMins % 60;
    const parts: string[] = [];
    if (d > 0) parts.push(`${d}d`);
    if (h > 0) parts.push(`${h}h`);
    if (m > 0 || parts.length === 0) parts.push(`${m}m`);
    return `Due in ${parts.join(" ")}`;
  } catch {
    if (r.days_left === 0) return "Due today";
    if (r.days_left === 1) return "Due tomorrow";
    return `Due in ${r.days_left ?? "—"} days`;
  }
}

function statusBadge(r: Rental) {
  if (r.status === "returned") return <span className="muted">returned</span>;
  if (r.is_overdue) return <span className="badge badge-overdue">overdue</span>;
  if (r.status === "return_requested") return <span className="badge badge-return_requested">return requested</span>;
  return <span className="badge badge-active">active</span>;
}
function paymentDetails(r: Rental, ownerView = false) {
  const rent = r.listing?.rent_fee || "0.00";
  const fine = r.fine_due || r.fine_preview || "0.00";
  const total = ownerView ? (r.amount_to_collect || r.amount_due || "0.00") : (r.amount_to_pay || r.amount_due || "0.00");
  return (
    <div className="muted" style={{ fontSize: "0.82rem", marginTop: 4 }}>
      <div>Rent ₹{rent} · Fine ₹{fine}</div>
      <strong>{ownerView ? "To collect" : "To pay"}: ₹{total}</strong>
      {r.time_remaining && r.status !== "returned" && <div>Time left: {r.time_remaining}</div>}
      {r.return_requested_at && <div>Return requested: {new Date(r.return_requested_at).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</div>}
    </div>
  );
}

function contactDetails(person: Rental["owner"], label: string) {
  if (!person) return null;
  return (
    <div className="muted" style={{ fontSize: "0.82rem", marginTop: 4 }}>
      <div><strong>{label}:</strong> {person.name || `${person.first_name} ${person.last_name}`}</div>
      <div>{person.email}{person.phone ? ` · ${person.phone}` : ""}</div>
      <div>{person.address || "Handover address not provided"}</div>
    </div>
  );
}

export function Rentals() {
  const [mine, setMine] = useState<Rental[]>([]);
  const [out, setOut] = useState<Rental[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modalRental, setModalRental] = useState<Rental | null>(null);
  const [modalData, setModalData] = useState({ fine_amount: "", amount_collected: "", payment_method: "", payment_note: "" });

  const load = async () => {
    try {
      const [m, o] = await Promise.all([circleApi.myRentals(), circleApi.rentedOut()]);
      setMine(m.rentals);
      setOut(o.rentals);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const act = async (fn: () => Promise<unknown>, okMsg: string) => {
    setError("");
    setNotice("");
    try {
      await fn();
      setNotice(okMsg);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  };

  const openCompleteModal = (r: Rental) => {
    setModalRental(r);
    setModalData({
      fine_amount: r.fine_amount ? String(r.fine_amount) : "0",
      amount_collected: r.amount_collected ? String(r.amount_collected) : "",
      payment_method: r.payment_method || "",
      payment_note: r.payment_note || "",
    });
  };

  const closeModal = () => {
    setModalRental(null);
    setModalData({ fine_amount: "", amount_collected: "", payment_method: "", payment_note: "" });
  };

  const submitComplete = async () => {
    if (!modalRental) return;
    setError("");
    setNotice("");
    try {
      await circleApi.completeReturn(modalRental.id, modalData);
      setNotice("Return completed with details — renter notified.");
      closeModal();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  };



  const fmtDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString();
    } catch {
      return iso;
    }
  };

  const fmtDateTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    } catch {
      return iso;
    }
  };

  return (
    <>
      <PageHeader title="My Rentals" subtitle="Books you rented — return before the due date" />
      <div className="page-body">
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        {mine.length === 0 ? (
          <div className="empty-state card"><p>You have no active rentals. Claim a rent listing in Circle.</p></div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Book</th><th>Due</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {mine.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.listing?.title || "Book"}</strong>
                      <br /><span className="muted">since {fmtDate(r.start_date)}</span>
                      {contactDetails(r.owner, "Owner")}
                    </td>
                    <td>
                      {fmtDateTime(r.due_date)}
                      <br /><span className="muted">{dueLabel(r)}</span>
                      {paymentDetails(r)}
                    </td>
                    <td>{statusBadge(r)}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {r.status === "active" && !r.is_overdue && (
                        <button type="button" className="btn btn-primary btn-sm" onClick={() => act(() => circleApi.requestReturn(r.id), "Return requested — the owner will confirm.")}>Return book</button>
                      )}
                      {r.status === "active" && r.is_overdue && (
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => act(() => circleApi.requestReturn(r.id), "Return requested — the owner will confirm.")}>Return now (overdue)</button>
                      )}
                      {r.status === "return_requested" && (
                        <button type="button" className="btn btn-ghost btn-sm" onClick={() => act(() => circleApi.cancelReturn(r.id), "Return request withdrawn.")}>Withdraw request</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <h2 style={{ fontSize: "1.1rem", margin: "2rem 0 0.75rem" }}>Rented out by me</h2>
        {out.length === 0 ? (
          <p className="muted">Nobody is renting your books right now.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Book</th><th>Renter</th><th>Due</th><th>Status</th><th>Fine / Collected</th><th></th></tr></thead>
              <tbody>
                {out.map((r) => (
                  <tr key={r.id}>
                    <td><strong>{r.listing?.title || "Book"}</strong></td>
                    <td>{contactDetails(r.renter, "Renter") || <span className="muted">{r.renter_id.slice(0, 8)}…</span>}</td>
                    <td>{fmtDateTime(r.due_date)}<br /><span className="muted">{dueLabel(r)}</span>{paymentDetails(r, true)}</td>
                    <td>{statusBadge(r)}</td>
                    <td>
                      {r.fine_amount && Number(r.fine_amount) > 0 && (
                        <span className="badge badge-overdue">Fine: ₹{Number(r.fine_amount).toFixed(2)}</span>
                      )}
                      {r.amount_collected && Number(r.amount_collected) > 0 && (
                        <span className="badge badge-active" style={{ marginLeft: 6 }}>Collected: ₹{Number(r.amount_collected).toFixed(2)}</span>
                      )}
                    </td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {r.status === "active" && !r.is_overdue && (
                        <button type="button" className="btn btn-primary btn-sm" onClick={() => act(() => circleApi.confirmReturn(r.id), "Return confirmed — listing is open again.")}>Complete rental</button>
                      )}
                      {r.status === "active" && r.is_overdue && (
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => act(() => circleApi.confirmReturn(r.id), "Return confirmed — listing is open again.")}>Complete (overdue)</button>
                      )}
                      {r.status === "active" && r.is_overdue && (
                        <button type="button" className="btn btn-warning btn-sm" style={{ marginLeft: 4 }} onClick={() => act(() => circleApi.applyFine(r.id), "10% overdue fine applied — renter notified.")}>Apply 10% fine</button>
                      )}
                      {r.status === "return_requested" && (
                        <>
                          <button type="button" className="btn btn-primary btn-sm" onClick={() => act(() => circleApi.confirmReturn(r.id), "Return confirmed — listing is open again.")}>Confirm receipt</button>
                          <button type="button" className="btn btn-secondary btn-sm" style={{ marginLeft: 4 }} onClick={() => openCompleteModal(r)}>Complete with details</button>
                        </>
                      )}
                      {r.status === "active" && (
                        <button type="button" className="btn btn-secondary btn-sm" style={{ marginLeft: 4 }} onClick={() => openCompleteModal(r)}>Complete with details</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {modalRental && (
          <div className="modal-overlay" onClick={closeModal}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <h3>Complete Return for "{modalRental.listing?.title || "Book"}"</h3>
              {contactDetails(modalRental.renter, "Renter")}
              <div className="card" style={{ margin: "0.75rem 0", padding: "0.75rem" }}>
                <strong>Return summary</strong>
                <div>Due: {fmtDateTime(modalRental.due_date)} · Returned now: {fmtDateTime(new Date().toISOString())}</div>
                <div>Expected: ₹{modalRental.amount_to_collect || modalRental.amount_due || "0.00"} · Fine due: ₹{modalRental.fine_due || "0.00"}</div>
              </div>
              <div className="form-group"><label>Fine Amount ₹</label><input type="number" step="0.01" min="0" value={modalData.fine_amount} onChange={(e) => setModalData({ ...modalData, fine_amount: e.target.value })} /></div>
              <div className="form-group"><label>Amount Collected ₹</label><input type="number" step="0.01" min="0" value={modalData.amount_collected} onChange={(e) => setModalData({ ...modalData, amount_collected: e.target.value })} /></div>
              <div className="form-group"><label>Payment Method</label><input value={modalData.payment_method} onChange={(e) => setModalData({ ...modalData, payment_method: e.target.value })} placeholder="Cash / UPI / Card" /></div>
              <div className="form-group"><label>Payment Note</label><textarea value={modalData.payment_note} onChange={(e) => setModalData({ ...modalData, payment_note: e.target.value })} placeholder="Any additional notes…" /></div>
              <div className="page-actions">
                <button type="button" className="btn btn-ghost" onClick={closeModal}>Cancel</button>
                <button type="button" className="btn btn-primary" onClick={submitComplete}>Complete Return</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
