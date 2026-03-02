import type {
  KidProfile,
  Genre,
  HistoricalEvent,
  JobCreatedResponse,
  JobStatusResponse,
  JobCompleteResponse,
} from "../types";

const BASE = "/api";

export async function fetchGenres(): Promise<Genre[]> {
  const res = await fetch(`${BASE}/genres`);
  return res.json();
}

export async function fetchHistoricalEvents(): Promise<HistoricalEvent[]> {
  const res = await fetch(`${BASE}/historical-events`);
  return res.json();
}

export async function createCustomStory(
  kid: KidProfile,
  genre: string,
  description: string
): Promise<JobCreatedResponse> {
  const res = await fetch(`${BASE}/story/custom`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kid, genre, description }),
  });
  return res.json();
}

export async function createHistoricalStory(
  kid: KidProfile,
  eventId: string
): Promise<JobCreatedResponse> {
  const res = await fetch(`${BASE}/story/historical`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kid, event_id: eventId }),
  });
  return res.json();
}

export async function pollJobStatus(
  jobId: string
): Promise<JobStatusResponse | JobCompleteResponse> {
  const res = await fetch(`${BASE}/story/status/${jobId}`);
  return res.json();
}

export function getAudioUrl(jobId: string): string {
  return `${BASE}/story/audio/${jobId}`;
}
