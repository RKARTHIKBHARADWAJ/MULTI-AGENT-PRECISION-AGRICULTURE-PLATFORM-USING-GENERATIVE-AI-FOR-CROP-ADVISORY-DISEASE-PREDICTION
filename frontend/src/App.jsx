import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import AlertsPage from "./pages/AlertsPage";
import DashboardPage from "./pages/DashboardPage";
import FieldsPage from "./pages/FieldsPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ReportDetailPage from "./pages/ReportDetailPage";
import SubmitReportPage from "./pages/SubmitReportPage";
import { api } from "./api";

function PrivateRoute({ children }) {
  if (!api.isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="fields" element={<FieldsPage />} />
        <Route path="submit" element={<SubmitReportPage />} />
        <Route path="reports/:id" element={<ReportDetailPage />} />
        <Route path="alerts" element={<AlertsPage />} />
      </Route>
    </Routes>
  );
}
