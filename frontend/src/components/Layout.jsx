import { Link, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Layout() {
  const navigate = useNavigate();

  function handleLogout() {
    api.logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <h1>Precision Agriculture</h1>
          <p>Multi-agent crop advisory &amp; farm decisions</p>
        </div>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/fields">Fields</Link>
          <Link to="/submit">New Report</Link>
          <Link to="/alerts">Alerts</Link>
          <button type="button" onClick={handleLogout}>Logout</button>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
