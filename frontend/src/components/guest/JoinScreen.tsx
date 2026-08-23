"use client";

import { useState } from "react";
import { Music } from "lucide-react";
import { useGuestStore } from "@/stores/guest-store";

export default function JoinScreen({ venueSlug }: { venueSlug: string }) {
  const [code, setCode] = useState("");
  const { join, isLoading, error } = useGuestStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length === 6) {
      join(code, venueSlug);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex p-4 rounded-2xl bg-violet-500/10 mb-4">
            <Music size={40} className="text-violet-400" />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
            VibeQueue
          </h1>
          <p className="text-neutral-500 text-sm mt-2">
            Request songs. Boost the vibe.
          </p>
        </div>

        {/* Join Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-neutral-400 mb-2">
              Enter table code
            </label>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              placeholder="_ _ _ _ _ _"
              className="w-full text-center text-3xl tracking-[0.5em] font-mono p-4 rounded-xl bg-neutral-900 border border-neutral-800 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 transition-colors placeholder:text-neutral-700 placeholder:tracking-[0.3em]"
              autoFocus
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm text-center bg-red-500/10 p-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={code.length !== 6 || isLoading}
            className="w-full py-4 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-neutral-800 disabled:text-neutral-600 font-semibold text-lg transition-colors"
          >
            {isLoading ? "Joining..." : "Join"}
          </button>
        </form>

        <p className="text-neutral-600 text-xs text-center mt-6">
          Ask your waiter for the 6-digit code
        </p>
      </div>
    </div>
  );
}
