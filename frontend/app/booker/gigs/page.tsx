"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { GigThreadPanel } from "@/components/marketplace/GigThreadPanel";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import {
  activityTypeLabel,
  gigStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import { ApiError, GigRequest, User, createGigReview, fetchGigs, fetchCurrentUser } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function BookerGigsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [gigs, setGigs] = useState<GigRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewBusy, setReviewBusy] = useState<string | null>(null);
  const [expandedThreadId, setExpandedThreadId] = useState<string | null>(null);

  async function submitReview(gigId: string, form: HTMLFormElement) {
    const token = getToken();
    if (!token) return;
    const data = new FormData(form);
    const rating = Number(data.get("rating"));
    const body = String(data.get("body") || "");
    setReviewBusy(gigId);
    setError(null);
    try {
      await createGigReview(token, gigId, { rating, body: body || undefined });
      form.reset();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Review failed.");
    } finally {
      setReviewBusy(null);
    }
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
        if (!currentUser.is_booker) {
          router.replace("/dashboard");
          return null;
        }
        return fetchGigs(token, "booker");
      })
      .then((response) => {
        if (response) setGigs(response.items);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("Booker access or verification required.");
        } else {
          setError("Unable to load gigs.");
        }
      });
  }, [router]);

  if (!user || gigs === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={5} label="Loading gigs" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="My gigs"
        description="Gig requests you have submitted on StageConnect."
      />
      <BlockedAction user={user} action="view gigs" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {user.verification_status === "verified" ? (
        gigs.length === 0 ? (
          <EmptyState
            title="No gigs yet"
            description="Browse offerings and request a gig to get started."
            action={{ label: "Find a gig", href: "/offerings" }}
          />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Offering</th>
                  <th>Act Owner</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Scheduled</th>
                  <th>Requested</th>
                </tr>
              </thead>
              <tbody>
                {gigs.map((gig) => (
                  <tr key={gig.id}>
                    <td>
                      <Link href={`/offerings/${gig.offering_id}`}>
                        {gig.act_name}
                      </Link>
                      <div className={styles.cardMeta}>
                        {activityTypeLabel(gig.activity_type)}
                      </div>
                    </td>
                    <td>{gig.act_owner_email}</td>
                    <td>{gig.payment_type === "free" ? "Free (friend)" : "Paid"}</td>
                    <td>{gigStatusLabel(gig.status)}</td>
                    <td>
                      {gig.scheduled_at
                        ? new Date(gig.scheduled_at).toLocaleString()
                        : "—"}
                    </td>
                    <td>
                      {new Date(gig.requested_at).toLocaleDateString()}
                      {gig.thread_id ? (
                        <div className={styles.cardMetaSpaced}>
                          <button
                            type="button"
                            className={styles.buttonSecondary}
                            onClick={() =>
                              setExpandedThreadId((current) =>
                                current === gig.thread_id ? null : gig.thread_id ?? null,
                              )
                            }
                          >
                            {expandedThreadId === gig.thread_id
                              ? "Hide messages"
                              : "View messages"}
                          </button>
                          {expandedThreadId === gig.thread_id ? (
                            <GigThreadPanel threadId={gig.thread_id} />
                          ) : null}
                        </div>
                      ) : null}
                      {gig.status === "completed" ? (
                        <form
                          className={styles.formPage}
                          style={{ marginTop: "0.5rem" }}
                          onSubmit={(event) => {
                            event.preventDefault();
                            void submitReview(gig.id, event.currentTarget);
                          }}
                        >
                          <label>
                            Rating
                            <select name="rating" required defaultValue="5">
                              {[5, 4, 3, 2, 1].map((value) => (
                                <option key={value} value={value}>
                                  {value} stars
                                </option>
                              ))}
                            </select>
                          </label>
                          <label>
                            Review (optional)
                            <textarea name="body" rows={2} />
                          </label>
                          <button
                            type="submit"
                            className={styles.buttonSecondary}
                            disabled={reviewBusy === gig.id}
                          >
                            {reviewBusy === gig.id ? "Saving…" : "Leave review"}
                          </button>
                        </form>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : null}

      <p>
        <Link href="/dashboard">Back to dashboard</Link>
      </p>
    </div>
  );
}
