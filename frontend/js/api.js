const TOKEN_KEY = "hacsa_token";
const USER_KEY = "hacsa_user";
const EVENT_ID_KEY = "hacsa_event_id";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function isOpsRole(role) {
  return ["staff", "safety_officer", "ops_lead"].includes(role);
}

function destinationFor(role) {
  if (role === "speaker") return "/portal/index.html?role=speaker";
  if (role === "organiser") return "/organiser/index.html";
  if (isOpsRole(role)) return "/ops/command-center.html";
  return "/portal/index.html?role=participant";
}

function requireAuth(allowed) {
  const user = getUser();
  if (!getToken() || !user) {
    window.location.replace("/index.html");
    return null;
  }
  if (allowed && !allowed.includes(user.role)) {
    window.location.replace(destinationFor(user.role));
    return null;
  }
  return user;
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { ...options, headers });
  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!response.ok) {
    const detail = data && data.detail ? data.detail : response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

async function eventId() {
  const cached = localStorage.getItem(EVENT_ID_KEY);
  if (cached) return cached;
  const config = await api("/api/config");
  localStorage.setItem(EVENT_ID_KEY, config.event_id);
  return config.event_id;
}
