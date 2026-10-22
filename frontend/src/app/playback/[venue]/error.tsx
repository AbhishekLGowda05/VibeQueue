"use client";

import { useEffect } from "react";

export default function ErrorPage({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error("Playback error:", error);
  }, [error]);

  // Auto-retry after 5 seconds — playback tab should self-recover
  useEffect(() => {
    const timer = setTimeout(retry, 5_000);
    return () => clearTimeout(timer);
  }, [retry]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-neutral-950 text-white p-6">
      <h2 className="text-xl font-bold mb-4">Playback interrupted</h2>
      <p className="text-neutral-500 mb-6 text-sm">Reconnecting automatically...</p>
      <button
        onClick={() => retry()}
        className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 font-semibold transition-colors"
      >
        Retry now
      </button>
    </div>
  );
}
