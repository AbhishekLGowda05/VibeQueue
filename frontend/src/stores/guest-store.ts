// VibeQueue — Guest state management (Zustand)

import { create } from "zustand";
import type { QueueEntry, BillingSummary, JoinResponse } from "@/types";
import { api } from "@/lib/api";

interface GuestState {
  // Auth
  isJoined: boolean;
  token: string | null;
  sessionId: string | null;
  venueId: string | null;
  venueSlug: string | null;
  venueName: string | null;
  tableNumber: number | null;
  spendCap: number;
  spendRemaining: number;

  // Queue
  queue: QueueEntry[];
  mySongs: QueueEntry[];
  isLoading: boolean;
  error: string | null;

  // Billing
  isBillingOpen: boolean;
  billingSummary: BillingSummary | null;

  // Actions
  join: (tableCode: string, venueSlug: string) => Promise<void>;
  leave: () => void;
  setQueue: (queue: QueueEntry[]) => void;
  updateQueueEntry: (entry: QueueEntry) => void;
  removeQueueEntry: (id: string) => void;
  requestSong: (songId: string) => Promise<void>;
  boostSong: (queueId: string, songId: string, amount: 15 | 25 | 35) => Promise<void>;
  openBilling: () => void;
  setBillingSummary: (summary: BillingSummary) => void;
  setError: (error: string | null) => void;
}

export const useGuestStore = create<GuestState>((set, get) => ({
  isJoined: false,
  token: null,
  sessionId: null,
  venueId: null,
  venueSlug: null,
  venueName: null,
  tableNumber: null,
  spendCap: 150,
  spendRemaining: 150,
  queue: [],
  mySongs: [],
  isLoading: false,
  error: null,
  isBillingOpen: false,
  billingSummary: null,

  join: async (tableCode: string, venueSlug: string) => {
    set({ isLoading: true, error: null });
    try {
      const res: JoinResponse = await api.guestJoin({
        table_code: tableCode,
        venue_slug: venueSlug,
      });
      api.setToken(res.token);
      set({
        isJoined: true,
        token: res.token,
        sessionId: res.session_id,
        venueSlug,
        venueName: res.venue_name,
        tableNumber: res.table_number,
        spendCap: res.spend_cap,
        spendRemaining: res.spend_cap,
        isLoading: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to join",
        isLoading: false,
      });
    }
  },

  leave: () => {
    api.setToken(null);
    set({
      isJoined: false,
      token: null,
      sessionId: null,
      venueId: null,
      venueSlug: null,
      venueName: null,
      tableNumber: null,
      queue: [],
      mySongs: [],
      isBillingOpen: false,
      billingSummary: null,
    });
  },

  setQueue: (queue: QueueEntry[]) => {
    const { sessionId } = get();
    const mySongs = sessionId
      ? queue.filter((q) => q.session_id === sessionId)
      : [];
    set({ queue, mySongs });
  },

  updateQueueEntry: (entry: QueueEntry) => {
    const { queue } = get();
    const idx = queue.findIndex((q) => q.id === entry.id);
    const newQueue = [...queue];
    if (idx >= 0) {
      newQueue[idx] = entry;
    } else {
      newQueue.push(entry);
    }
    newQueue.sort((a, b) => a.position - b.position);
    const { sessionId } = get();
    const mySongs = sessionId
      ? newQueue.filter((q) => q.session_id === sessionId)
      : [];
    set({ queue: newQueue, mySongs });
  },

  removeQueueEntry: (id: string) => {
    const { queue, sessionId } = get();
    const newQueue = queue.filter((q) => q.id !== id);
    const mySongs = sessionId
      ? newQueue.filter((q) => q.session_id === sessionId)
      : [];
    set({ queue: newQueue, mySongs });
  },

  requestSong: async (songId: string) => {
    const { venueId } = get();
    if (!venueId) return;
    set({ isLoading: true, error: null });
    try {
      const entry = await api.requestSong(venueId, songId);
      get().updateQueueEntry(entry);
      set({ isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to request song",
        isLoading: false,
      });
    }
  },

  boostSong: async (queueId: string, songId: string, amount: 15 | 25 | 35) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.createBoost({
        queue_id: queueId,
        song_id: songId,
        amount,
      });
      set({
        spendRemaining: res.spend_remaining,
        isLoading: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to boost",
        isLoading: false,
      });
    }
  },

  openBilling: () => set({ isBillingOpen: true }),

  setBillingSummary: (summary: BillingSummary) =>
    set({ billingSummary: summary }),

  setError: (error: string | null) => set({ error }),
}));
