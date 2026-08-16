import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

export default function ReportDetailPage() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getReport(id)
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [id]);

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!report) {
    return <p>Loading report...</p>;
  }

  return (
    <div>
      <h2>
        {report.crop} Report #{report.id}
      </h2>
      <p className="muted">
        {report.growth_stage} — ({report.latitude}, {report.longitude}) —{" "}
        {new Date(report.created_at).toLocaleString()}
      </p>

      <section className="card">
        <h3>Crop Advisory</h3>
        <pre className="advisory">{report.crop_advisory || "No advisory generated."}</pre>
      </section>

      <section className="card">
        <h3>Farm Decisions</h3>
        <ul className="decisions">
          {report.farm_decisions.map((decision, index) => (
            <li key={index}>
              <span className={`badge ${decision.priority}`}>{decision.priority}</span>
              <strong>{decision.action}</strong> — {decision.reason}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
