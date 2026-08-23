"use client";

import { ChevronDown, ChevronUp, Check, Clock } from "lucide-react";
import { useState } from "react";
import type { QueueEntry } from "@/types";

export default function MySongs({ songs }: { songs: QueueEntry[] }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-t border-neutral-800 bg-neutral-900/50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-neutral-400 uppercase tracking-wider"
      >
        <span>My Songs ({songs.length})</span>
        {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-2">
          {songs.map((song) => (
            <div
              key={song.id}
              className="flex items-center gap-3 p-3 rounded-lg bg-neutral-800/50"
            >
              <StatusIcon status={song.status} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{song.song_title}</div>
                <div className="text-xs text-neutral-500">{song.song_artist}</div>
              </div>
              <StatusLabel status={song.status} position={song.position} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusIcon({ status }: { status: QueueEntry["status"] }) {
  if (status === "played") return <Check size={16} className="text-green-400 shrink-0" />;
  if (status === "waiting") return <Clock size={16} className="text-amber-400 shrink-0" />;
  return <div className="w-4 h-4 rounded-full bg-violet-500/30 border border-violet-500 shrink-0" />;
}

function StatusLabel({ status, position }: { status: QueueEntry["status"]; position: number }) {
  if (status === "played") {
    return <span className="text-xs text-green-400 font-medium">PLAYED</span>;
  }
  if (status === "waiting") {
    return <span className="text-xs text-amber-400">Waiting</span>;
  }
  if (status === "playing") {
    return <span className="text-xs text-violet-400 font-medium">NOW PLAYING</span>;
  }
  return <span className="text-xs text-neutral-500">Queue #{position}</span>;
}
