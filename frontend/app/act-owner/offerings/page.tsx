"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { activityTypeLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  ActOwnerOffering,
  User,
  fetchCurrentUser,
  fetchActOwnerOfferings,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function ActOwnerOfferingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [offerings, setOfferings] = useState<ActOwnerOffering[] | null>(null);
  const [error, setError] = useState<string | null>(null);

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
          return null;
        }
        return fetchActOwnerOfferings(token);
      })
      .then((data) => {
        if (data) setOfferings(data);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("Act Owner access or verification required.");
        } else {
          setError("Unable to load offerings.");
        }
      });
  }, [router]);

  if (!user || offerings === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={4} label="Loading offerings" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader title="My offerings" description="Gigs and experiences you offer." />
      <BlockedAction user={user} action="manage offerings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {user.verification_status === "verified" ? (
        <>
          <p>
            <Link href="/act-owner/offerings/new" className={styles.button}>
              Create offering
            </Link>
          </p>
          {offerings.length === 0 ? (
            <EmptyState
              title="No offerings yet"
              description="Create a offering from one of your acts."
              action={{ label: "Create offering", href: "/act-owner/offerings/new" }}
            />
          ) : (
            <ul>
              {offerings.map((offering) => (
                <li key={offering.id}>
                  <Link href={`/act-owner/offerings/${offering.id}`}>
                    {activityTypeLabel(offering.activity_type)} — $
                    {Number(offering.price).toFixed(2)}
                  </Link>
                  {offering.active ? "" : " (inactive)"}
                  {offering.promoter_only_allowed ? " · Promoter connection only" : ""}
                </li>
              ))}
            </ul>
          )}
        </>
      ) : null}
      <p>
        <Link href="/dashboard">Back to dashboard</Link>
      </p>
    </div>
  );
}
