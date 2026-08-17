const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

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
