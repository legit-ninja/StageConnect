"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ActivityType,
  Act,
  ApiError,
  User,
  createActOwnerOffering,
  fetchCurrentUser,
  fetchActOwnerActs,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function NewOfferingPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [acts, setActs] = useState<Act[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token)
      .then(setUser)
      .then(() => fetchActOwnerActs(token!))
      .then(setActs)
      .catch(() => setError("Unable to load acts."));
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      await createActOwnerOffering(token, {
        act_id: String(form.get("act_id")),
        activity_type: String(form.get("activity_type")) as ActivityType,
        price: Number(form.get("price")),
        availability: String(form.get("availability") || "") || undefined,
        promoter_only_allowed: form.get("promoter_only_allowed") === "on",
        min_booker_experience: form.get("min_booker_experience")
          ? Number(form.get("min_booker_experience"))
          : undefined,
        max_venue_capacity: form.get("max_venue_capacity")
          ? Number(form.get("max_venue_capacity"))
          : undefined,
        sound_system_required: form.get("sound_system_required") === "on",
        equipment_provided: String(form.get("equipment_provided") || "either"),
      });
      router.push("/act-owner/offerings");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Failed to create offering.");
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return (
      <div className={styles.formPage}>
        <LoadingState variant="table" count={3} label="Loading" />
      </div>
    );
  }

  return (
    <div className={styles.formPage}>
      <PageHeader
        title="Create offering"
        description="Publish a verified live music experience for bookers in your region."
      />
      <BlockedAction user={user} action="create offerings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {user.verification_status === "verified" ? (
        acts.length === 0 ? (
          <EmptyState
            title="Add an act first"
            description="You need at least one act before creating an offering."
            action={{ label: "Add act", href: "/act-owner/acts/new" }}
          />
        ) : (
          <form onSubmit={handleSubmit}>
            <label>
              Act
              <select name="act_id" required>
                {acts.map((act) => (
                  <option key={act.id} value={act.id}>
                    {act.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Event type
              <select name="activity_type" required defaultValue="private_gig">
                <option value="private_gig">Private gig</option>
                <option value="corporate">Corporate event</option>
                <option value="wedding">Wedding</option>
                <option value="festival">Festival</option>
              </select>
            </label>
            <label>
              Price (USD)
              <input name="price" type="number" min={0} step="0.01" required />
            </label>
            <label>
              Availability
              <textarea name="availability" rows={2} placeholder="e.g. Weekends only" />
            </label>
            <label>
              <input name="promoter_only_allowed" type="checkbox" /> Promoter connection only (free gig path)
            </label>
            <label>
              Minimum booker experience (optional)
              <select name="min_booker_experience" defaultValue="">
                <option value="">No minimum</option>
                <option value="1">Beginner and up</option>
                <option value="2">Intermediate and up</option>
                <option value="3">Experienced and up</option>
                <option value="4">Professional and up</option>
                <option value="5">Industry veteran only</option>
              </select>
            </label>
            <label>
              Max venue capacity (optional)
              <input name="max_venue_capacity" type="number" min={10} max={100000} />
            </label>
            <label>
              <input name="sound_system_required" type="checkbox" /> Sound system required
            </label>
            <label>
              Equipment
              <select name="equipment_provided" defaultValue="either">
                <option value="provided">Provided by act owner</option>
                <option value="bring_own">Booker provides</option>
                <option value="either">Either</option>
              </select>
            </label>
            <button className={styles.button} type="submit" disabled={busy}>
              Create offering
            </button>
          </form>
        )
      ) : null}
      <Link href="/act-owner/offerings">Cancel</Link>
    </div>
  );
}
