"use client";

import { use } from "react";
import PlaybackPlayer from "@/components/playback/PlaybackPlayer";

export default function PlaybackPage({
  params,
}: {
  params: Promise<{ venue: string }>;
}) {
  const { venue } = use(params);
  return <PlaybackPlayer venueSlug={venue} />;
}
