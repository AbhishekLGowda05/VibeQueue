"use client";

import { useEffect } from "react";
import {
  SkipForward,
  Pause,
  Play,
  AlertTriangle,
  X,
} from "lucide-react";
import { useDashboardStore } from "@/stores/dashboard-store";
import { subscribeToQueue, subscribeToPlaybackEvents } from "@/lib/supabase";
import type { QueueEntry, Alert } from "@/types";
import ActiveTables from "./ActiveTables";
import OpenTableDialog from "./OpenTableDialog";
import { formatINR } from "@/lib/utils";

export default function DashboardView() {
  const {
    venueId,
    venue,
    queue,
    playback,
    alerts,
    tonight,
    mode,
    setQueue,
    setPlayback,
    addAlert,
    dismissAlert,
    skipSong,
    pauseAll,
    resumeAll,
    toggleMode,
    confirmManual,
    loadDashboard,
    error,
    setError,
  } = useDashboardStore();

  const nowPlaying = playback?.current_song;
  const isPaused = playback?.is_paused || false;
  const nextUp = queue
    .filter((q) => q.status === "active")
    .sort((a, b) => a.position - b.position)
    .slice(0, 5);
  const waitingCount = queue.filter((q) => q.status === "waiting").length;
  const activeAlerts = alerts.filter((a) => !a.dismissed);

  // Load initial dashboard state
  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Subscribe to real-time updates
  useEffect(() => {
    if (!venueId) return;

    const queueChannel = subscribeToQueue(venueId, (payload) => {
      // Re-fetch the full queue on any change
      loadDashboard();
    });

    const playbackChannel = subscribeToPlaybackEvents(venueId, () => {
      loadDashboard();
    });

    return () => {
      queueChannel.unsubscribe();
      playbackChannel.unsubscribe();
    };
  }, [venueId, loadDashboard]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Alert Banner */}
      {activeAlerts.length > 0 && (
        <div className="bg-red-500/10 border-b border-red-500/20">
          {activeAlerts.map((alert) => (
            <div
              key={alert.id}
              className="flex items-center justify-between px-6 py-3"
            >
              <div className="flex items-center gap-3">
                <AlertTriangle size={18} className="text-red-400" />
                <span className="text-sm text-red-400">{alert.message}</span>
              </div>
              <button
                onClick={() => dismissAlert(alert.id)}
                className="p-1 rounded hover:bg-red-500/10"
              >
                <X size={16} className="text-red-400" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Top Bar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-neutral-800">
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
            VibeQueue
          </h1>
          <p className="text-xs text-neutral-500">{venue?.name || "Dashboard"}</p>
        </div>

        {/* Mode Toggle */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-neutral-500">MODE:</span>
          <button
            onClick={toggleMode}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              mode === "A"
                ? "bg-green-500/10 text-green-400 border border-green-500/20"
                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
            }`}
          >
            {mode === "A" ? "A: AUTOMATED" : "B: MANUAL"}
          </button>
        </div>
      </header>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-between">
          <span className="text-red-400 text-sm">{error}</span>
          <button onClick={() => setError(null)}>
            <X size={16} className="text-red-400" />
          </button>
        </div>
      )}

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-0 lg:gap-0">
        {/* Left Column: Now Playing + Queue */}
        <div className="lg:col-span-2 border-r border-neutral-800">
          {/* Zone A: Now Playing */}
          <div className="p-6 border-b border-neutral-800">
            <div className="text-xs text-neutral-500 uppercase tracking-wider mb-3 font-semibold">
              Now Playing
            </div>

            {nowPlaying ? (
              <div className="p-5 rounded-2xl bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 now-playing-glow">
                <div className="text-2xl font-bold mb-1">
                  {nowPlaying.song_title}
                </div>
                <div className="text-neutral-400">
                  {nowPlaying.song_artist}
                </div>
                <div className="text-sm text-neutral-500 mt-2">
                  Requested by Table {nowPlaying.table_number}
                </div>

                <div className="flex gap-3 mt-4">
                  <button
                    onClick={() => skipSong(nowPlaying.id)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-sm font-medium transition-colors"
                  >
                    <SkipForward size={16} /> Skip
                  </button>
                  <button
                    onClick={isPaused ? resumeAll : pauseAll}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isPaused
                        ? "bg-green-500/10 text-green-400 hover:bg-green-500/20"
                        : "bg-red-500/10 text-red-400 hover:bg-red-500/20"
                    }`}
                  >
                    {isPaused ? (
                      <>
                        <Play size={16} /> Resume
                      </>
                    ) : (
                      <>
                        <Pause size={16} /> Pause All
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-2xl bg-neutral-900 border border-neutral-800 text-center text-neutral-500">
                {isPaused ? "Queue Paused" : "No song playing"}
              </div>
            )}

            {/* Mode B: Manual confirmation */}
            {mode === "B" && nextUp.length > 0 && !nowPlaying && (
              <div className="mt-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <div className="text-sm font-semibold text-amber-400 mb-2">
                  Next Song Ready
                </div>
                <div className="text-lg font-bold">
                  {nextUp[0].song_title} &middot; {nextUp[0].song_artist}
                </div>
                <div className="text-xs text-neutral-500 mb-3">
                  Table {nextUp[0].table_number} &middot; Boost score{" "}
                  {Math.round(nextUp[0].boost_score)}
                </div>
                <button
                  onClick={confirmManual}
                  className="px-4 py-2 rounded-lg bg-amber-500 text-black font-semibold text-sm hover:bg-amber-400 transition-colors"
                >
                  Mark as Played &mdash; Start This Song
                </button>
              </div>
            )}
          </div>

          {/* Zone B: Queue Preview */}
          <div className="p-6">
            <div className="text-xs text-neutral-500 uppercase tracking-wider mb-3 font-semibold">
              Next Up
            </div>

            {nextUp.length === 0 ? (
              <div className="text-center py-8 text-neutral-600 text-sm">
                Queue is empty
              </div>
            ) : (
              <div className="space-y-2">
                {nextUp.map((entry) => (
                  <div
                    key={entry.id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-neutral-900 border border-neutral-800/50"
                  >
                    <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-neutral-800 text-sm font-bold text-neutral-400">
                      #{entry.position}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {entry.song_title} &middot;{" "}
                        <span className="text-neutral-500">
                          {entry.song_artist}
                        </span>
                      </div>
                    </div>
                    <div className="text-sm text-neutral-500">
                      Table {entry.table_number}
                    </div>
                    {entry.boost_score > 0 && (
                      <div className="text-xs font-semibold text-violet-400 bg-violet-500/10 px-2 py-1 rounded">
                        {Math.round(entry.boost_score)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {waitingCount > 0 && (
              <p className="text-xs text-neutral-600 mt-3">
                {waitingCount} more songs in waiting pool
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Tables + Stats */}
        <div className="flex flex-col">
          <ActiveTables />

          {/* Zone D: Tonight's Numbers */}
          <div className="p-6 border-t border-neutral-800 mt-auto">
            <div className="text-xs text-neutral-500 uppercase tracking-wider mb-3 font-semibold">
              Tonight
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Tables served" value={tonight.tables_served.toString()} />
              <Stat
                label="Music revenue"
                value={formatINR(tonight.music_revenue)}
              />
              <Stat label="Songs played" value={tonight.songs_played.toString()} />
              <Stat
                label="Boost conversion"
                value={`${tonight.boost_conversion}%`}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800/50">
      <div className="text-xs text-neutral-500">{label}</div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  );
}
