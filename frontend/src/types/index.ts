export interface KidProfile {
  name: string;
  age: number;
  favorite_animal?: string;
  favorite_color?: string;
  hobby?: string;
  best_friend?: string;
  pet_name?: string;
  personality?: string;
}

export interface Genre {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface HistoricalEvent {
  id: string;
  title: string;
  figure: string;
  year: number;
  summary: string;
  key_facts: string[];
  thumbnail: string;
}

export interface JobCreatedResponse {
  job_id: string;
  status: string;
  stages: string[];
  current_stage: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  current_stage: string;
  progress: number;
  total_segments: number;
  error: string;
}

export interface JobCompleteResponse {
  job_id: string;
  status: string;
  title: string;
  duration_seconds: number;
  audio_url: string;
  transcript: string;
}

export type StoryType = "custom" | "historical";

export type StoryMood = "exciting" | "heartwarming" | "funny" | "mysterious";
export type StoryLength = "short" | "medium" | "long";

export type WizardStep =
  | "hero"
  | "craft"
  | "story";
