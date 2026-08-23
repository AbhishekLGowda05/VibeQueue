// VibeQueue — API client for communicating with FastAPI backend

import type {
  JoinRequest,
  JoinResponse,
  StaffLoginRequest,
  StaffLoginResponse,
  QueueEntry,
  BoostRequest,
  BoostResponse,
  BillingSummary,
  SongSearchResult,
  DashboardState,
  PlaybackStatus,
  Session,
  PlaybackEvent,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
  }

  // === Auth ===

  async guestJoin(data: JoinRequest): Promise<JoinResponse> {
    return this.request<JoinResponse>("/auth/join", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async staffLogin(data: StaffLoginRequest): Promise<StaffLoginResponse> {
    return this.request<StaffLoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // === Queue ===

  async getQueue(venueId: string): Promise<QueueEntry[]> {
    return this.request<QueueEntry[]>(`/queue/${venueId}`);
  }

  async requestSong(venueId: string, songId: string): Promise<QueueEntry> {
    return this.request<QueueEntry>("/queue/request", {
      method: "POST",
      body: JSON.stringify({ venue_id: venueId, song_id: songId }),
    });
  }

  async skipSong(queueId: string): Promise<void> {
    return this.request(`/queue/${queueId}/skip`, { method: "POST" });
  }

  async removeSong(queueId: string): Promise<void> {
    return this.request(`/queue/${queueId}`, { method: "DELETE" });
  }

  // === Boosts ===

  async createBoost(data: BoostRequest): Promise<BoostResponse> {
    return this.request<BoostResponse>("/boosts/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async cancelBoost(boostId: string): Promise<void> {
    return this.request(`/boosts/${boostId}`, { method: "DELETE" });
  }

  // === Songs ===

  async searchSongs(venueId: string, query: string): Promise<SongSearchResult[]> {
    return this.request<SongSearchResult[]>(
      `/songs/search?venue_id=${venueId}&q=${encodeURIComponent(query)}`
    );
  }

  // === Billing ===

  async getBillingSummary(sessionId: string): Promise<BillingSummary> {
    return this.request<BillingSummary>(`/billing/${sessionId}`);
  }

  async confirmBilling(sessionId: string): Promise<{ payment_order_id: string }> {
    return this.request(`/billing/${sessionId}/confirm`, { method: "POST" });
  }

  // === Playback ===

  async getPlaybackStatus(venueId: string): Promise<PlaybackStatus> {
    return this.request<PlaybackStatus>(`/playback/status/${venueId}`);
  }

  async reportPlaybackEvent(event: PlaybackEvent): Promise<void> {
    return this.request("/playback/events", {
      method: "POST",
      body: JSON.stringify(event),
    });
  }

  async pausePlayback(venueId: string): Promise<void> {
    return this.request(`/playback/pause`, {
      method: "POST",
      body: JSON.stringify({ venue_id: venueId }),
    });
  }

  async resumePlayback(venueId: string): Promise<void> {
    return this.request(`/playback/resume`, {
      method: "POST",
      body: JSON.stringify({ venue_id: venueId }),
    });
  }

  async confirmManualPlayback(venueId: string): Promise<void> {
    return this.request(`/playback/confirm-manual`, {
      method: "POST",
      body: JSON.stringify({ venue_id: venueId }),
    });
  }

  // === Dashboard ===

  async getDashboardState(venueId: string): Promise<DashboardState> {
    return this.request<DashboardState>(`/venues/${venueId}/dashboard`);
  }

  // === Sessions ===

  async openTable(venueId: string, tableNumber: number): Promise<Session> {
    return this.request<Session>("/sessions/open", {
      method: "POST",
      body: JSON.stringify({ venue_id: venueId, table_number: tableNumber }),
    });
  }

  async closeTable(sessionId: string): Promise<void> {
    return this.request(`/sessions/${sessionId}/billing`, { method: "POST" });
  }

  async flagTable(sessionId: string): Promise<void> {
    return this.request(`/sessions/${sessionId}/flag`, { method: "POST" });
  }

  async unflagTable(sessionId: string): Promise<void> {
    return this.request(`/sessions/${sessionId}/unflag`, { method: "POST" });
  }

  async dismissAlert(alertId: string): Promise<void> {
    return this.request(`/alerts/${alertId}/dismiss`, { method: "POST" });
  }

  async setVenueMode(venueId: string, mode: "A" | "B"): Promise<void> {
    return this.request(`/venues/${venueId}/mode`, {
      method: "POST",
      body: JSON.stringify({ mode }),
    });
  }
}

export const api = new ApiClient();
