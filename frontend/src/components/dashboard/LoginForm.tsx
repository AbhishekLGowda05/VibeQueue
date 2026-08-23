"use client";

import { useState } from "react";
import { Music } from "lucide-react";
import { useDashboardStore } from "@/stores/dashboard-store";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoading, error } = useDashboardStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login(email, password);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 rounded-xl bg-violet-500/10 mb-3">
            <Music size={32} className="text-violet-400" />
          </div>
          <h1 className="text-2xl font-bold">VibeQueue Dashboard</h1>
          <p className="text-neutral-500 text-sm mt-1">Venue staff login</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full p-3 rounded-xl bg-neutral-900 border border-neutral-800 focus:border-violet-500 focus:outline-none text-sm"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full p-3 rounded-xl bg-neutral-900 border border-neutral-800 focus:border-violet-500 focus:outline-none text-sm"
          />

          {error && (
            <div className="text-red-400 text-sm text-center bg-red-500/10 p-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !email || !password}
            className="w-full py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-neutral-800 disabled:text-neutral-600 font-semibold transition-colors"
          >
            {isLoading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
