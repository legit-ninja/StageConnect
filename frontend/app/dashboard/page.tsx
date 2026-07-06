"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { VerificationBanner } from "@/components/marketplace/VerificationBanner";
import { VerificationPill } from "@/components/marketplace/VerificationPill";
import styles from "@/components/marketplace/marketplace.module.css";
import { ApiError, User, fetchCurrentUser } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    fetchCurrentUser(token)
      .then(setUser)
      .catch((err: unknown) => {
        clearToken();
        if (err instanceof ApiError && err.status === 401) {
          router.replace("/login");
          return;
        }
        setError("Unable to load your profile.");
      });
  }, [router]);

  if (error) {
    return (
      <div className={styles.listingsPage}>
        <InlineAlert variant="error">{error}</InlineAlert>
      </div>
    );
  }

  if (!user) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={3} label="Loading dashboard" />
      </div>
    );
  }

  const isVerified = user.verification_status === "verified";
  const displayName = [user.first_name, user.last_name].filter(Boolean).join(" ").trim();

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title={displayName ? `Welcome, ${displayName}` : "Dashboard"}
        description={`Signed in as ${user.email}`}
        actions={<VerificationPill status={user.verification_status} />}
      />

      <VerificationBanner user={user} />

      {user.is_minor ? (
        <InlineAlert variant="warning">
          Minor accounts need a verified guardian linked before gig activity. Ask your
          guardian to complete verification and link your account.
        </InlineAlert>
      ) : null}

      <div className={styles.hubCardGrid}>
        {!isVerified ? (
          <article className={styles.hubCard}>
            <h3>Complete verification</h3>
            <p>Identity verification is required before you can request gigs or host offerings.</p>
            <Link href="/settings" className={styles.button}>
              Profile settings
            </Link>
          </article>
        ) : null}

        {user.is_booker ? (
          <article className={styles.hubCard}>
            <h3>Gig calendar</h3>
            <p>See open slots, your schedule, and local weather forecasts.</p>
            <Link href="/calendar" className={styles.button}>
              Open calendar
            </Link>
          </article>
        ) : null}

        {isVerified && user.is_booker ? (
          <article className={styles.hubCard}>
            <h3>Find a gig</h3>
            <p>Browse verified offerings and request your next live music experience.</p>
            <Link href="/offerings" className={styles.button}>
              Browse offerings
            </Link>
          </article>
        ) : null}

        {user.is_booker ? (
          <article className={styles.hubCard}>
            <h3>My gigs</h3>
            <p>Track pending, approved, and past gig requests.</p>
            <Link href="/booker/gigs" className={`${styles.button} ${styles.buttonSecondary}`}>
              View gigs
            </Link>
          </article>
        ) : null}

        {isVerified && user.is_act_owner ? (
          <article className={styles.hubCard}>
            <h3>Act owner hub</h3>
            <p>Manage acts, offerings, availability, and gig requests.</p>
            <Link href="/act-owner/offerings" className={styles.button}>
              Manage offerings
            </Link>
          </article>
        ) : null}

        {user.is_act_owner ? (
          <article className={styles.hubCard}>
            <h3>Gig inbox</h3>
            <p>Review and respond to booker requests.</p>
            <Link href="/act-owner/gigs" className={`${styles.button} ${styles.buttonSecondary}`}>
              Open inbox
            </Link>
          </article>
        ) : null}

        {user.is_act_owner ? (
          <article className={styles.hubCard}>
            <h3>Promoter connections</h3>
            <p>Invite trusted bookers for promoter-only offerings.</p>
            <Link href="/act-owner/promoters" className={`${styles.button} ${styles.buttonSecondary}`}>
              Manage connections
            </Link>
          </article>
        ) : null}

        {user.is_admin ? (
          <article className={styles.hubCard}>
            <h3>Admin panel</h3>
            <p>Moderation, verification queue, and platform audit tools.</p>
            <Link href="/admin" className={`${styles.button} ${styles.buttonSecondary}`}>
              Open admin
            </Link>
          </article>
        ) : null}
      </div>

      {!isVerified ? (
        <EmptyState
          title="Browse while you wait"
          description="You can explore offerings before verification completes, but booking and hosting stay locked."
          action={{ label: "Browse offerings", href: "/offerings" }}
        />
      ) : null}
    </div>
  );
}
