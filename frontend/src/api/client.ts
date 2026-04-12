import type {
  KidProfile,
  Genre,
  HistoricalEvent,
  JobCreatedResponse,
  JobStatusResponse,
  JobCompleteResponse,
} from "../types";

const BASE = import.meta.env.VITE_API_URL || "/api";

const PASSWORD_KEY = "taleweaver_password";

export function getStoredPassword(): string {
  return sessionStorage.getItem(PASSWORD_KEY) || "";
}

export function setStoredPassword(pw: string) {
  sessionStorage.setItem(PASSWORD_KEY, pw);
}

export function clearStoredPassword() {
  sessionStorage.removeItem(PASSWORD_KEY);
}

function authHeaders(): Record<string, string> {
  const pw = getStoredPassword();
  if (pw) return { Authorization: `Bearer ${pw}` };
  return {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    clearStoredPassword();
    window.location.reload();
    throw new Error("Invalid password");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function verifyPassword(password: string): Promise<boolean> {
  const res = await fetch(`${BASE}/genres`, {
    headers: { Authorization: `Bearer ${password}` },
  });
  return res.ok;
}

export async function fetchGenres(): Promise<Genre[]> {
  const res = await fetch(`${BASE}/genres`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function fetchHistoricalEvents(): Promise<HistoricalEvent[]> {
  const res = await fetch(`${BASE}/historical-events`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function createCustomStory(
  kid: KidProfile,
  genre: string,
  description: string,
  mood?: string,
  length?: string,
): Promise<JobCreatedResponse> {
  const res = await fetch(`${BASE}/story/custom`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ kid, genre, description, mood, length }),
  });
  return handleResponse(res);
}

export async function createHistoricalStory(
  kid: KidProfile,
  eventId: string,
  mood?: string,
  length?: string,
): Promise<JobCreatedResponse> {
  const res = await fetch(`${BASE}/story/historical`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ kid, event_id: eventId, mood, length }),
  });
  return handleResponse(res);
}

export async function pollJobStatus(
  jobId: string
): Promise<JobStatusResponse | JobCompleteResponse> {
  const res = await fetch(`${BASE}/story/status/${jobId}`, { headers: authHeaders() });
  return handleResponse(res);
}

export function getAudioUrl(jobId: string): string {
  const pw = getStoredPassword();
  const url = `${BASE}/story/audio/${jobId}`;
  if (pw) return `${url}?token=${encodeURIComponent(pw)}`;
  return url;
}
