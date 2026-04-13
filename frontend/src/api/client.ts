import type {
  KidProfile,
  Genre,
  HistoricalEvent,
  JobCreatedResponse,
  JobStatusResponse,
  JobCompleteResponse,
  AdminMe,
  AllowedEmail,
  StoryDetail,
  StoriesResponse,
  MyStoryDetail,
  MyStoriesResponse,
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

// Admin API

export async function fetchAdminMe(): Promise<AdminMe> {
  const res = await fetch(`${BASE}/admin/me`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function fetchAllowedEmails(): Promise<AllowedEmail[]> {
  const res = await fetch(`${BASE}/admin/emails`, { headers: authHeaders() });
  const data = await handleResponse<{ emails: AllowedEmail[] }>(res);
  return data.emails;
}

export async function addAllowedEmail(email: string): Promise<void> {
  const res = await fetch(`${BASE}/admin/emails`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ email }),
  });
  await handleResponse(res);
}

export async function removeAllowedEmail(email: string): Promise<void> {
  const res = await fetch(`${BASE}/admin/emails/${encodeURIComponent(email)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  await handleResponse(res);
}

export async function fetchStories(limit = 20, offset = 0): Promise<StoriesResponse> {
  const res = await fetch(`${BASE}/admin/stories?limit=${limit}&offset=${offset}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function fetchStory(id: number): Promise<StoryDetail> {
  const res = await fetch(`${BASE}/admin/stories/${id}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

// My Stories API

export async function fetchMyStories(limit = 20, offset = 0): Promise<MyStoriesResponse> {
  const res = await fetch(`${BASE}/my-stories?limit=${limit}&offset=${offset}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function fetchMyStory(id: number): Promise<MyStoryDetail> {
  const res = await fetch(`${BASE}/my-stories/${id}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export function getMyStoryAudioUrl(id: number): string {
  const token = getAuthToken();
  const url = `${BASE}/my-stories/${id}/audio`;
  if (token) return `${url}?token=${encodeURIComponent(token)}`;
  return url;
}
