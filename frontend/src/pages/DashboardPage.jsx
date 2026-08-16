import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function DashboardPage() {
  const [reports, setReports] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.listReports(), api.listAlerts(true)])
      .then(([reportData, alertData]) => {
        setReports(reportData.slice(0, 5));
        setAlerts(alertData.slice(0, 5));
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      {error && <p className="error">{error}</p>}

      <section className="card-grid">
        <div className="card">
          <h3>Recent Reports</h3>
          {reports.length === 0 ? (
            <p>No reports yet. <Link to="/submit">Submit your first field report</Link>.</p>
          ) : (
            <ul>
              {reports.map((report) => (
                <li key={report.id}>
                  <Link to={`/reports/${report.id}`}>
                    {report.crop} — {new Date(report.created_at).toLocaleString()}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h3>Unread Alerts</h3>
          {alerts.length === 0 ? (
            <p>No unread alerts.</p>
          ) : (
            <ul>
              {alerts.map((alert) => (
                <li key={alert.id}>
                  <strong>[{alert.priority}]</strong> {alert.action}: {alert.reason}
                </li>
              ))}
            </ul>
          )}
          <Link to="/alerts">View all alerts</Link>
        </div>
      </section>
    </div>
  );
}
