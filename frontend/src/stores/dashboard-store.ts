// VibeQueue — Dashboard state management (Zustand)

import { create } from "zustand";
import type {
  QueueEntry,
  Session,
  Alert,
  PlaybackStatus,
  TonightStats,
  Venue,
} from "@/types";
import { api } from "@/lib/api";

interface DashboardState {
  // Auth
  isAuthenticated: boolean;
  token: string | null;
  venueId: string | null;
  venue: Venue | null;

  // State
  queue: QueueEntry[];
  waitingPool: QueueEntry[];
  activeSessions: Session[];
  playback: PlaybackStatus | null;
  alerts: Alert[];
  tonight: TonightStats;
  mode: "A" | "B";

  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadDashboard: () => Promise<void>;
  setQueue: (queue: QueueEntry[]) => void;
  setPlayback: (playback: PlaybackStatus) => void;
  addAlert: (alert: Alert) => void;
  dismissAlert: (alertId: string) => void;
  openTable: (tableNumber: number) => Promise<Session>;
  closeTable: (sessionId: string) => Promise<void>;
  flagTable: (sessionId: string) => Promise<void>;
  skipSong: (queueId: string) => Promise<void>;
  pauseAll: () => Promise<void>;
  resumeAll: () => Promise<void>;
  toggleMode: () => Promise<void>;
  confirmManual: () => Promise<void>;
  setError: (error: string | null) => void;
  error: string | null;
  isLoading: boolean;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  isAuthenticated: false,
  token: null,
  venueId: null,
  venue: null,
  queue: [],
  waitingPool: [],
  activeSessions: [],
  playback: null,
  alerts: [],
  tonight: {
    tables_served: 0,
    music_revenue: 0,
    songs_played: 0,
    boost_conversion: 0,
  },
  mode: "A",
  error: null,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.staffLogin({ email, password });
      api.setToken(res.token);
      set({
        isAuthenticated: true,
        token: res.token,
        venueId: res.venue_id,
        isLoading: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Login failed",
        isLoading: false,
      });
    }
  },

  logout: () => {
    api.setToken(null);
    set({
      isAuthenticated: false,
      token: null,
      venueId: null,
      venue: null,
      queue: [],
      waitingPool: [],
      activeSessions: [],
      playback: null,
      alerts: [],
    });
  },

  loadDashboard: async () => {
    const { venueId } = get();
    if (!venueId) return;
    set({ isLoading: true });
    try {
      const state = await api.getDashboardState(venueId);
      set({
        venue: state.venue,
        queue: state.queue,
        waitingPool: state.waiting_pool,
        activeSessions: state.active_sessions,
        playback: state.playback,
        alerts: state.alerts,
        tonight: state.tonight,
        mode: state.playback.mode,
        isLoading: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to load dashboard",
        isLoading: false,
      });
    }
  },

  setQueue: (queue: QueueEntry[]) => {
    const active = queue.filter((q) => q.status === "active" || q.status === "playing");
    const waiting = queue.filter((q) => q.status === "waiting");
    set({ queue: active, waitingPool: waiting });
  },

  setPlayback: (playback: PlaybackStatus) => set({ playback }),

  addAlert: (alert: Alert) => {
    const { alerts } = get();
    set({ alerts: [alert, ...alerts] });
  },

  dismissAlert: async (alertId: string) => {
    try {
      await api.dismissAlert(alertId);
      const { alerts } = get();
      set({ alerts: alerts.filter((a) => a.id !== alertId) });
    } catch {
      // silent
    }
  },

  openTable: async (tableNumber: number) => {
    const { venueId } = get();
    if (!venueId) throw new Error("No venue");
    const session = await api.openTable(venueId, tableNumber);
    const { activeSessions } = get();
    set({ activeSessions: [...activeSessions, session] });
    return session;
  },

  closeTable: async (sessionId: string) => {
    await api.closeTable(sessionId);
    const { activeSessions } = get();
    set({
      activeSessions: activeSessions.map((s) =>
        s.id === sessionId ? { ...s, status: "billing" as const } : s
      ),
    });
  },

  flagTable: async (sessionId: string) => {
    await api.flagTable(sessionId);
    const { activeSessions } = get();
    set({
      activeSessions: activeSessions.map((s) =>
        s.id === sessionId ? { ...s, status: "flagged" as const } : s
      ),
    });
  },

  skipSong: async (queueId: string) => {
    await api.skipSong(queueId);
  },

  pauseAll: async () => {
    const { venueId } = get();
    if (!venueId) return;
    await api.pausePlayback(venueId);
    const { playback } = get();
    if (playback) set({ playback: { ...playback, is_paused: true } });
  },

  resumeAll: async () => {
    const { venueId } = get();
    if (!venueId) return;
    await api.resumePlayback(venueId);
    const { playback } = get();
    if (playback) set({ playback: { ...playback, is_paused: false } });
  },

  toggleMode: async () => {
    const { venueId, mode } = get();
    if (!venueId) return;
    const newMode = mode === "A" ? "B" : "A";
    await api.setVenueMode(venueId, newMode);
    set({ mode: newMode });
  },

  confirmManual: async () => {
    const { venueId } = get();
    if (!venueId) return;
    await api.confirmManualPlayback(venueId);
  },

  setError: (error: string | null) => set({ error }),
}));
