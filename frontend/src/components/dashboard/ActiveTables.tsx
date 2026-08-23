"use client";

import { useState } from "react";
import { Plus, X, Flag, CreditCard } from "lucide-react";
import { useDashboardStore } from "@/stores/dashboard-store";
import { formatINR } from "@/lib/utils";
import OpenTableDialog from "./OpenTableDialog";

export default function ActiveTables() {
  const { activeSessions, closeTable, flagTable } = useDashboardStore();
  const [showOpenDialog, setShowOpenDialog] = useState(false);

  const activeTables = activeSessions.filter(
    (s) => s.status === "active" || s.status === "flagged" || s.status === "billing"
  );

  return (
    <div className="p-6 border-b border-neutral-800">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-neutral-500 uppercase tracking-wider font-semibold">
          Active Tables
        </div>
        <button
          onClick={() => setShowOpenDialog(true)}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-xs font-semibold transition-colors"
        >
          <Plus size={14} /> Open Table
        </button>
      </div>

      {activeTables.length === 0 ? (
        <div className="text-center py-6 text-neutral-600 text-sm">
          No active tables
        </div>
      ) : (
        <div className="space-y-2">
          {activeTables.map((session) => (
            <div
              key={session.id}
              className={`flex items-center justify-between p-3 rounded-xl border ${
                session.status === "flagged"
                  ? "bg-red-500/5 border-red-500/20"
                  : session.status === "billing"
                  ? "bg-amber-500/5 border-amber-500/20"
                  : "bg-neutral-900 border-neutral-800/50"
              }`}
            >
              <div>
                <div className="font-semibold text-sm">
                  Table {session.table_number}
                  {session.status === "flagged" && (
                    <span className="ml-2 text-xs text-red-400">FLAGGED</span>
                  )}
                  {session.status === "billing" && (
                    <span className="ml-2 text-xs text-amber-400">BILLING</span>
                  )}
                </div>
                <div className="text-xs text-neutral-500">
                  {session.guest_count} guests &middot; Code: {session.table_code} &middot;{" "}
                  {formatINR(session.total_spend)} spent
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => closeTable(session.id)}
                  className="p-2 rounded-lg hover:bg-neutral-800 text-neutral-500 hover:text-amber-400 transition-colors"
                  title="Close table / billing"
                >
                  <CreditCard size={16} />
                </button>
                <button
                  onClick={() => flagTable(session.id)}
                  className="p-2 rounded-lg hover:bg-neutral-800 text-neutral-500 hover:text-red-400 transition-colors"
                  title="Flag table"
                >
                  <Flag size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showOpenDialog && (
        <OpenTableDialog onClose={() => setShowOpenDialog(false)} />
      )}
    </div>
  );
}
