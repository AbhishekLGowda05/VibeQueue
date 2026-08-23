// VibeQueue — Supabase client for real-time WebSocket subscriptions

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://localhost:54321";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "your-anon-key";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Subscribe to real-time queue changes for a venue
export function subscribeToQueue(
  venueId: string,
  onUpdate: (payload: Record<string, unknown>) => void
) {
  return supabase
    .channel(`queue:${venueId}`)
    .on(
      "postgres_changes",
      {
        event: "*",
        schema: "public",
        table: "queue",
        filter: `venue_id=eq.${venueId}`,
      },
      (payload) => onUpdate(payload as unknown as Record<string, unknown>)
    )
    .subscribe();
}

// Subscribe to playback commands for a venue (used by Playback Page)
export function subscribeToPlaybackCommands(
  venueId: string,
  onCommand: (payload: Record<string, unknown>) => void
) {
  return supabase
    .channel(`playback_commands:${venueId}`)
    .on(
      "postgres_changes",
      {
        event: "INSERT",
        schema: "public",
        table: "playback_commands",
        filter: `venue_id=eq.${venueId}`,
      },
      (payload) => onCommand(payload as unknown as Record<string, unknown>)
    )
    .subscribe();
}

// Subscribe to playback events (used by Dashboard)
export function subscribeToPlaybackEvents(
  venueId: string,
  onEvent: (payload: Record<string, unknown>) => void
) {
  return supabase
    .channel(`playback_events:${venueId}`)
    .on(
      "postgres_changes",
      {
        event: "INSERT",
        schema: "public",
        table: "playback_events",
        filter: `venue_id=eq.${venueId}`,
      },
      (payload) => onEvent(payload as unknown as Record<string, unknown>)
    )
    .subscribe();
}

// Subscribe to alerts (used by Dashboard)
export function subscribeToAlerts(
  venueId: string,
  onAlert: (payload: Record<string, unknown>) => void
) {
  return supabase
    .channel(`alerts:${venueId}`)
    .on(
      "postgres_changes",
      {
        event: "INSERT",
        schema: "public",
        table: "alerts",
        filter: `venue_id=eq.${venueId}`,
      },
      (payload) => onAlert(payload as unknown as Record<string, unknown>)
    )
    .subscribe();
}

// Subscribe to session state changes (billing trigger for guest)
export function subscribeToSession(
  sessionId: string,
  onUpdate: (payload: Record<string, unknown>) => void
) {
  return supabase
    .channel(`session:${sessionId}`)
    .on(
      "postgres_changes",
      {
        event: "UPDATE",
        schema: "public",
        table: "sessions",
        filter: `id=eq.${sessionId}`,
      },
      (payload) => onUpdate(payload as unknown as Record<string, unknown>)
    )
    .subscribe();
}
