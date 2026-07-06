"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { activityTypeLabel } from "@/components/admin/adminLabels";
import { AdminShell } from "@/components/admin/AdminShell";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { EmptyState } from "@/components/admin/EmptyState";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { DataTable } from "@/components/admin/PlaceholderPage";
import { StatusBadge } from "@/components/admin/StatusBadge";
import styles from "@/components/admin/admin.module.css";
import {
  AdminOfferingSummary,
  ApiError,
  fetchAdminOfferings,
  updateAdminOfferingActive,
} from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

type ActiveFilter = "all" | "active" | "inactive";

type PendingToggle = {
  offering: AdminOfferingSummary;
  nextActive: boolean;
};

export function AdminOfferingsContent() {
  const searchParams = useSearchParams();
  const actOwnerId = searchParams.get("act_owner_id");
  const { token } = useAdminAuth();
  const [offerings, setOfferings] = useState<AdminOfferingSummary[]>([]);
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>("all");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [pendingToggle, setPendingToggle] = useState<PendingToggle | null>(null);

  function loadOfferings() {
    if (!token) return;
    setLoading(true);
    const active =
      activeFilter === "all"
        ? undefined
        : activeFilter === "active";
    fetchAdminOfferings(token, { active, act_owner_id: actOwnerId ?? undefined })
      .then((response) => setOfferings(response.items))
      .catch(() => setError("Unable to load offerings."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadOfferings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, activeFilter, actOwnerId]);

  async function confirmToggle() {
    if (!token || !pendingToggle) return;
    const { offering, nextActive } = pendingToggle;
    setBusyId(offering.id);
    setError(null);
    setSuccess(null);
    try {
      await updateAdminOfferingActive(token, offering.id, nextActive);
      setSuccess(
        nextActive
          ? "Offering reactivated. Action logged in audit trail."
          : "Offering hidden from marketplace. Action logged in audit trail.",
      );
      loadOfferings();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusyId(null);
      setPendingToggle(null);
    }
  }

  const filterChips: { value: ActiveFilter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "active", label: "Active" },
    { value: "inactive", label: "Inactive" },
  ];

  return (
    <AdminShell
      title="Offerings"
      description={
        actOwnerId
          ? "Offerings for selected act owner"
          : "Moderation for act gig offerings"
      }
    >
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}

      <div className={styles.filterChips} role="group" aria-label="Filter offerings">
        {filterChips.map((chip) => (
          <button
            key={chip.value}
            type="button"
            className={`${styles.chip} ${
              activeFilter === chip.value ? styles.chipActive : ""
            }`}
            onClick={() => setActiveFilter(chip.value)}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState label="Loading offerings" />
      ) : offerings.length === 0 ? (
        <EmptyState
          title="No offerings found"
          description={
            actOwnerId
              ? "This act owner has no offerings matching the current filter."
              : activeFilter !== "all"
                ? "Try a different filter."
                : "No offerings on the platform yet."
          }
          action={{ label: "Back to dashboard", href: "/admin" }}
        />
      ) : (
        <DataTable
          headers={[
            "Act",
            "Act Owner",
            "Activity",
            "Price",
            "Availability",
            "Status",
            "Actions",
          ]}
        >
          {offerings.map((offering) => (
            <tr key={offering.id}>
              <td>{offering.act_name}</td>
              <td>{offering.act_owner_email}</td>
              <td>{activityTypeLabel(offering.activity_type)}</td>
              <td>${Number(offering.price).toFixed(2)}</td>
              <td>{offering.availability ?? "—"}</td>
              <td>
                <StatusBadge kind="offering" active={offering.active} />
              </td>
              <td>
                <button
                  type="button"
                  className={
                    offering.active ? styles.buttonDanger : styles.button
                  }
                  disabled={busyId === offering.id}
                  onClick={() =>
                    setPendingToggle({
                      offering,
                      nextActive: !offering.active,
                    })
                  }
                >
                  {offering.active ? "Deactivate" : "Reactivate"}
                </button>
              </td>
            </tr>
          ))}
        </DataTable>
      )}

      <ConfirmDialog
        open={pendingToggle !== null}
        title={
          pendingToggle?.nextActive
            ? "Reactivate offering?"
            : "Deactivate offering?"
        }
        description={
          pendingToggle
            ? pendingToggle.nextActive
              ? `"${pendingToggle.offering.act_name}" will be visible on the marketplace again. This action is logged.`
              : `"${pendingToggle.offering.act_name}" will be hidden from the marketplace. This action is logged.`
            : ""
        }
        confirmLabel={pendingToggle?.nextActive ? "Reactivate" : "Deactivate"}
        destructive={!pendingToggle?.nextActive}
        onConfirm={() => void confirmToggle()}
        onCancel={() => setPendingToggle(null)}
      />
    </AdminShell>
  );
}
