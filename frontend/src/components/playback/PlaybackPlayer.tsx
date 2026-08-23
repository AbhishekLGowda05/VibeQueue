"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Wifi, WifiOff, Music } from "lucide-react";
import { api } from "@/lib/api";
import { subscribeToPlaybackCommands } from "@/lib/supabase";
import type { PlaybackCommand, PlaybackEvent } from "@/types";

// YouTube IFrame Player API types
declare global {
  interface Window {
    YT: {
      Player: new (
        elementId: string,
        config: {
          width: number;
          height: number;
          playerVars: Record<string, number | string>;
          events: Record<string, (event: YTEvent) => void>;
        }
      ) => YTPlayer;
      PlayerState: {
        ENDED: number;
        PLAYING: number;
        PAUSED: number;
        BUFFERING: number;
        CUED: number;
      };
    };
    onYouTubeIframeAPIReady: () => void;
  }
}

interface YTPlayer {
  loadVideoById: (config: { videoId: string; startSeconds: number }) => void;
  playVideo: () => void;
  pauseVideo: () => void;
  stopVideo: () => void;
  destroy: () => void;
}

interface YTEvent {
  data: number;
  target: YTPlayer;
}

export default function PlaybackPlayer({ venueSlug }: { venueSlug: string }) {
  const playerRef = useRef<YTPlayer | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [currentSong, setCurrentSong] = useState<{
    title: string;
    artist: string;
    table: number;
  } | null>(null);
  const [status, setStatus] = useState<string>("Initializing...");
  const keepAliveRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Report playback events to backend
  const reportEvent = useCallback(
    async (
      eventType: PlaybackEvent["event_type"],
      videoId: string,
      queueId: string,
      errorCode?: number
    ) => {
      try {
        await api.reportPlaybackEvent({
          venue_id: venueSlug,
          queue_id: queueId,
          youtube_video_id: videoId,
          event_type: eventType,
          error_code: errorCode,
          occurred_at: new Date().toISOString(),
        });
      } catch {
        // Non-critical, log silently
      }
    },
    [venueSlug]
  );

  // Initialize YouTube IFrame Player
  useEffect(() => {
    // Load the IFrame API script
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);

    let currentVideoId = "";
    let currentQueueId = "";

    window.onYouTubeIframeAPIReady = () => {
      playerRef.current = new window.YT.Player("yt-player", {
        width: 320,
        height: 180,
        playerVars: {
          autoplay: 1,
          controls: 0,
          modestbranding: 1,
          rel: 0,
          showinfo: 0,
          iv_load_policy: 3,
          disablekb: 1,
        },
        events: {
          onReady: () => {
            setIsReady(true);
            setStatus("Ready — waiting for songs");
          },
          onStateChange: (event: YTEvent) => {
            if (event.data === 0) {
              // ENDED
              setStatus("Song ended — advancing queue");
              reportEvent("ENDED", currentVideoId, currentQueueId);
              setCurrentSong(null);
            } else if (event.data === 1) {
              // PLAYING
              setStatus("Playing");
              reportEvent("PLAYING", currentVideoId, currentQueueId);
            } else if (event.data === 2) {
              // PAUSED
              setStatus("Paused");
              reportEvent("PAUSED", currentVideoId, currentQueueId);
            } else if (event.data === 3) {
              // BUFFERING
              setStatus("Buffering...");
            }
          },
          onError: (event: YTEvent) => {
            setStatus(`Error: code ${event.data}`);
            reportEvent("ERROR", currentVideoId, currentQueueId, event.data);
          },
        },
      });
    };

    // Subscribe to playback commands
    const channel = subscribeToPlaybackCommands(venueSlug, (payload) => {
      const command = (payload as { new?: PlaybackCommand }).new;
      if (!command || !playerRef.current) return;

      setIsConnected(true);

      if (command.action === "play" && command.youtube_video_id) {
        currentVideoId = command.youtube_video_id;
        currentQueueId = command.queue_id;
        setCurrentSong({
          title: command.song_title,
          artist: command.song_artist,
          table: command.table_number,
        });
        setStatus("Loading...");
        playerRef.current.loadVideoById({
          videoId: command.youtube_video_id,
          startSeconds: 0,
        });
      } else if (command.action === "pause") {
        playerRef.current.pauseVideo();
      } else if (command.action === "resume") {
        playerRef.current.playVideo();
      } else if (command.action === "skip") {
        playerRef.current.stopVideo();
        setCurrentSong(null);
        setStatus("Skipped — waiting for next song");
      }
    });

    setIsConnected(true);

    return () => {
      channel.unsubscribe();
      playerRef.current?.destroy();
    };
  }, [venueSlug, reportEvent]);

  // Keep-alive: play silent audio to prevent tab sleeping
  useEffect(() => {
    try {
      audioCtxRef.current = new AudioContext();
      const oscillator = audioCtxRef.current.createOscillator();
      const gainNode = audioCtxRef.current.createGain();
      gainNode.gain.value = 0; // Silent
      oscillator.connect(gainNode);
      gainNode.connect(audioCtxRef.current.destination);
      oscillator.start();

      keepAliveRef.current = setInterval(() => {
        // Ping to keep the tab alive
        if (audioCtxRef.current?.state === "suspended") {
          audioCtxRef.current.resume();
        }
      }, 30000);
    } catch {
      // AudioContext not available
    }

    return () => {
      if (keepAliveRef.current) clearInterval(keepAliveRef.current);
      audioCtxRef.current?.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-8">
      {/* Connection Status */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        {isConnected ? (
          <div className="flex items-center gap-1.5 text-green-400 text-xs">
            <Wifi size={14} />
            <span>Connected</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-red-400 text-xs">
            <WifiOff size={14} />
            <span>Disconnected</span>
          </div>
        )}
      </div>

      {/* VibeQueue Logo (minimal) */}
      <div className="mb-8 text-center">
        <div className="text-sm text-neutral-600 font-semibold uppercase tracking-widest">
          VibeQueue Playback
        </div>
      </div>

      {/* YouTube Player */}
      <div className="rounded-xl overflow-hidden bg-black border border-neutral-800 mb-6">
        <div id="yt-player" />
      </div>

      {/* Now Playing Info */}
      {currentSong ? (
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 text-violet-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Music size={12} />
            Now Playing
          </div>
          <div className="text-lg font-bold">{currentSong.title}</div>
          <div className="text-sm text-neutral-500">{currentSong.artist}</div>
          <div className="text-xs text-neutral-600 mt-1">
            Table {currentSong.table}
          </div>
        </div>
      ) : (
        <div className="text-center text-neutral-600 text-sm">{status}</div>
      )}

      {/* Status */}
      <div className="absolute bottom-4 left-4 text-xs text-neutral-700">
        {status}
      </div>
    </div>
  );
}
