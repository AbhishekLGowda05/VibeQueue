"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, ChevronUp, X } from "lucide-react";
import { useGuestStore } from "@/stores/guest-store";
import { api } from "@/lib/api";
import { subscribeToQueue, subscribeToSession } from "@/lib/supabase";
import type { QueueEntry, SongSearchResult } from "@/types";
import NowPlaying from "./NowPlaying";
import QueueCard from "./QueueCard";
import BoostSheet from "./BoostSheet";
import BillingScreen from "./BillingScreen";
import MySongs from "./MySongs";

export default function QueueView() {
  const {
    venueSlug,
    venueName,
    tableNumber,
    sessionId,
    spendCap,
    spendRemaining,
    queue,
    mySongs,
    setQueue,
    updateQueueEntry,
    isBillingOpen,
    openBilling,
    error,
    setError,
  } = useGuestStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SongSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedSong, setSelectedSong] = useState<QueueEntry | null>(null);
  const [showSearch, setShowSearch] = useState(false);

  const nowPlaying = queue.find((q) => q.status === "playing");
  const activeQueue = queue
    .filter((q) => q.status === "active")
    .sort((a, b) => a.position - b.position)
    .slice(0, 8);

  // Subscribe to real-time queue updates
  useEffect(() => {
    if (!venueSlug) return;

    const channel = subscribeToQueue(venueSlug, (payload) => {
      const data = (payload as { new?: QueueEntry }).new;
      if (data) {
        updateQueueEntry(data);
      }
    });

    return () => {
      channel.unsubscribe();
    };
  }, [venueSlug, updateQueueEntry]);

  // Subscribe to session changes (billing trigger)
  useEffect(() => {
    if (!sessionId) return;

    const channel = subscribeToSession(sessionId, (payload) => {
      const data = (payload as { new?: { status: string } }).new;
      if (data?.status === "billing") {
        openBilling();
      }
    });

    return () => {
      channel.unsubscribe();
    };
  }, [sessionId, openBilling]);

  // Load initial queue
  useEffect(() => {
    if (!venueSlug) return;
    api.getQueue(venueSlug).then(setQueue).catch(() => {});
  }, [venueSlug, setQueue]);

  // Search songs
  const handleSearch = useCallback(
    async (query: string) => {
      setSearchQuery(query);
      if (query.length < 2 || !venueSlug) {
        setSearchResults([]);
        return;
      }
      setIsSearching(true);
      try {
        const results = await api.searchSongs(venueSlug, query);
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    },
    [venueSlug]
  );

  // Request a song
  const handleRequestSong = async (song: SongSearchResult) => {
    if (!venueSlug) return;
    try {
      const entry = await api.requestSong(venueSlug, song.id);
      updateQueueEntry(entry);
      setSearchQuery("");
      setSearchResults([]);
      setShowSearch(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to request song");
    }
  };

  if (isBillingOpen) {
    return <BillingScreen />;
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-neutral-950/90 backdrop-blur-lg border-b border-neutral-800/50 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
              VibeQueue
            </h1>
            <p className="text-xs text-neutral-500">{venueName} &middot; Table {tableNumber}</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-neutral-500">Spend limit</div>
            <div className="text-sm font-medium">
              <span className="text-violet-400">₹{spendRemaining}</span>
              <span className="text-neutral-600"> / ₹{spendCap}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Error toast */}
      {error && (
        <div className="mx-4 mt-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-between">
          <span className="text-red-400 text-sm">{error}</span>
          <button onClick={() => setError(null)}>
            <X size={16} className="text-red-400" />
          </button>
        </div>
      )}

      {/* Now Playing */}
      {nowPlaying && <NowPlaying song={nowPlaying} />}

      {/* Live Queue */}
      <div className="flex-1 px-4 py-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider">
            Live Queue
          </h2>
          <span className="text-xs text-neutral-600">{activeQueue.length} songs</span>
        </div>

        {activeQueue.length === 0 ? (
          <div className="text-center py-12 text-neutral-600">
            <p className="text-lg mb-1">Queue is empty</p>
            <p className="text-sm">Be the first to request a song!</p>
          </div>
        ) : (
          <div className="space-y-2">
            {activeQueue.map((entry) => (
              <QueueCard
                key={entry.id}
                entry={entry}
                isOwnTable={entry.session_id === sessionId}
                onBoost={() => setSelectedSong(entry)}
              />
            ))}
          </div>
        )}
      </div>

      {/* My Songs */}
      {mySongs.length > 0 && <MySongs songs={mySongs} />}

      {/* Search FAB */}
      <button
        onClick={() => setShowSearch(true)}
        className="fixed bottom-6 right-6 p-4 rounded-full bg-violet-600 hover:bg-violet-500 shadow-lg shadow-violet-500/25 transition-all active:scale-95 z-20"
      >
        <Search size={24} />
      </button>

      {/* Search Overlay */}
      {showSearch && (
        <div className="fixed inset-0 z-30 bg-neutral-950/95 backdrop-blur-lg flex flex-col">
          <div className="p-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-1 relative">
                <Search
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500"
                />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="Search songs..."
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-neutral-900 border border-neutral-800 focus:border-violet-500 focus:outline-none text-sm"
                  autoFocus
                />
              </div>
              <button
                onClick={() => {
                  setShowSearch(false);
                  setSearchQuery("");
                  setSearchResults([]);
                }}
                className="p-3 rounded-xl bg-neutral-900 text-neutral-400"
              >
                <X size={18} />
              </button>
            </div>

            {isSearching && (
              <div className="text-center py-8 text-neutral-500 text-sm">
                Searching...
              </div>
            )}

            <div className="space-y-1">
              {searchResults.map((song) => (
                <button
                  key={song.id}
                  onClick={() => handleRequestSong(song)}
                  className="w-full text-left p-4 rounded-xl hover:bg-neutral-900 transition-colors"
                >
                  <div className="font-medium">{song.title}</div>
                  <div className="text-sm text-neutral-500">{song.artist}</div>
                </button>
              ))}
            </div>

            {searchQuery.length >= 2 &&
              !isSearching &&
              searchResults.length === 0 && (
                <div className="text-center py-8 text-neutral-500 text-sm">
                  No songs found in this venue&apos;s catalogue
                </div>
              )}
          </div>
        </div>
      )}

      {/* Boost Sheet */}
      {selectedSong && (
        <BoostSheet
          entry={selectedSong}
          onClose={() => setSelectedSong(null)}
        />
      )}
    </div>
  );
}
