"use client";

import { X, ChevronUp } from "lucide-react";
import { useGuestStore } from "@/stores/guest-store";
import type { QueueEntry, BoostTier } from "@/types";
import { estimatePosition, formatINR } from "@/lib/utils";

const BOOST_TIERS: { amount: BoostTier; label: string; score: number }[] = [
  { amount: 15, label: "Small Boost", score: 15 },
  { amount: 25, label: "Medium Boost", score: 25 },
  { amount: 35, label: "Priority Boost", score: 35 },
];

interface BoostSheetProps {
  entry: QueueEntry;
  onClose: () => void;
}

export default function BoostSheet({ entry, onClose }: BoostSheetProps) {
  const { boostSong, queue, spendRemaining, isLoading } = useGuestStore();

  const handleBoost = async (amount: BoostTier) => {
    if (amount > spendRemaining) return;
    await boostSong(entry.id, entry.song_id, amount);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sheet */}
      <div className="relative w-full max-w-lg bg-neutral-900 rounded-t-3xl border-t border-neutral-800 p-6 pb-10 animate-slide-up">
        {/* Handle */}
        <div className="w-10 h-1 bg-neutral-700 rounded-full mx-auto mb-4" />

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold">Boost {entry.song_title}</h3>
            <p className="text-sm text-neutral-500">{entry.song_artist}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-neutral-800 text-neutral-500"
          >
            <X size={20} />
          </button>
        </div>

        {/* Boost Options */}
        <div className="space-y-3 mb-6">
          {BOOST_TIERS.map((tier) => {
            const estimatedPos = estimatePosition(
              queue.filter((q) => q.status === "active"),
              tier.score,
              entry.boost_score
            );
            const canAfford = tier.amount <= spendRemaining;

            return (
              <button
                key={tier.amount}
                onClick={() => handleBoost(tier.amount)}
                disabled={!canAfford || isLoading}
                className={`w-full flex items-center justify-between p-4 rounded-xl border transition-all active:scale-[0.98] ${
                  canAfford
                    ? "bg-neutral-800 border-neutral-700 hover:border-violet-500/50"
                    : "bg-neutral-800/50 border-neutral-800 opacity-50 cursor-not-allowed"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-violet-500/10">
                    <ChevronUp size={18} className="text-violet-400" />
                  </div>
                  <div className="text-left">
                    <div className="font-semibold">{tier.label}</div>
                    <div className="text-xs text-neutral-500">
                      +{tier.score} score &middot; moves to ~#{estimatedPos}
                    </div>
                  </div>
                </div>
                <div className="font-bold text-violet-400">
                  {formatINR(tier.amount)}
                </div>
              </button>
            );
          })}
        </div>

        {/* Footer Info */}
        <div className="text-center text-xs text-neutral-500">
          <p>Current position: #{entry.position}</p>
          <p className="mt-1">
            ₹{spendRemaining} remaining tonight &middot; You only pay if the song plays
          </p>
        </div>
      </div>
    </div>
  );
}
