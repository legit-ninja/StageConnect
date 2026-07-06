"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { StatCard } from "@/components/admin/StatCard";
import styles from "@/components/admin/admin.module.css";
import { AdminStats, fetchAdminStats } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

export default function AdminDashboardPage() {
  const { token } = useAdminAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    fetchAdminStats(token)
      .then(setStats)
      .catch(() => {
        setError("Unable to load dashboard stats.");
      });
  }, [token]);

  if (error) {
    return (
      <AdminShell title="Dashboard" description="Platform overview">
        <InlineAlert variant="error">{error}</InlineAlert>
      </AdminShell>
    );
  }

  if (!stats) {
    return (
      <AdminShell title="Dashboard" description="Platform overview">
        <LoadingState variant="stats" label="Loading dashboard stats" />
      </AdminShell>
    );
  }

  const needsReview = stats.unverified_users + stats.pending_users;
  const inactiveOfferings = stats.total_offerings - stats.active_offerings;

  return (
    <AdminShell
      title="Dashboard"
      description="Platform overview and quick actions"
      actions={
        needsReview > 0 ? (
          <Link href="/admin/verification" className={styles.button}>
            Review {needsReview} user{needsReview === 1 ? "" : "s"}
          </Link>
        ) : null
      }
    >
      <div className={styles.attentionGrid}>
        <div
          className={`${styles.attentionCard} ${
            needsReview > 0 ? styles.attentionCardUrgent : ""
          }`}
        >
          <div className={styles.attentionCardLabel}>Verification queue</div>
          <div className={styles.attentionCardValue}>{needsReview}</div>
          <Link href="/admin/verification" className={styles.muted}>
            Open queue →
          </Link>
        </div>
        <div className={styles.attentionCard}>
          <div className={styles.attentionCardLabel}>Inactive offerings</div>
          <div className={styles.attentionCardValue}>{inactiveOfferings}</div>
          <Link href="/admin/offerings" className={styles.muted}>
            Review offerings →
          </Link>
        </div>
        <div className={styles.attentionCard}>
          <div className={styles.attentionCardLabel}>Signups (7 days)</div>
          <div className={styles.attentionCardValue}>{stats.signups_last_7d}</div>
          <Link href="/admin/users" className={styles.muted}>
            Browse users →
          </Link>
        </div>
      </div>

      <h2 className={styles.sectionHeading}>Users</h2>
      <div className={styles.statGrid}>
        <StatCard label="Total users" value={stats.total_users} />
        <StatCard label="Verified" value={stats.verified_users} />
        <StatCard label="Unverified" value={stats.unverified_users} />
        <StatCard label="Pending review" value={stats.pending_users} />
        <StatCard label="Rejected" value={stats.rejected_users} />
        <StatCard label="Bookers" value={stats.booker_users} />
        <StatCard label="Act Owners" value={stats.act_owner_users} />
        <StatCard label="Trainer claims" value={stats.manager_users} />
        <StatCard label="Verified trainers" value={stats.verified_manager_users} />
        <StatCard label="OAuth linked" value={stats.oauth_users} />
      </div>

      <h2 className={styles.sectionHeading}>Marketplace</h2>
      <div className={styles.statGrid}>
        <StatCard label="Acts" value={stats.total_acts} />
        <StatCard label="Offerings" value={stats.total_offerings} />
        <StatCard label="Active offerings" value={stats.active_offerings} />
        <StatCard label="Admins" value={stats.admin_users} />
      </div>

      <p className={styles.muted}>
        <Link href="/admin/audit" className={styles.linkUnderline}>
          View audit log
        </Link>
      </p>
    </AdminShell>
  );
}
