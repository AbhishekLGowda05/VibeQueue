"use client";

import { useDashboardStore } from "@/stores/dashboard-store";
import LoginForm from "@/components/dashboard/LoginForm";
import DashboardView from "@/components/dashboard/DashboardView";

export default function DashboardPage() {
  const isAuthenticated = useDashboardStore((s) => s.isAuthenticated);

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return <DashboardView />;
}
