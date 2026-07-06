"use client";

import { useEffect, useState } from "react";

import { activityTypeLabel } from "@/components/admin/adminLabels";
import styles from "@/components/admin/admin.module.css";
import { AdminShell } from "@/components/admin/AdminShell";
import { EmptyState } from "@/components/admin/EmptyState";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { DataTable } from "@/components/admin/PlaceholderPage";
import { gigStatusLabel } from "@/components/marketplace/marketplaceLabels";
import { ApiError, GigRequest, fetchAdminGigs } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

export default function AdminGigsPage() {
  const { token } = useAdminAuth();
  const [gigs, setGigs] = useState<GigRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetchAdminGigs(token)
      .then((response) => {
        setGigs(response.items);
        setTotal(response.total);
      })
      .catch((err: unknown) => {
        setError(
          err instanceof ApiError ? err.message : "Unable to load gigs.",
        );
      })
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <AdminShell
      title="Gigs"
      description="Gig request oversight across the marketplace"
    >
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {loading ? (
        <LoadingState label="Loading gigs" />
      ) : gigs.length === 0 ? (
        <EmptyState
          title="No gig requests"
          description="Gig requests from bookers will appear here for moderation preview."
          action={{ label: "Open verification queue", href: "/admin/verification" }}
        />
      ) : (
        <>
          <p className={styles.mutedText}>
            {total} gig request{total === 1 ? "" : "s"} total
          </p>
          <DataTable
            headers={["Booker", "Act Owner", "Offering", "Type", "Status", "Requested"]}
          >
            {gigs.map((gig) => (
              <tr key={gig.id}>
                <td>{gig.booker_email}</td>
                <td>{gig.act_owner_email}</td>
                <td>
                  {gig.act_name} ({activityTypeLabel(gig.activity_type)})
                </td>
                <td>{gig.payment_type === "free" ? "Free" : "Paid"}</td>
                <td>{gigStatusLabel(gig.status)}</td>
                <td>{new Date(gig.requested_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </DataTable>
        </>
      )}
    </AdminShell>
  );
}
