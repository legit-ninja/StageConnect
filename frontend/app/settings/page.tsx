"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  ApiError,
  GroupMemberInput,
  GroupProfile,
  BookerType,
  fetchCurrentUser,
  fetchGroupProfile,
  updateGroupProfile,
  updateProfile,
  type User,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

const EXPERIENCE_OPTIONS = [
  { value: "", label: "Not set" },
  { value: "1", label: "Self-reported: Beginner" },
  { value: "2", label: "Self-reported: Intermediate" },
  { value: "3", label: "Self-reported: Experienced" },
  { value: "4", label: "Self-reported: Professional" },
  { value: "5", label: "Self-reported: Industry veteran" },
];

type RosterRow = {
  display_name: string;
  booker_experience_level: string;
  is_minor: boolean;
};

function emptyRoster(size: number): RosterRow[] {
  return Array.from({ length: size }, () => ({
    display_name: "",
    booker_experience_level: "",
    is_minor: false,
  }));
}

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isActManager, setIsActManager] = useState(false);
  const [isBookingCoordinator, setIsBookingCoordinator] = useState(false);
  const [bookerExperienceLevel, setBookerExperienceLevel] = useState("");
  const [bookerType, setBookerType] = useState<BookerType>("individual");
  const [groupName, setGroupName] = useState("");
  const [groupSize, setGroupSize] = useState(2);
  const [roster, setRoster] = useState<RosterRow[]>(emptyRoster(2));
  const [message, setMessage] = useState<string | null>(null);
  const [groupMessage, setGroupMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [groupError, setGroupError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savingGroup, setSavingGroup] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login?next=/settings");
      return;
    }
    Promise.all([fetchCurrentUser(token), fetchGroupProfile(token)])
      .then(([u, group]) => {
        setUser(u);
        setIsActManager(u.is_act_manager);
        setIsBookingCoordinator(u.is_booking_coordinator);
        setBookerExperienceLevel(
          u.booker_experience_level ? String(u.booker_experience_level) : "",
        );
        applyGroupProfile(group);
      })
      .catch(() => router.replace("/login?next=/settings"));
  }, [router]);

  function applyGroupProfile(group: GroupProfile) {
    setBookerType(group.booker_type);
    setGroupName(group.group_name ?? "");
    setGroupSize(group.group_size ?? 2);
    if (group.booker_type === "group" && group.members.length > 0) {
      setRoster(
        group.members.map((m) => ({
          display_name: m.display_name,
          booker_experience_level: m.booker_experience_level
            ? String(m.booker_experience_level)
            : "",
          is_minor: m.is_minor,
        })),
      );
    } else if (group.group_size) {
      setRoster(emptyRoster(group.group_size));
    }
  }

  function handleGroupSizeChange(size: number) {
    const next = Math.min(20, Math.max(2, size));
    setGroupSize(next);
    setRoster((prev) => {
      if (prev.length === next) return prev;
      if (prev.length < next) {
        return [...prev, ...emptyRoster(next - prev.length)];
      }
      return prev.slice(0, next);
    });
  }

  async function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateProfile(token, {
        is_act_manager: isActManager,
        is_booking_coordinator: isBookingCoordinator,
        booker_experience_level:
          bookerType === "individual" && bookerExperienceLevel
            ? Number(bookerExperienceLevel)
            : null,
      });
      setUser(updated);
      setMessage("Profile updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save profile.");
    } finally {
      setSaving(false);
    }
  }

  async function handleGroupSubmit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setSavingGroup(true);
    setGroupError(null);
    setGroupMessage(null);
    try {
      const members: GroupMemberInput[] | null =
        bookerType === "group"
          ? roster.map((row, idx) => ({
              display_name: row.display_name,
              booker_experience_level: row.booker_experience_level
                ? Number(row.booker_experience_level)
                : null,
              is_minor: row.is_minor,
              sort_order: idx,
            }))
          : null;
      const updated = await updateGroupProfile(token, {
        booker_type: bookerType,
        group_name: bookerType === "group" ? groupName : null,
        group_size: bookerType === "group" ? groupSize : null,
        members,
      });
      applyGroupProfile(updated);
      const refreshed = await fetchCurrentUser(token);
      setUser(refreshed);
      setGroupMessage("Group profile updated.");
    } catch (err) {
      setGroupError(err instanceof ApiError ? err.message : "Could not save group profile.");
    } finally {
      setSavingGroup(false);
    }
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Settings"
        description="Manage your appearance and self-reported profile claims."
      />

      {user?.is_booker ? (
        <div className={styles.hubSection}>
          <h2 className={styles.hubSectionTitle}>Booker type</h2>
          <p className={styles.cardMeta}>
            Individual bookers book for themselves. Group accounts book for a named roster
            (including minors when you are the verified guardian).
          </p>
          {user ? (
            <form className={styles.formStack} onSubmit={handleGroupSubmit}>
              <div className={styles.formStack}>
                <p className={styles.fieldLabel}>Booker type</p>
                <label className={styles.checkboxLabel}>
                  <input
                    type="radio"
                    name="booker_type"
                    checked={bookerType === "individual"}
                    onChange={() => setBookerType("individual")}
                  />
                  Individual
                </label>
                <label className={styles.checkboxLabel}>
                  <input
                    type="radio"
                    name="booker_type"
                    checked={bookerType === "group"}
                    onChange={() => setBookerType("group")}
                  />
                  Group
                </label>
              </div>

              {bookerType === "group" ? (
                <>
                  <label className={styles.fieldLabel}>
                    Group name
                    <input
                      value={groupName}
                      onChange={(e) => setGroupName(e.target.value)}
                      required
                      maxLength={100}
                    />
                  </label>
                  <label className={styles.fieldLabel}>
                    Number of bookers in group
                    <input
                      type="number"
                      min={2}
                      max={20}
                      value={groupSize}
                      onChange={(e) => handleGroupSizeChange(Number(e.target.value))}
                      required
                    />
                  </label>
                  <h3 className={styles.hubSectionTitle}>Group roster</h3>
                  {roster.map((row, idx) => (
                    <div key={idx} className={styles.formStack}>
                      <label className={styles.fieldLabel}>
                        Member {idx + 1} name
                        <input
                          value={row.display_name}
                          onChange={(e) =>
                            setRoster((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, display_name: e.target.value } : r,
                              ),
                            )
                          }
                          required
                          maxLength={100}
                        />
                      </label>
                      <label className={styles.fieldLabel}>
                        Experience level
                        <select
                          value={row.booker_experience_level}
                          onChange={(e) =>
                            setRoster((prev) =>
                              prev.map((r, i) =>
                                i === idx
                                  ? { ...r, booker_experience_level: e.target.value }
                                  : r,
                              ),
                            )
                          }
                        >
                          {EXPERIENCE_OPTIONS.map((opt) => (
                            <option key={opt.value || "none"} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className={styles.checkboxLabel}>
                        <input
                          type="checkbox"
                          checked={row.is_minor}
                          onChange={(e) =>
                            setRoster((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, is_minor: e.target.checked } : r,
                              ),
                            )
                          }
                        />
                        Minor (you are the verified guardian)
                      </label>
                    </div>
                  ))}
                </>
              ) : null}

              {groupError ? <p className={styles.errorText}>{groupError}</p> : null}
              {groupMessage ? <p className={styles.successText}>{groupMessage}</p> : null}
              <button type="submit" className={styles.button} disabled={savingGroup}>
                {savingGroup ? "Saving…" : "Save booker type & roster"}
              </button>
            </form>
          ) : (
            <p>Loading profile…</p>
          )}
        </div>
      ) : null}

      <div className={styles.hubSection}>
        <h2 className={styles.hubSectionTitle}>Profile claims</h2>
        <p className={styles.cardMeta}>
          Manager and experience labels are self-reported — not verified credentials unless an
          admin has confirmed manager status separately.
        </p>
        {user ? (
          <form className={styles.formStack} onSubmit={handleProfileSubmit}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={isActManager}
                onChange={(e) => setIsActManager(e.target.checked)}
              />
              Self-reported: Act manager (manages acts)
            </label>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={isBookingCoordinator}
                onChange={(e) => setIsBookingCoordinator(e.target.checked)}
              />
              Self-reported: Booking coordinator (coordinates gigs)
            </label>
            {bookerType === "individual" ? (
              <label className={styles.fieldLabel}>
                Booker experience level
                <select
                  value={bookerExperienceLevel}
                  onChange={(e) => setBookerExperienceLevel(e.target.value)}
                >
                  {EXPERIENCE_OPTIONS.map((opt) => (
                    <option key={opt.value || "none"} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <p className={styles.cardMeta}>
                Experience levels for group accounts are set per roster member above.
              </p>
            )}
            {user.manager_verified ? (
              <p className={styles.verifiedBadge}>Verified manager (admin-confirmed)</p>
            ) : null}
            {error ? <p className={styles.errorText}>{error}</p> : null}
            {message ? <p className={styles.successText}>{message}</p> : null}
            <button type="submit" className={styles.button} disabled={saving}>
              {saving ? "Saving…" : "Save profile"}
            </button>
          </form>
        ) : (
          <p>Loading profile…</p>
        )}
      </div>

      <div className={styles.hubSection}>
        <h2 className={styles.hubSectionTitle}>Appearance</h2>
        <ThemeToggle />
      </div>
    </div>
  );
}
