const API_BASE = import.meta.env.VITE_API_URL || "";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function clearToken() {
  localStorage.removeItem("token");
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Request failed");
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export const api = {
  register: (data) =>
    request("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  login: async (data) => {
    const result = await request("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    setToken(result.access_token);
    return result;
  },
  logout: () => clearToken(),
  me: () => request("/api/auth/me"),
  listFields: () => request("/api/fields"),
  createField: (data) =>
    request("/api/fields", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  listReports: () => request("/api/reports"),
  getReport: (id) => request(`/api/reports/${id}`),
  runReportWithImage: (formData) =>
    request("/api/reports/run-with-image", {
      method: "POST",
      body: formData,
    }),
  listAlerts: (unreadOnly = false) =>
    request(`/api/alerts?unread_only=${unreadOnly}`),
  markAlertRead: (id) =>
    request(`/api/alerts/${id}/read`, { method: "PATCH" }),
  isLoggedIn: () => !!getToken(),
};
