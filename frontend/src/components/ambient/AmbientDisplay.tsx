"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Music, ChevronUp, QrCode } from "lucide-react";
import { api } from "@/lib/api";
import { subscribeToQueue, subscribeToPlaybackEvents } from "@/lib/supabase";
import type { QueueEntry, PlaybackStatus } from "@/types";

export default function AmbientDisplay({ venueSlug }: { venueSlug: string }) {
  const [nowPlaying, setNowPlaying] = useState<QueueEntry | null>(null);
  const [nextUp, setNextUp] = useState<QueueEntry[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [songProgress, setSongProgress] = useState(0);
  const [songStartTime, setSongStartTime] = useState<number | null>(null);
  const AVERAGE_SONG_DURATION = 210; // 3.5 minutes in seconds

  const processQueue = useCallback((entries: QueueEntry[]) => {
    const playing = entries.find((q) => q.status === "playing");
    const active = entries
      .filter((q) => q.status === "active")
      .sort((a, b) => a.position - b.position)
      .slice(0, 3);

    setNowPlaying(playing || null);
    setNextUp(active);

    if (playing) {
      setSongStartTime(Date.now());
    }
  }, []);

  // Load initial state
  useEffect(() => {
    api
      .getQueue(venueSlug)
      .then(processQueue)
      .catch(() => {});
    api
      .getPlaybackStatus(venueSlug)
      .then((status: PlaybackStatus) => {
        setIsPaused(status.is_paused);
        if (status.current_song) {
          setNowPlaying(status.current_song);
          setSongStartTime(Date.now());
        }
      })
      .catch(() => {});
  }, [venueSlug, processQueue]);

  // Subscribe to real-time updates
  useEffect(() => {
    const queueChannel = subscribeToQueue(venueSlug, () => {
      // Refetch queue on any change
      api.getQueue(venueSlug).then(processQueue).catch(() => {});
    });

    const playbackChannel = subscribeToPlaybackEvents(venueSlug, () => {
      api.getQueue(venueSlug).then(processQueue).catch(() => {});
      api
        .getPlaybackStatus(venueSlug)
        .then((status: PlaybackStatus) => setIsPaused(status.is_paused))
        .catch(() => {});
    });

    return () => {
      queueChannel.unsubscribe();
      playbackChannel.unsubscribe();
    };
  }, [venueSlug, processQueue]);

  // Song progress animation
  useEffect(() => {
    if (!songStartTime || !nowPlaying) {
      setSongProgress(0);
      return;
    }

    const interval = setInterval(() => {
      const elapsed = (Date.now() - songStartTime) / 1000;
      const progress = Math.min((elapsed / AVERAGE_SONG_DURATION) * 100, 100);
      setSongProgress(progress);
    }, 1000);

    return () => clearInterval(interval);
  }, [songStartTime, nowPlaying]);

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-12 select-none cursor-default overflow-hidden">
      {/* Paused overlay */}
      {isPaused && (
        <div className="absolute inset-0 bg-black/80 flex items-center justify-center z-10">
          <div className="text-center">
            <div className="text-3xl font-bold text-neutral-500 mb-2">
              Queue Paused
            </div>
            <div className="text-neutral-600">back soon</div>
          </div>
        </div>
      )}

      {/* Now Playing */}
      <AnimatePresence mode="wait">
        {nowPlaying ? (
          <motion.div
            key={nowPlaying.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
            className="text-center mb-16 max-w-4xl"
          >
            {/* Label */}
            <div className="flex items-center justify-center gap-2 text-violet-400 text-sm font-bold uppercase tracking-[0.3em] mb-6">
              <Music size={16} />
              Now Playing
            </div>

            {/* Progress Bar */}
            <div className="w-full max-w-2xl mx-auto h-1 bg-neutral-800 rounded-full mb-8 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full transition-all duration-1000 ease-linear"
                style={{ width: `${songProgress}%` }}
              />
            </div>

            {/* Song Title */}
            <h1 className="text-6xl font-bold mb-3 bg-gradient-to-r from-white to-neutral-300 bg-clip-text text-transparent leading-tight">
              {nowPlaying.song_title}
            </h1>

            {/* Artist */}
            <p className="text-2xl text-neutral-400 mb-6">
              {nowPlaying.song_artist}
            </p>

            {/* Divider */}
            <div className="w-24 h-px bg-neutral-800 mx-auto mb-6" />

            {/* Table Attribution */}
            <p className="text-xl text-neutral-500">
              Requested by{" "}
              <span className="text-violet-400 font-semibold">
                TABLE {nowPlaying.table_number}
              </span>
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center mb-16"
          >
            <div className="inline-flex p-6 rounded-3xl bg-violet-500/5 mb-6">
              <Music size={48} className="text-violet-400/50" />
            </div>
            <h1 className="text-4xl font-bold text-neutral-600">VibeQueue</h1>
            <p className="text-neutral-700 mt-2">Waiting for songs...</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Divider */}
      <div className="w-full max-w-2xl h-px bg-neutral-900 mb-12" />

      {/* Next Up */}
      {nextUp.length > 0 && (
        <div className="w-full max-w-2xl">
          <h2 className="text-sm font-bold text-neutral-600 uppercase tracking-[0.2em] mb-6 text-center">
            Next Up
          </h2>

          <AnimatePresence mode="popLayout">
            {nextUp.map((entry) => (
              <motion.div
                key={entry.id}
                layout
                layoutId={`ambient-${entry.id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
                className="flex items-center gap-6 px-6 py-4 rounded-2xl bg-neutral-900/50 border border-neutral-800/30 mb-4"
              >
                <div className="text-2xl font-bold text-neutral-700 w-8 text-center">
                  #{entry.position}
                </div>
                <div className="flex-1">
                  <div className="text-xl font-semibold">{entry.song_title}</div>
                  <div className="text-neutral-500">{entry.song_artist}</div>
                </div>
                <div className="text-right">
                  <div className="text-neutral-500 text-sm">
                    TABLE {entry.table_number}
                  </div>
                  {entry.boost_score > 0 && (
                    <div className="flex items-center gap-1 text-violet-400 text-sm font-semibold">
                      <ChevronUp size={14} />
                      {Math.round(entry.boost_score)}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* CTA */}
      <div className="absolute bottom-8 flex items-center gap-3 text-neutral-600">
        <QrCode size={20} />
        <span className="text-sm font-medium tracking-wide">
          WANT YOUR SONG NEXT? SCAN THE QR ON YOUR TABLE
        </span>
      </div>
    </div>
  );
}
