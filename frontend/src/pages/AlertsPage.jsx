import { useEffect, useState } from "react";
import { api } from "../api";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  async function loadAlerts() {
    const data = await api.listAlerts(false);
    setAlerts(data);
  }

  useEffect(() => {
    loadAlerts().catch((err) => setError(err.message));
  }, []);

  async function markRead(alertId) {
    try {
      await api.markAlertRead(alertId);
      await loadAlerts();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <h2>Alerts</h2>
      {error && <p className="error">{error}</p>}

      {alerts.length === 0 ? (
        <p>No alerts yet.</p>
      ) : (
        <ul className="alert-list">
          {alerts.map((alert) => (
            <li key={alert.id} className={alert.is_read ? "read" : "unread"}>
              <div>
                <span className={`badge ${alert.priority}`}>{alert.priority}</span>
                <strong>{alert.action}</strong>
                <p>{alert.reason}</p>
                <small>{new Date(alert.created_at).toLocaleString()}</small>
              </div>
              {!alert.is_read && (
                <button type="button" onClick={() => markRead(alert.id)}>
                  Mark read
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
