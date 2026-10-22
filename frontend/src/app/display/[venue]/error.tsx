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
    console.error("Ambient display error:", error);
  }, [error]);

  // Auto-retry after 10 seconds — the TV has no operator
  useEffect(() => {
    const timer = setTimeout(retry, 10_000);
    return () => clearTimeout(timer);
  }, [retry]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-neutral-950 text-white p-6">
      <h2 className="text-2xl font-bold mb-4">Display temporarily unavailable</h2>
      <p className="text-neutral-500 text-lg">Reconnecting automatically...</p>
    </div>
  );
}
