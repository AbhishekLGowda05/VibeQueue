"use client";

import Link from "next/link";
import { Music, Monitor, Tv, Headphones } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-12">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent mb-4">
          VibeQueue
        </h1>
        <p className="text-neutral-400 text-lg max-w-md mx-auto">
          Request songs. Boost the vibe. Own the night.
        </p>
      </div>

      <div className="grid gap-4 w-full max-w-sm">
        <Link
          href="/join/demo-venue"
          className="flex items-center gap-4 p-5 rounded-2xl bg-neutral-900 border border-neutral-800 hover:border-violet-500/50 hover:bg-neutral-800/80 transition-all group"
        >
          <div className="p-3 rounded-xl bg-violet-500/10 text-violet-400 group-hover:bg-violet-500/20 transition-colors">
            <Music size={24} />
          </div>
          <div>
            <div className="font-semibold">Guest Interface</div>
            <div className="text-sm text-neutral-500">Join as a guest &amp; request songs</div>
          </div>
        </Link>

        <Link
          href="/dashboard"
          className="flex items-center gap-4 p-5 rounded-2xl bg-neutral-900 border border-neutral-800 hover:border-violet-500/50 hover:bg-neutral-800/80 transition-all group"
        >
          <div className="p-3 rounded-xl bg-violet-500/10 text-violet-400 group-hover:bg-violet-500/20 transition-colors">
            <Monitor size={24} />
          </div>
          <div>
            <div className="font-semibold">Venue Dashboard</div>
            <div className="text-sm text-neutral-500">Staff control panel</div>
          </div>
        </Link>

        <Link
          href="/playback/demo-venue"
          className="flex items-center gap-4 p-5 rounded-2xl bg-neutral-900 border border-neutral-800 hover:border-violet-500/50 hover:bg-neutral-800/80 transition-all group"
        >
          <div className="p-3 rounded-xl bg-violet-500/10 text-violet-400 group-hover:bg-violet-500/20 transition-colors">
            <Headphones size={24} />
          </div>
          <div>
            <div className="font-semibold">Playback Player</div>
            <div className="text-sm text-neutral-500">YouTube music player (Tab 2)</div>
          </div>
        </Link>

        <Link
          href="/display/demo-venue"
          className="flex items-center gap-4 p-5 rounded-2xl bg-neutral-900 border border-neutral-800 hover:border-violet-500/50 hover:bg-neutral-800/80 transition-all group"
        >
          <div className="p-3 rounded-xl bg-violet-500/10 text-violet-400 group-hover:bg-violet-500/20 transition-colors">
            <Tv size={24} />
          </div>
          <div>
            <div className="font-semibold">Ambient Display</div>
            <div className="text-sm text-neutral-500">TV scoreboard for the venue</div>
          </div>
        </Link>
      </div>

      <p className="text-neutral-600 text-xs mt-12">VibeQueue Pilot &middot; Bengaluru 2026</p>
    </div>
  );
}
