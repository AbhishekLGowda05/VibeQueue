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
    console.error("VibeQueue error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-neutral-950 text-white p-6">
      <h2 className="text-xl font-bold mb-4">Something went wrong</h2>
      <p className="text-neutral-500 mb-6 text-sm text-center max-w-sm">
        {error.message || "An unexpected error occurred."}
      </p>
      <button
        onClick={() => retry()}
        className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 font-semibold transition-colors"
      >
        Try again
      </button>
    </div>
  );
}
