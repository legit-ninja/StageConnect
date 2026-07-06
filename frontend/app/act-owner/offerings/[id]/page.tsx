"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { OfferingImage } from "@/components/marketplace/OfferingImage";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { OfferingSlotsSection } from "@/components/marketplace/OfferingSlotsSection";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  ActOwnerOffering,
  User,
  fetchCurrentUser,
  fetchActOwnerOfferings,
  publicActUrl,
  updateActOwnerOffering,
  uploadOfferingPhoto,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function EditOfferingPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [user, setUser] = useState<User | null>(null);
  const [offering, setOffering] = useState<ActOwnerOffering | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    Promise.all([fetchCurrentUser(token), fetchActOwnerOfferings(token)])
      .then(([currentUser, offerings]) => {
        setUser(currentUser);
        setOffering(offerings.find((item) => item.id === id) ?? null);
      })
      .catch(() => setError("Unable to load offering."));
  }, [id, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      await updateActOwnerOffering(token, id, {
        price: Number(form.get("price")),
        availability: String(form.get("availability") || "") || undefined,
        active: form.get("active") === "on",
      });
      router.push("/act-owner/offerings");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handlePhotoUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const token = getToken();
    const file = event.target.files?.[0];
    if (!token || !file) return;
    setBusy(true);
    setError(null);
    try {
      await uploadOfferingPhoto(token, id, file);
      setSuccess("Photo uploaded.");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  function copyShareLink() {
    if (!offering) return;
    const url = publicActUrl(offering.slug);
    void navigator.clipboard.writeText(url);
    setCopied(true);
  }

  if (!user || offering === undefined) {
    return (
      <div className={styles.formPage}>
        <LoadingState variant="table" count={4} label="Loading offering" />
      </div>
    );
  }

  if (offering === null) {
    return (
      <div className={styles.formPage}>
        <EmptyState
          title="Offering not found"
          description="This offering may have been removed or you do not have access."
          action={{ label: "Back to offerings", href: "/act-owner/offerings" }}
        />
      </div>
    );
  }

  const shareUrl = publicActUrl(offering.slug);
  const facebookShare = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;

  return (
    <div className={styles.formPage}>
      <PageHeader
        title="Edit offering"
        description="Update pricing, availability, and photos for this gig."
      />
      <BlockedAction user={user} action="edit offerings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}

      <div className={styles.shareBox}>
        <h2>Share offering</h2>
        <p className={styles.cardMeta}>{shareUrl}</p>
        <div className={styles.shareRow}>
          <button type="button" className={styles.buttonSecondary} onClick={copyShareLink}>
            {copied ? "Copied!" : "Copy link"}
          </button>
          <a
            href={facebookShare}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.buttonSecondary}
          >
            Share on Facebook
          </a>
        </div>
        <OfferingImage
          src={`/api/og/${offering.slug}`}
          alt="Share card preview"
          className={styles.sharePreview}
        />
      </div>

      {user.verification_status === "verified" ? (
        <>
          <label>
            Upload photo
            <input type="file" accept="image/*" onChange={handlePhotoUpload} disabled={busy} />
          </label>

          <form onSubmit={handleSubmit}>
            <label>
              Price (USD)
              <input
                name="price"
                type="number"
                min={0}
                step="0.01"
                required
                defaultValue={Number(offering.price)}
              />
            </label>
            <label>
              General availability notes
              <textarea
                name="availability"
                rows={2}
                placeholder="e.g. Weekends by appointment"
                defaultValue={offering.availability ?? ""}
              />
            </label>
            <label>
              <input name="active" type="checkbox" defaultChecked={offering.active} /> Active
            </label>
            <button className={styles.button} type="submit" disabled={busy}>
              Save
            </button>
          </form>

          <OfferingSlotsSection offeringId={offering.id} />
        </>
      ) : null}
      <Link href="/act-owner/offerings">Back</Link>
    </div>
  );
}
