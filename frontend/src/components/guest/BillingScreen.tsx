"use client";

import { useState, useEffect } from "react";
import { Check, X, Trash2 } from "lucide-react";
import { useGuestStore } from "@/stores/guest-store";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import type { BillingSummary } from "@/types";

export default function BillingScreen() {
  const { sessionId, tableNumber, venueName } = useGuestStore();
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;
    api
      .getBillingSummary(sessionId)
      .then(setSummary)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [sessionId]);

  const handleRemoveBoost = async (boostId: string) => {
    if (!summary) return;
    try {
      await api.cancelBoost(boostId);
      const updated = {
        ...summary,
        items: summary.items.filter((i) => i.boost_id !== boostId),
      };
      // Recalculate totals
      const confirmedTotal = updated.items
        .filter((i) => i.status === "confirmed")
        .reduce((sum, i) => sum + i.amount, 0);
      const pendingTotal = updated.items
        .filter((i) => i.status === "pending")
        .reduce((sum, i) => sum + i.amount, 0);
      const gst = confirmedTotal * 0.18;
      updated.confirmed_total = confirmedTotal;
      updated.pending_total = pendingTotal;
      updated.gst_amount = gst;
      updated.grand_total = confirmedTotal + gst;
      setSummary(updated);
    } catch {
      // silent
    }
  };

  const handleConfirm = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      await api.confirmBilling(sessionId);
      setConfirmed(true);
    } catch {
      // silent
    } finally {
      setIsLoading(false);
    }
  };

  if (confirmed && summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6">
        <div className="p-4 rounded-full bg-green-500/10 mb-4">
          <Check size={40} className="text-green-400" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Music tab added to your bill</h2>
        <p className="text-lg text-violet-400 font-semibold">
          {formatINR(summary.grand_total)}
        </p>
        <p className="text-neutral-500 text-sm mt-4">
          Pay this along with your food &amp; drinks bill
        </p>
      </div>
    );
  }

  if (isLoading || !summary) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-neutral-500">Loading your tab...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen px-4 py-6">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold">Tonight&apos;s Music Tab</h2>
        <p className="text-sm text-neutral-500">
          Table {tableNumber} &middot; {venueName}
        </p>
      </div>

      {/* Items */}
      <div className="flex-1 space-y-2 mb-6">
        {summary.items.map((item) => (
          <div
            key={item.boost_id}
            className="flex items-center gap-3 p-4 rounded-xl bg-neutral-900 border border-neutral-800"
          >
            {item.played ? (
              <Check size={16} className="text-green-400 shrink-0" />
            ) : (
              <X size={16} className="text-amber-400 shrink-0" />
            )}

            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{item.song_title}</div>
              <div className="text-xs text-neutral-500">
                {item.played ? "PLAYED" : "PENDING — not yet played"}
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span className="text-sm font-semibold">
                {formatINR(item.amount)}
              </span>
              {!item.played && (
                <button
                  onClick={() => handleRemoveBoost(item.boost_id)}
                  className="p-1.5 rounded-lg hover:bg-red-500/10 text-red-400"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="border-t border-neutral-800 pt-4 space-y-2 mb-6">
        <div className="flex justify-between text-sm">
          <span className="text-neutral-400">Confirmed total</span>
          <span>{formatINR(summary.confirmed_total)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-neutral-400">GST (18%)</span>
          <span>{formatINR(summary.gst_amount)}</span>
        </div>
        <div className="flex justify-between font-bold text-lg pt-2 border-t border-neutral-800">
          <span>Music Total</span>
          <span className="text-violet-400">{formatINR(summary.grand_total)}</span>
        </div>
      </div>

      <p className="text-xs text-neutral-600 text-center mb-4">
        This will be added to your food &amp; drinks bill
      </p>

      <button
        onClick={handleConfirm}
        disabled={isLoading}
        className="w-full py-4 rounded-xl bg-violet-600 hover:bg-violet-500 font-semibold text-lg transition-colors disabled:opacity-50"
      >
        {isLoading ? "Processing..." : `Confirm ${formatINR(summary.grand_total)}`}
      </button>
    </div>
  );
}
