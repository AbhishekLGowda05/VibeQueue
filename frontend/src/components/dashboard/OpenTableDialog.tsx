"use client";

import { useState } from "react";
import { X, Copy, Check } from "lucide-react";
import { useDashboardStore } from "@/stores/dashboard-store";

export default function OpenTableDialog({ onClose }: { onClose: () => void }) {
  const { openTable } = useDashboardStore();
  const [tableNumber, setTableNumber] = useState("");
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleOpen = async () => {
    const num = parseInt(tableNumber);
    if (isNaN(num) || num < 1) return;
    setIsLoading(true);
    setError(null);
    try {
      const session = await openTable(num);
      setGeneratedCode(session.table_code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open table");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (generatedCode) {
      navigator.clipboard.writeText(generatedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-neutral-900 rounded-2xl border border-neutral-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">Open New Table</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-neutral-800">
            <X size={20} className="text-neutral-500" />
          </button>
        </div>

        {!generatedCode ? (
          <>
            <input
              type="number"
              min="1"
              value={tableNumber}
              onChange={(e) => setTableNumber(e.target.value)}
              placeholder="Table number"
              className="w-full p-3 rounded-xl bg-neutral-800 border border-neutral-700 focus:border-violet-500 focus:outline-none text-sm mb-4"
              autoFocus
            />

            {error && (
              <div className="text-red-400 text-sm mb-4">{error}</div>
            )}

            <button
              onClick={handleOpen}
              disabled={!tableNumber || isLoading}
              className="w-full py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-neutral-800 disabled:text-neutral-600 font-semibold transition-colors"
            >
              {isLoading ? "Opening..." : "Generate Code"}
            </button>
          </>
        ) : (
          <div className="text-center">
            <p className="text-sm text-neutral-400 mb-3">
              Table {tableNumber} code:
            </p>
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="text-4xl font-mono font-bold tracking-[0.3em] text-violet-400">
                {generatedCode}
              </div>
              <button
                onClick={handleCopy}
                className="p-2 rounded-lg hover:bg-neutral-800 transition-colors"
              >
                {copied ? (
                  <Check size={20} className="text-green-400" />
                ) : (
                  <Copy size={20} className="text-neutral-500" />
                )}
              </button>
            </div>
            <p className="text-xs text-neutral-500 mb-4">
              Tell this code to the guests at Table {tableNumber}
            </p>
            <button
              onClick={onClose}
              className="w-full py-3 rounded-xl bg-neutral-800 hover:bg-neutral-700 font-semibold transition-colors"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
