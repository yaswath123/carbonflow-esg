import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, Check, Database, FileUp, Lock, RefreshCw, X } from "lucide-react";
import "./styles.css";

const API_ROOT = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
const API_ORIGIN = API_ROOT.startsWith("http") ? API_ROOT : `https://${API_ROOT}`;
const API = API_ORIGIN.endsWith("/api") ? API_ORIGIN : `${API_ORIGIN.replace(/\/$/, "")}/api`;

function formatKg(value) {
  const number = Number(value || 0);
  if (number > 1000) return `${(number / 1000).toFixed(1)} tCO2e`;
  return `${number.toFixed(1)} kgCO2e`;
}

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [records, setRecords] = useState([]);
  const [status, setStatus] = useState("");
  const [source, setSource] = useState("");
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (source) params.set("source", source);
    const [dashboardResponse, recordsResponse] = await Promise.all([
      fetch(`${API}/dashboard/`),
      fetch(`${API}/records/?${params.toString()}`),
    ]);
    setDashboard(await dashboardResponse.json());
    const rows = await recordsResponse.json();
    setRecords(rows);
    setSelected((current) => rows.find((row) => row.id === current?.id) || rows[0] || null);
    setBusy(false);
  }

  useEffect(() => {
    load();
  }, [status, source]);

  async function review(action) {
    if (!selected) return;
    await fetch(`${API}/records/${selected.id}/review/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, note: action === "approve" ? "Looks consistent with source evidence." : "Needs source follow-up." }),
    });
    await load();
  }

  async function upload(sourceType, file) {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    await fetch(`${API}/upload/${sourceType}/`, { method: "POST", body: formData });
    await load();
  }

  const totals = dashboard?.totals || {};
  const scopeRows = dashboard?.by_scope || [];
  const riskRows = useMemo(() => records.filter((record) => record.flags.length), [records]);

  return (
    <main>
      <header className="topbar">
        <div>
          <p className="eyebrow">Analyst review</p>
          <h1>Breathe ESG ingestion console</h1>
        </div>
        <button className="iconButton" onClick={load} disabled={busy} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </header>

      <section className="metrics">
        <Metric label="Records" value={totals.records || 0} icon={<Database size={18} />} />
        <Metric label="Pending review" value={totals.pending || 0} icon={<AlertTriangle size={18} />} />
        <Metric label="Approved" value={totals.approved || 0} icon={<Check size={18} />} />
        <Metric label="Emissions" value={formatKg(totals.co2e_kg)} icon={<Lock size={18} />} />
      </section>

      <section className="workspace">
        <aside className="sidebar">
          <div className="panel">
            <h2>Uploads</h2>
            <Uploader label="SAP" source="sap" onUpload={upload} />
            <Uploader label="Utility" source="utility" onUpload={upload} />
            <Uploader label="Travel" source="travel" onUpload={upload} />
          </div>

          <div className="panel">
            <h2>Filters</h2>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="">All</option>
                <option value="pending">Pending</option>
                <option value="needs_attention">Needs attention</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="locked">Locked</option>
              </select>
            </label>
            <label>
              Source
              <select value={source} onChange={(event) => setSource(event.target.value)}>
                <option value="">All</option>
                <option value="sap">SAP</option>
                <option value="utility">Utility</option>
                <option value="travel">Travel</option>
              </select>
            </label>
          </div>

          <div className="panel compact">
            <h2>Scope split</h2>
            {scopeRows.map((row) => (
              <div className="splitRow" key={row.scope}>
                <span>{row.scope.replace("_", " ")}</span>
                <strong>{formatKg(row.co2e_kg)}</strong>
              </div>
            ))}
          </div>
        </aside>

        <section className="tableArea">
          <div className="tableHeader">
            <div>
              <h2>Incoming activity rows</h2>
              <p>{riskRows.length} rows have warnings that need analyst judgement.</p>
            </div>
            <div className="legend">
              <span className="dot pending" /> Pending
              <span className="dot warning" /> Attention
              <span className="dot approved" /> Approved
            </div>
          </div>

          <div className="tableShell">
            <table>
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Activity</th>
                  <th>Period</th>
                  <th>Quantity</th>
                  <th>CO2e</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr className={selected?.id === record.id ? "active" : ""} key={record.id} onClick={() => setSelected(record)}>
                    <td>{record.source_system.source_type}</td>
                    <td>
                      <strong>{record.activity_type.replaceAll("_", " ")}</strong>
                      <span>{record.facility?.name || record.raw_payload.traveler_ref || "No facility"}</span>
                    </td>
                    <td>{record.period_start} to {record.period_end}</td>
                    <td>{record.quantity_normalized || "?"} {record.unit_normalized}</td>
                    <td>{formatKg(record.co2e_kg)}</td>
                    <td><StatusBadge status={record.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="detail">
          <h2>Row evidence</h2>
          {selected ? (
            <>
              <div className="detailBlock">
                <p className="eyebrow">Source record</p>
                <strong>{selected.source_record_id}</strong>
                <span>{selected.source_system.name}</span>
              </div>
              <div className="flags">
                {selected.flags.length ? selected.flags.map((flag) => <span key={flag}>{flag}</span>) : <span>no flags</span>}
              </div>
              <dl>
                <dt>Scope</dt><dd>{selected.scope.replace("_", " ")}</dd>
                <dt>Original</dt><dd>{selected.quantity_original || "?"} {selected.unit_original}</dd>
                <dt>Normalized</dt><dd>{selected.quantity_normalized || "?"} {selected.unit_normalized}</dd>
                <dt>Emission factor</dt><dd>{selected.emission_factor || "missing"}</dd>
                <dt>Confidence</dt><dd>{selected.confidence_score}%</dd>
              </dl>
              <pre>{JSON.stringify(selected.raw_payload, null, 2)}</pre>
              <div className="actions">
                <button onClick={() => review("approve")}><Check size={16} />Approve</button>
                <button onClick={() => review("reject")}><X size={16} />Reject</button>
                <button onClick={() => review("lock")}><Lock size={16} />Lock</button>
              </div>
            </>
          ) : (
            <p>No rows loaded yet.</p>
          )}
        </aside>
      </section>
    </main>
  );
}

function Metric({ label, value, icon }) {
  return (
    <div className="metric">
      <div>{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Uploader({ label, source, onUpload }) {
  return (
    <label className="upload">
      <FileUp size={16} />
      <span>{label}</span>
      <input type="file" accept=".csv" onChange={(event) => onUpload(source, event.target.files[0])} />
    </label>
  );
}

function StatusBadge({ status }) {
  return <span className={`badge ${status}`}>{status.replace("_", " ")}</span>;
}

createRoot(document.getElementById("root")).render(<App />);
