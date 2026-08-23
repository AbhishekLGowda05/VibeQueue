// VibeQueue — Core TypeScript types matching the FastAPI backend models

export interface Venue {
  id: string;
  slug: string;
  name: string;
  address: string;
  spend_cap: number; // e.g. 150 (INR)
  default_mode: "A" | "B"; // A=automated, B=manual
  is_active: boolean;
  queue_size: number; // active queue size (default 8)
  cooldown_minutes: number; // request cooldown per table
  created_at: string;
}

export interface Session {
  id: string;
  venue_id: string;
  table_number: number;
  table_code: string;
  guest_count: number;
  status: "active" | "billing" | "closed" | "flagged";
  total_spend: number;
  expires_at: string;
  created_at: string;
}

export interface Song {
  id: string;
  venue_id: string;
  title: string;
  artist: string;
  youtube_video_id: string;
  genre: string;
  enabled: boolean;
  time_available_after?: string; // e.g. "22:00"
}

export type QueueStatus = "active" | "waiting" | "playing" | "played" | "skipped" | "expired" | "cancelled";

export interface QueueEntry {
  id: string;
  venue_id: string;
  session_id: string;
  song_id: string;
  song_title: string;
  song_artist: string;
  youtube_video_id: string;
  table_number: number;
  position: number;
  boost_score: number;
  status: QueueStatus;
  requested_at: string;
}

export type BoostTier = 15 | 25 | 35;

export type BoostStatus = "pending" | "confirmed" | "cancelled";

export interface Boost {
  id: string;
  session_id: string;
  queue_id: string;
  song_title: string;
  amount: BoostTier;
  status: BoostStatus;
  created_at: string;
}

export interface BillingItem {
  boost_id: string;
  song_title: string;
  song_artist: string;
  amount: number;
  status: "confirmed" | "pending";
  played: boolean;
}

export interface BillingSummary {
  items: BillingItem[];
  confirmed_total: number;
  pending_total: number;
  gst_amount: number;
  grand_total: number;
}

export interface PlaybackCommand {
  id: string;
  venue_id: string;
  queue_id: string;
  youtube_video_id: string;
  song_title: string;
  song_artist: string;
  table_number: number;
  status: "pending" | "playing" | "completed" | "error";
  action: "play" | "pause" | "resume" | "skip";
  issued_at: string;
  acknowledged_at?: string;
}

export interface PlaybackEvent {
  venue_id: string;
  queue_id: string;
  youtube_video_id: string;
  event_type: "PLAYING" | "ENDED" | "ERROR" | "PAUSED" | "BUFFERING";
  error_code?: number;
  occurred_at: string;
}

export interface PlaybackStatus {
  venue_id: string;
  is_playing: boolean;
  is_paused: boolean;
  current_song?: QueueEntry;
  mode: "A" | "B";
}

export interface Alert {
  id: string;
  venue_id: string;
  type: "playback_stale" | "youtube_error" | "spend_cap" | "queue_empty";
  message: string;
  dismissed: boolean;
  created_at: string;
}

export interface DashboardState {
  venue: Venue;
  queue: QueueEntry[];
  waiting_pool: QueueEntry[];
  active_sessions: Session[];
  playback: PlaybackStatus;
  alerts: Alert[];
  tonight: TonightStats;
}

export interface TonightStats {
  tables_served: number;
  music_revenue: number;
  songs_played: number;
  boost_conversion: number; // percentage
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Auth
export interface JoinRequest {
  table_code: string;
  venue_slug: string;
}

export interface JoinResponse {
  token: string;
  session_id: string;
  table_number: number;
  venue_name: string;
  spend_cap: number;
}

export interface StaffLoginRequest {
  email: string;
  password: string;
}

export interface StaffLoginResponse {
  token: string;
  venue_id: string;
  venue_name: string;
  role: string;
}

export interface BoostRequest {
  song_id: string;
  queue_id: string;
  amount: BoostTier;
}

export interface BoostResponse {
  boost_id: string;
  status: string;
  new_queue_position: number;
  song_name: string;
  spend_remaining: number;
}

export interface SongSearchResult {
  id: string;
  title: string;
  artist: string;
  youtube_video_id: string;
  genre: string;
}
