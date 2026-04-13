import type {
  KidProfile,
  Genre,
  HistoricalEvent,
  JobCreatedResponse,
  JobStatusResponse,
  JobCompleteResponse,
} from "../types";

const BASE = import.meta.env.VITE_API_URL || "/api";

const TOKEN_KEY = "taleweaver_token";

export function getAuthToken(): string {
  return sessionStorage.getItem(TOKEN_KEY) || "";
}

export function setAuthToken(token: string) {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
}

function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    setAuthToken("");
    window.location.reload();
    throw new Error("Authentication failed");
  }
  if (res.status === 403) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Your account is not authorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function verifyToken(token: string): Promise<boolean> {
  const res = await fetch(`${BASE}/genres`, {
    headers: { Authorization: `Bearer ${token}` },
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
  const token = getAuthToken();
  const url = `${BASE}/story/audio/${jobId}`;
  if (token) return `${url}?token=${encodeURIComponent(token)}`;
  return url;
}

export async function fetchAudioBlob(jobId: string): Promise<string> {
  const res = await fetch(`${BASE}/story/audio/${jobId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch audio: ${res.status}`);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
