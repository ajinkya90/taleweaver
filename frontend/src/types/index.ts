export type KidGender = "boy" | "girl";

export interface KidProfile {
  name: string;
  age: number;
  gender?: KidGender;
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

export interface AdminMe {
  email: string;
  is_admin: boolean;
}

export interface AllowedEmail {
  id: number;
  email: string;
  added_at: string;
}

export interface StoryLogEntry {
  id: number;
  job_id: string;
  user_email: string;
  story_type: string;
  kid_name: string;
  kid_age: number;
  genre: string | null;
  event_id: string | null;
  description: string | null;
  mood: string | null;
  length: string | null;
  title: string;
  duration_seconds: number;
  created_at: string;
}

export interface StoryDetail extends StoryLogEntry {
  prompt: string;
  story_text: string;
}

export interface StoriesResponse {
  stories: StoryLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface MyStoryEntry {
  id: number;
  title: string;
  kid_name: string;
  kid_age: number;
  story_type: string;
  genre: string | null;
  event_id: string | null;
  duration_seconds: number;
  created_at: string;
}

export interface MyStoryDetail extends MyStoryEntry {
  story_text: string;
  mood: string | null;
  length: string | null;
  description: string | null;
}

export interface MyStoriesResponse {
  stories: MyStoryEntry[];
  total: number;
  limit: number;
  offset: number;
}
