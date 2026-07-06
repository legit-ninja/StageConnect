"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { OfferingImage } from "@/components/marketplace/OfferingImage";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { activityTypeLabel, genreLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  AvailabilitySlot,
  GroupProfile,
  OfferingDetail,
  User,
  createGig,
  fetchCurrentUser,
  fetchGroupProfile,
  fetchOffering,
  fetchOfferingOpenSlots,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

const INQUIRY_NOTE_MIN_LENGTH = 10;

function formatSlotRange(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  return `${startDate.toLocaleDateString()} · ${startDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })} – ${endDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
}

export default function OfferingDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const slotIdFromQuery = searchParams.get("slot");
  const [offering, setOffering] = useState<OfferingDetail | null>(null);
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [openSlots, setOpenSlots] = useState<AvailabilitySlot[] | null>(null);
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(slotIdFromQuery);
  const [showContactForm, setShowContactForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [busy, setBusy] = useState(false);
  const [groupProfile, setGroupProfile] = useState<GroupProfile | null>(null);
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([]);

  useEffect(() => {
    const token = getToken();
    fetchOffering(id, token)
      .then(setOffering)
      .catch(() => {
        setError("Offering not found.");
      });
  }, [id]);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setOpenSlots(null);
      return;
    }
    fetchCurrentUser(token)
      .then((currentUser) => {
        setUser(currentUser);
        if (currentUser.is_booker && currentUser.verification_status === "verified") {
          const slotsPromise = fetchOfferingOpenSlots(token, id).then(setOpenSlots);
          const familyPromise =
            currentUser.booker_type === "group"
              ? fetchGroupProfile(token).then((profile) => {
                  setGroupProfile(profile);
                  setSelectedMemberIds(profile.members.map((m) => m.id));
                })
              : Promise.resolve(undefined);
          return Promise.all([slotsPromise, familyPromise]);
        }
        setOpenSlots(null);
        return undefined;
      })
      .catch(() => {
        setUser(null);
        setOpenSlots(null);
      });
  }, [id]);

  useEffect(() => {
    if (slotIdFromQuery) {
      setSelectedSlotId(slotIdFromQuery);
      setShowContactForm(false);
    }
  }, [slotIdFromQuery]);

  function familyMemberPayload(): { group_member_ids?: string[] } {
    if (user?.booker_type !== "group") return {};
    return { group_member_ids: selectedMemberIds };
  }

  async function handleSlotGig(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !offering || !selectedSlotId) return;
    if (user?.booker_type === "group" && selectedMemberIds.length === 0) {
      setSubmitError("Select at least one family member for this gig.");
      return;
    }
    setBusy(true);
    setSubmitError(null);
    const note = String(new FormData(event.currentTarget).get("note") || "");
    try {
      await createGig(token, {
        offering_id: offering.id,
        availability_slot_id: selectedSlotId,
        note: note || undefined,
        ...familyMemberPayload(),
      });
      setSuccess(true);
    } catch (err: unknown) {
      setSubmitError(err instanceof ApiError ? err.message : "Unable to submit gig request.");
    } finally {
      setBusy(false);
    }
  }

  async function handleContactSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !offering) return;
    const note = String(new FormData(event.currentTarget).get("note") || "").trim();
    if (note.length < INQUIRY_NOTE_MIN_LENGTH) {
      setSubmitError(`Please enter at least ${INQUIRY_NOTE_MIN_LENGTH} characters.`);
      return;
    }
    if (user?.booker_type === "group" && selectedMemberIds.length === 0) {
      setSubmitError("Select at least one family member for this gig.");
      return;
    }
    setBusy(true);
    setSubmitError(null);
    try {
      await createGig(token, {
        offering_id: offering.id,
        note,
        ...familyMemberPayload(),
      });
      setSuccess(true);
    } catch (err: unknown) {
      setSubmitError(err instanceof ApiError ? err.message : "Unable to send message.");
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return (
      <div className={styles.detailPage}>
        <EmptyState
          title="Offering not found"
          description="This gig may have been removed or is no longer active."
          action={{ label: "Back to browse", href: "/offerings" }}
        />
      </div>
    );
  }

  if (!offering) {
    return (
      <div className={styles.detailPage}>
        <LoadingState variant="cards" count={1} label="Loading offering" />
      </div>
    );
  }

  const photo = offering.photo_urls[0];
  const photoCount = offering.photo_urls.length;
  const price = Number(offering.price);
  const isFriendOnly = offering.promoter_only_allowed;
  const hasOpenSlots = openSlots !== null && openSlots.length > 0;

  function renderGigSection() {
    if (success) {
      return (
        <InlineAlert variant="success">
          Your request was submitted on StageConnect.{" "}
          <Link href="/booker/gigs">View my gigs</Link>
        </InlineAlert>
      );
    }

    if (user === undefined || (user?.is_booker && openSlots === null && user.verification_status === "verified")) {
      return <LoadingState variant="table" count={2} label="Loading account" />;
    }

    if (user === null) {
      return (
        <div className={styles.detailSection}>
          <p>Sign in to request a gig on this offering.</p>
          <Link href={`/login?next=/offerings/${id}`} className={styles.button}>
            Sign in
          </Link>
        </div>
      );
    }

    if (!user.is_booker) {
      return (
        <InlineAlert variant="warning">
          Your account is not set up as a booker. Update your profile or register as a booker.
        </InlineAlert>
      );
    }

    if (user.is_minor) {
      return (
        <InlineAlert variant="warning">
          Minor accounts require a verified guardian before gig activity.
        </InlineAlert>
      );
    }

    if (user.verification_status !== "verified") {
      return <BlockedAction user={user} action="request gigs" />;
    }

    const friendNotice = isFriendOnly ? (
      <InlineAlert variant="info">
        This is a promoter-connection-only gig. The host must send you a promoter connection and you
        must accept before you can request this gig.
      </InlineAlert>
    ) : null;

    const groupPicker =
      user.booker_type === "group" ? (
        <fieldset className={styles.slotList}>
          <legend>Who is live music?</legend>
          {!groupProfile || groupProfile.members.length === 0 ? (
            <InlineAlert variant="warning">
              Set up your group roster in{" "}
              <Link href="/settings">Settings</Link> before gig.
            </InlineAlert>
          ) : (
            groupProfile.members.map((member) => (
              <label key={member.id} className={styles.slotRow}>
                <input
                  type="checkbox"
                  checked={selectedMemberIds.includes(member.id)}
                  onChange={(e) => {
                    setSelectedMemberIds((prev) =>
                      e.target.checked
                        ? [...prev, member.id]
                        : prev.filter((id) => id !== member.id),
                    );
                  }}
                />
                {member.display_name}
                {member.is_minor ? " (minor)" : ""}
              </label>
            ))
          )}
        </fieldset>
      ) : null;

    if (showContactForm || !hasOpenSlots) {
      return (
        <div className={styles.detailSection}>
          {friendNotice}
          {!hasOpenSlots ? (
            <InlineAlert variant="info">
              No times available right now — send a message and the host will get back to you on
              the platform.{" "}
              <Link href="/calendar">Browse the calendar</Link> for other offerings.
            </InlineAlert>
          ) : (
            <p className={styles.cardMeta}>
              Ask a question before gig, or{" "}
              <button
                type="button"
                className={styles.buttonSecondary}
                onClick={() => setShowContactForm(false)}
              >
                return to available times
              </button>
              .
            </p>
          )}
          <form onSubmit={handleContactSubmit}>
            {groupPicker}
            <label>
              Message to host (required)
              <textarea
                name="note"
                rows={4}
                maxLength={2000}
                required
                minLength={INQUIRY_NOTE_MIN_LENGTH}
                placeholder="Introduce yourself and what you are looking for…"
              />
            </label>
            {submitError ? <InlineAlert variant="error">{submitError}</InlineAlert> : null}
            <button className={styles.button} type="submit" disabled={busy}>
              {busy ? "Sending…" : "Contact host"}
            </button>
          </form>
        </div>
      );
    }

    return (
      <div className={styles.detailSection}>
        {friendNotice}
        {slotIdFromQuery ? (
          <InlineAlert variant="info">
            You selected a time from the calendar. Confirm below to request that slot.
          </InlineAlert>
        ) : null}
        <form onSubmit={handleSlotGig}>
          {groupPicker}
          <fieldset className={styles.slotList}>
            <legend>Choose an available time</legend>
            {openSlots?.map((slot) => (
              <label key={slot.id} className={styles.slotRow}>
                <input
                  type="radio"
                  name="availability_slot_id"
                  value={slot.id}
                  checked={selectedSlotId === slot.id}
                  onChange={() => setSelectedSlotId(slot.id)}
                  required
                />
                {formatSlotRange(slot.start_at, slot.end_at)}
              </label>
            ))}
          </fieldset>
          <label>
            Note to host (optional)
            <textarea name="note" rows={3} maxLength={2000} />
          </label>
          {submitError ? <InlineAlert variant="error">{submitError}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy || !selectedSlotId}>
            {busy ? "Submitting…" : "Request gig"}
          </button>
        </form>
        <p className={styles.cardMeta}>
          <button
            type="button"
            className={styles.buttonSecondary}
            onClick={() => setShowContactForm(true)}
          >
            Ask a question first
          </button>
        </p>
      </div>
    );
  }

  return (
    <div className={styles.detailPage}>
      <p>
        <Link href="/offerings">← Back to browse</Link>
      </p>
      <OfferingImage src={photo} alt={offering.act_name} className={styles.detailImage} />
      {photoCount > 1 ? (
        <p className={styles.cardMeta}>+{photoCount - 1} more photo(s)</p>
      ) : null}
      <h1>{offering.act_name}</h1>
      {offering.genres.length > 0 ? (
        <div className={styles.chipRow}>
          {offering.genres.map((style) => (
            <span key={style} className={styles.chip}>
              {genreLabel(style)}
            </span>
          ))}
        </div>
      ) : null}
      <p>
        {activityTypeLabel(offering.activity_type)}
        {offering.act_type ? ` · ${offering.act_type}` : ""}
        {isFriendOnly ? (
          <>
            {" "}
            <span className={styles.badgeFriendsOnly}>Promoter connection only</span>
          </>
        ) : null}
      </p>
      <p>
        <strong>
          {isFriendOnly && price === 0 ? "Promoter connection only" : `$${price.toFixed(2)}`}
        </strong>
      </p>
      <div className={styles.detailSection}>
        <h2>Location</h2>
        <p>{offering.display_location}</p>
      </div>
      {offering.availability ? (
        <div className={styles.detailSection}>
          <h2>Availability notes</h2>
          <p>{offering.availability}</p>
        </div>
      ) : null}
      {offering.description ? (
        <div className={styles.detailSection}>
          <h2>About</h2>
          <p>{offering.description}</p>
        </div>
      ) : null}
      <div className={styles.detailSection}>
        <h2>Request a gig</h2>
        {renderGigSection()}
        <p className={`${styles.cardMeta} ${styles.cardMetaSpaced}`}>
          All gigs and payments stay on StageConnect for your safety.
        </p>
      </div>
    </div>
  );
}
