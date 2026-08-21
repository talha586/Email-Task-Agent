const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

let authToken = sessionStorage.getItem("authToken") || null;

export function getAuthToken() {
  return authToken;
}

export function setAuthToken(token) {
  authToken = token;
  if (token) {
    sessionStorage.setItem("authToken", token);
  } else {
    sessionStorage.removeItem("authToken");
  }
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) {
    headers.Authorization = `Token ${authToken}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    setAuthToken(null);
    throw new Error("401 Unauthorized — please log in again.");
  }

  if (!res.ok) {
    let detail = "";
    try {
      detail = await res.text();
    } catch {
      // ignore — use status only
    }
    throw new Error(
      `${res.status} ${res.statusText}${detail ? `: ${detail}` : ""}`,
    );
  }

  if (res.status === 204) return null;
  return res.json();
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/api-token-auth/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    throw new Error("Invalid username or password.");
  }

  const data = await res.json();
  setAuthToken(data.token);
  return data.token;
}

export function logout() {
  setAuthToken(null);
}

export function fetchTasks() {
  return request("/api/tasks/");
}

export function scanInbox(limit = 10) {
  return request(`/api/tasks/extract/?limit=${limit}`);
}

export function updateTask(id, data) {
  return request(`/api/tasks/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteTask(id) {
  return request(`/api/tasks/${id}/`, { method: "DELETE" });
}
