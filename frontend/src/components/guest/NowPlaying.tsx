"use client";

import { Music } from "lucide-react";
import type { QueueEntry } from "@/types";

export default function NowPlaying({ song }: { song: QueueEntry }) {
  return (
    <div className="mx-4 mt-4 p-4 rounded-2xl bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 now-playing-glow">
      <div className="flex items-center gap-1 text-xs text-violet-400 font-semibold uppercase tracking-wider mb-2">
        <Music size={12} />
        Now Playing
      </div>
      <div className="text-lg font-bold">{song.song_title}</div>
      <div className="text-sm text-neutral-400">{song.song_artist}</div>
      <div className="text-xs text-neutral-500 mt-1">
        Requested by Table {song.table_number}
      </div>
    </div>
  );
}
