import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchGenres,
  fetchHistoricalEvents,
  createCustomStory,
  createHistoricalStory,
  pollJobStatus,
  getAudioUrl,
} from './client';

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

function okResponse(data: unknown) {
  return { ok: true, json: () => Promise.resolve(data) };
}

function errorResponse(status: number, detail?: string) {
  return {
    ok: false,
    status,
    json: () => Promise.resolve(detail ? { detail } : {}),
  };
}

describe('fetchGenres', () => {
  it('returns genres on success', async () => {
    const genres = [{ id: 'adventure', name: 'Adventure', description: 'desc', icon: '🗺️' }];
    mockFetch.mockResolvedValueOnce(okResponse(genres));
    const result = await fetchGenres();
    expect(result).toEqual(genres);
    expect(mockFetch).toHaveBeenCalledWith('/api/genres');
  });

  it('throws on error response', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(500, 'Server error'));
    await expect(fetchGenres()).rejects.toThrow('Server error');
  });
});

describe('fetchHistoricalEvents', () => {
  it('returns events on success', async () => {
    const events = [{ id: 'moon', title: 'Moon Landing' }];
    mockFetch.mockResolvedValueOnce(okResponse(events));
    const result = await fetchHistoricalEvents();
    expect(result).toEqual(events);
  });
});

describe('createCustomStory', () => {
  it('sends correct payload', async () => {
    const job = { job_id: '123', status: 'processing', stages: [], current_stage: 'writing' };
    mockFetch.mockResolvedValueOnce(okResponse(job));

    const kid = { name: 'Arjun', age: 7 };
    const result = await createCustomStory(kid, 'fantasy', 'Magic adventure', 'exciting', 'short');

    expect(result).toEqual(job);
    expect(mockFetch).toHaveBeenCalledWith('/api/story/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kid, genre: 'fantasy', description: 'Magic adventure', mood: 'exciting', length: 'short' }),
    });
  });

  it('throws on error', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(422, 'Validation error'));
    await expect(createCustomStory({ name: 'A', age: 7 }, 'x', 'y')).rejects.toThrow('Validation error');
  });
});

describe('createHistoricalStory', () => {
  it('sends correct payload with mood and length', async () => {
    const job = { job_id: '456', status: 'processing', stages: [], current_stage: 'writing' };
    mockFetch.mockResolvedValueOnce(okResponse(job));

    const kid = { name: 'Arjun', age: 7 };
    await createHistoricalStory(kid, 'moon-landing', 'exciting', 'medium');

    expect(mockFetch).toHaveBeenCalledWith('/api/story/historical', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kid, event_id: 'moon-landing', mood: 'exciting', length: 'medium' }),
    });
  });
});

describe('pollJobStatus', () => {
  it('returns status on success', async () => {
    const status = { job_id: '123', status: 'processing', current_stage: 'writing', progress: 0, total_segments: 0 };
    mockFetch.mockResolvedValueOnce(okResponse(status));
    const result = await pollJobStatus('123');
    expect(result).toEqual(status);
    expect(mockFetch).toHaveBeenCalledWith('/api/story/status/123');
  });

  it('throws on 404', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(404, 'Job not found'));
    await expect(pollJobStatus('nonexistent')).rejects.toThrow('Job not found');
  });
});

describe('getAudioUrl', () => {
  it('returns correct URL', () => {
    expect(getAudioUrl('abc-123')).toBe('/api/story/audio/abc-123');
  });
});
