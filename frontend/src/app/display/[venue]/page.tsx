"use client";

import { use } from "react";
import AmbientDisplay from "@/components/ambient/AmbientDisplay";

export default function DisplayPage({
  params,
}: {
  params: Promise<{ venue: string }>;
}) {
  const { venue } = use(params);
  return <AmbientDisplay venueSlug={venue} />;
}
