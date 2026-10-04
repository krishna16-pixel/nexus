import { useState, type FormEvent } from "react";
import { PageHeader } from "../components/PageHeader";
import { circleApi } from "@shared/circle";
import type { PriceSuggestion } from "@shared/types";

export function Price() {
  const [form, setForm] = useState({ original_price: "", condition: "good", age_years: "1", edition: "" });
  const [result, setResult] = useState<PriceSuggestion | null>(null);
  const [error, setError] = useState("");

  const calc = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const r = await circleApi.priceSuggest({
        original_price: form.original_price || undefined,
        condition: form.condition,
        age_years: parseInt(form.age_years || "0", 10),
        edition: form.edition || undefined,
      });
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Calculation failed");
    }
  };

  return (
    <>
      <PageHeader title="Fair Price Calculator" subtitle="Suggested resale price from condition, edition and age" />
      <div className="page-body">
        <div className="card form-card" style={{ maxWidth: 520 }}>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={calc}>
            <div className="form-group"><label>Original price ₹</label><input value={form.original_price} onChange={(e) => setForm({ ...form, original_price: e.target.value })} required /></div>
            <div className="form-row">
              <div className="form-group"><label>Condition</label>
                <select value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })}>
                  <option value="new">New</option>
                  <option value="like_new">Like new</option>
                  <option value="good">Good</option>
                  <option value="fair">Fair</option>
                  <option value="poor">Poor</option>
                </select>
              </div>
              <div className="form-group"><label>Age (years)</label><input type="number" min={0} max={100} value={form.age_years} onChange={(e) => setForm({ ...form, age_years: e.target.value })} /></div>
            </div>
            <div className="form-group"><label>Edition (type “latest” for newest edition bonus)</label><input value={form.edition} onChange={(e) => setForm({ ...form, edition: e.target.value })} placeholder="e.g. 3rd edition" /></div>
            <button type="submit" className="btn btn-primary">Suggest price</button>
          </form>
          {result && (
            <div className="alert alert-success" style={{ marginTop: "1.5rem" }}>
              <div style={{ fontSize: "1.75rem", fontWeight: 700 }}>₹{result.suggested_price}</div>
              <p className="muted" style={{ margin: "0.5rem 0 0" }}>
                base ₹{result.breakdown.base_price} × condition {result.breakdown.condition_factor} × age {result.breakdown.age_factor} × edition {result.breakdown.edition_factor}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
