"use client";

import { use } from "react";
import { useGuestStore } from "@/stores/guest-store";
import JoinScreen from "@/components/guest/JoinScreen";
import QueueView from "@/components/guest/QueueView";

export default function GuestPage({
  params,
}: {
  params: Promise<{ venue: string }>;
}) {
  const { venue } = use(params);
  const isJoined = useGuestStore((s) => s.isJoined);

  if (!isJoined) {
    return <JoinScreen venueSlug={venue} />;
  }

  return <QueueView />;
}
