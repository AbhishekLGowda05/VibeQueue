"use client";

import { ChevronUp } from "lucide-react";
import type { QueueEntry } from "@/types";
import { timeAgo } from "@/lib/utils";

interface QueueCardProps {
  entry: QueueEntry;
  isOwnTable: boolean;
  onBoost: () => void;
}

export default function QueueCard({ entry, isOwnTable, onBoost }: QueueCardProps) {
  const canBoost = entry.status === "active";

  return (
    <div
      className={`queue-card flex items-center gap-3 p-3 rounded-xl ${
        isOwnTable
          ? "bg-violet-500/10 border border-violet-500/20"
          : "bg-neutral-900 border border-neutral-800/50"
      }`}
    >
      {/* Position */}
      <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-neutral-800 text-sm font-bold text-neutral-400 shrink-0">
        {entry.position}
      </div>

      {/* Song Info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{entry.song_title}</div>
        <div className="text-xs text-neutral-500 flex items-center gap-2">
          <span>{entry.song_artist}</span>
          <span>&middot;</span>
          <span>Table {entry.table_number}</span>
        </div>
      </div>

      {/* Score + Boost */}
      <div className="flex items-center gap-2 shrink-0">
        {entry.boost_score > 0 && (
          <div className="text-xs font-semibold text-violet-400 bg-violet-500/10 px-2 py-1 rounded-md">
            <ChevronUp size={12} className="inline -mt-0.5" />
            {Math.round(entry.boost_score)}
          </div>
        )}

        {canBoost && (
          <button
            onClick={onBoost}
            className="px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-xs font-semibold transition-colors active:scale-95"
          >
            Boost
          </button>
        )}
      </div>
    </div>
  );
}
