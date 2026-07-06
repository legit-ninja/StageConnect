"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import { Act, ApiError, User, fetchCurrentUser, fetchActOwnerActs } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function ActOwnerActsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [acts, setActs] = useState<Act[] | null>(null);
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
        return fetchActOwnerActs(token);
      })
      .then((data) => {
        if (data) setActs(data);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("Act Owner access or verification required.");
        } else {
          setError("Unable to load acts.");
        }
      });
  }, [router]);

  if (!user || acts === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={4} label="Loading acts" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader title="My acts" description="Acts you host on StageConnect." />
      <BlockedAction user={user} action="manage acts" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {user.verification_status === "verified" ? (
        <>
          <p>
            <Link href="/act-owner/acts/new" className={styles.button}>
              Add act
            </Link>
          </p>
          {acts.length === 0 ? (
            <EmptyState
              title="No acts yet"
              description="Add your first act to create gig offerings."
              action={{ label: "Add act", href: "/act-owner/acts/new" }}
            />
          ) : (
            <ul>
              {acts.map((act) => (
                <li key={act.id}>
                  <Link href={`/act-owner/acts/${act.id}`}>{act.name}</Link> —{" "}
                  {act.address}
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
