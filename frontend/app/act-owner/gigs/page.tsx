"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { GigsCalendar } from "@/components/marketplace/GigsCalendar";
import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { ConfirmDialog } from "@/components/marketplace/ConfirmDialog";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { VerificationPill } from "@/components/marketplace/VerificationPill";
import {
  activityTypeLabel,
  gigStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  GigRequest,
  User,
  fetchGigs,
  fetchCurrentUser,
  updateGigStatus,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

function bookerInboxLabel(gig: GigRequest): string {
  if (gig.is_group_gig && gig.booker_group_name) {
    return `Group — ${gig.booker_group_name} (${gig.group_party_size ?? "?"} bookers)`;
  }
  return gig.booker_email;
}

type PendingAction = {
  gig: GigRequest;
  status: "approved" | "declined" | "completed";
};

type InboxView = "list" | "calendar";

export default function ActOwnerGigsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [gigs, setGigs] = useState<GigRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<InboxView>("list");

  function loadGigs(token: string) {
    fetchGigs(token, "act_owner")
      .then((response) => setGigs(response.items))
      .catch(() => setError("Unable to load gig requests."));
  }

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token)
      .then((currentUser) => {
        setUser(currentUser);
        if (!currentUser.is_act_owner) {
          router.replace("/dashboard");
          return;
        }
        loadGigs(token);
      })
      .catch(() => setError("Unable to load profile."));
  }, [router]);

  async function confirmAction() {
    if (!pending) return;
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await updateGigStatus(token, pending.gig.id, pending.status);
      loadGigs(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
      setPending(null);
    }
  }

  if (!user || gigs === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={5} label="Loading gigs" />
      </div>
    );
  }

  const emptyInbox = gigs.length === 0;

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Gig inbox"
        description="Review and respond to gig requests for your offerings."
      />
      <BlockedAction user={user} action="manage gigs" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {user.verification_status === "verified" ? (
        emptyInbox ? (
          <EmptyState
            title="No gig requests"
            description="When bookers request gigs on your offerings, they will appear here."
            action={{ label: "Manage offerings", href: "/act-owner/offerings" }}
          />
        ) : (
          <>
            <div className={styles.viewTabs} role="tablist" aria-label="Gig inbox view">
              <button
                type="button"
                role="tab"
                aria-selected={view === "list"}
                className={view === "list" ? styles.viewTabActive : styles.viewTab}
                onClick={() => setView("list")}
              >
                List
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={view === "calendar"}
                className={view === "calendar" ? styles.viewTabActive : styles.viewTab}
                onClick={() => setView("calendar")}
              >
                Calendar
              </button>
            </div>

            {view === "list" ? (
              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Booker</th>
                      <th>Offering</th>
                      <th>Status</th>
                      <th>Scheduled</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {gigs.map((gig) => (
                      <tr key={gig.id}>
                        <td>
                          <div>{bookerInboxLabel(gig)}</div>
                          {gig.is_group_gig ? (
                            <div className={styles.cardMeta}>{gig.booker_email}</div>
                          ) : null}
                          <VerificationPill status={gig.booker_verification_status} />
                          {gig.group_participants?.map((participant) => (
                            <div key={participant.gig_id} className={styles.cardMeta}>
                              {participant.participant_display_name}
                              {participant.booker_experience_warning ? (
                                <div className={styles.banner} role="status">
                                  {participant.booker_experience_warning}
                                </div>
                              ) : null}
                            </div>
                          ))}
                          {!gig.is_group_gig && gig.booker_experience_warning ? (
                            <div className={styles.banner} role="status">
                              {gig.booker_experience_warning}
                            </div>
                          ) : null}
                        </td>
                        <td>
                          {gig.act_name} — {activityTypeLabel(gig.activity_type)}
                          {gig.note ? (
                            <div className={styles.cardMeta}>Note: {gig.note}</div>
                          ) : null}
                        </td>
                        <td>{gigStatusLabel(gig.status)}</td>
                        <td>
                          {gig.scheduled_at
                            ? new Date(gig.scheduled_at).toLocaleString()
                            : new Date(gig.requested_at).toLocaleDateString()}
                        </td>
                        <td>
                          {gig.status === "pending_act_owner" ||
                          gig.status === "pending_payment" ? (
                            <div className={styles.buttonGroup}>
                              <button
                                type="button"
                                className={styles.button}
                                disabled={busy}
                                onClick={() =>
                                  setPending({ gig, status: "approved" })
                                }
                              >
                                Approve
                              </button>
                              <button
                                type="button"
                                className={styles.buttonSecondary}
                                disabled={busy}
                                onClick={() =>
                                  setPending({ gig, status: "declined" })
                                }
                              >
                                Decline
                              </button>
                            </div>
                          ) : gig.status === "approved" ? (
                            <button
                              type="button"
                              className={styles.buttonSecondary}
                              disabled={busy}
                              onClick={() =>
                                setPending({ gig, status: "completed" })
                              }
                            >
                              Mark complete
                            </button>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <GigsCalendar
                gigs={gigs}
                onApprove={(gig) => setPending({ gig, status: "approved" })}
                onDecline={(gig) => setPending({ gig, status: "declined" })}
                onComplete={(gig) => setPending({ gig, status: "completed" })}
              />
            )}
          </>
        )
      ) : null}

      <ConfirmDialog
        open={pending !== null}
        title={
          pending?.status === "approved"
            ? "Approve gig?"
            : pending?.status === "completed"
              ? "Mark gig complete?"
              : "Decline gig?"
        }
        description={
          pending
            ? pending.status === "completed"
              ? `Mark the gig with ${bookerInboxLabel(pending.gig)} for ${pending.gig.act_name} as complete so both parties can leave reviews.`
              : `${pending.status === "approved" ? "Approve" : "Decline"} the gig request from ${bookerInboxLabel(pending.gig)} for ${pending.gig.act_name}.`
            : ""
        }
        confirmLabel={
          pending?.status === "approved"
            ? "Approve"
            : pending?.status === "completed"
              ? "Mark complete"
              : "Decline"
        }
        destructive={pending?.status === "declined"}
        onConfirm={confirmAction}
        onCancel={() => setPending(null)}
      />

      <p>
        <Link href="/dashboard">Back to dashboard</Link>
      </p>
    </div>
  );
}
