"use client";

import { Suspense } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { LoadingState } from "@/components/admin/LoadingState";
import { AdminOfferingsContent } from "./AdminOfferingsContent";

export default function AdminOfferingsPage() {
  return (
    <Suspense
      fallback={
        <AdminShell title="Offerings" description="Moderation for act gig offerings">
          <LoadingState label="Loading offerings" />
        </AdminShell>
      }
    >
      <AdminOfferingsContent />
    </Suspense>
  );
}
