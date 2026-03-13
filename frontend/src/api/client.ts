import type {
  KidProfile,
  Genre,
  HistoricalEvent,
  JobCreatedResponse,
  JobStatusResponse,
  JobCompleteResponse,
} from "../types";

const BASE = "/api";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchGenres(): Promise<Genre[]> {
  const res = await fetch(`${BASE}/genres`);
  return handleResponse(res);
}

export async function fetchHistoricalEvents(): Promise<HistoricalEvent[]> {
  const res = await fetch(`${BASE}/historical-events`);
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
    headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kid, event_id: eventId, mood, length }),
  });
  return handleResponse(res);
}

export async function pollJobStatus(
  jobId: string
): Promise<JobStatusResponse | JobCompleteResponse> {
  const res = await fetch(`${BASE}/story/status/${jobId}`);
  return handleResponse(res);
}

export function getAudioUrl(jobId: string): string {
  return `${BASE}/story/audio/${jobId}`;
}
