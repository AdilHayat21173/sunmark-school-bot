const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

function extractErrorMessage(data, fallback) {
  if (!data) return fallback;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    const first = data.detail[0];
    if (typeof first === "string") return first;
    if (first && typeof first === "object") {
      if (typeof first.msg === "string") return first.msg;
      if (Array.isArray(first.loc)) {
        return `${first.loc.join(".")}: ${first.msg || fallback}`;
      }
    }
  }
  return fallback;
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    let message = "Request failed";
    try {
      const data = await res.json();
      message = extractErrorMessage(data, message);
    } catch (_error) {
      message = `Request failed (${res.status})`;
    }
    const error = new Error(message);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

export async function register(email, password) {
  return request("/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
}

export async function login(email, password) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  return request("/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString()
  });
}

export async function getCurrentUser(token) {
  return request("/users/me", {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export async function createSession(token) {
  return request("/chat/session", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
}

export async function listSessions(token) {
  return request("/chat/sessions", {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export async function listMessages(token, sessionId) {
  return request(`/chat/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export async function sendMessage(token, sessionId, message) {
  return request(`/chat/${sessionId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message })
  });
}
