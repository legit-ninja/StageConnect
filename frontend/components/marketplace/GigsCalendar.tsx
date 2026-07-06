"use client";

import { useMemo, useState } from "react";

import {
  activityTypeLabel,
  gigStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import type { GigRequest } from "@/lib/api";
import { VerificationPill } from "@/components/marketplace/VerificationPill";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

type DotStatus = "pending" | "approved" | "declined" | "completed" | "cancelled";

const DOT_STATUS_CLASS: Record<DotStatus, string> = {
  pending: styles.statusDotPending,
  approved: styles.statusDotApproved,
  declined: styles.statusDotDeclined,
  completed: styles.statusDotCompleted,
  cancelled: styles.statusDotCancelled,
};

const BADGE_STATUS_CLASS: Record<DotStatus, string> = {
  pending: styles.statusBadgePending,
  approved: styles.statusBadgeApproved,
  declined: styles.statusBadgeDeclined,
  completed: styles.statusBadgeCompleted,
  cancelled: styles.statusBadgeCancelled,
};

const LEGEND: { key: DotStatus; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "declined", label: "Declined" },
  { key: "completed", label: "Completed" },
  { key: "cancelled", label: "Cancelled" },
];

function toIsoDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function formatMonthYear(year: number, month: number): string {
  return new Date(year, month, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

function buildCalendarCells(year: number, month: number): (number | null)[] {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const cells: (number | null)[] = [];
  for (let i = 0; i < first.getDay(); i += 1) {
    cells.push(null);
  }
  for (let day = 1; day <= last.getDate(); day += 1) {
    cells.push(day);
  }
  return cells;
}

function gigDotStatus(status: GigRequest["status"]): DotStatus {
  if (status === "pending_act_owner" || status === "pending_payment") return "pending";
  if (status === "approved") return "approved";
  if (status === "declined") return "declined";
  if (status === "completed") return "completed";
  return "cancelled";
}

function gigCalendarDate(gig: GigRequest): string | null {
  const iso = gig.scheduled_at ?? gig.requested_at;
  return iso ? iso.slice(0, 10) : null;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

export interface GigsCalendarProps {
  gigs: GigRequest[];
  onApprove?: (gig: GigRequest) => void;
  onDecline?: (gig: GigRequest) => void;
  onComplete?: (gig: GigRequest) => void;
}

export function GigsCalendar({
  gigs,
  onApprove,
  onDecline,
  onComplete,
}: GigsCalendarProps) {
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const cells = useMemo(
    () => buildCalendarCells(viewYear, viewMonth),
    [viewYear, viewMonth],
  );

  const gigsByDate = useMemo(() => {
    const map = new Map<string, GigRequest[]>();
    for (const gig of gigs) {
      const date = gigCalendarDate(gig);
      if (!date) continue;
      const list = map.get(date) ?? [];
      list.push(gig);
      map.set(date, list);
    }
    return map;
  }, [gigs]);

  const selectedGigs = selectedDate ? (gigsByDate.get(selectedDate) ?? []) : [];

  function shiftMonth(delta: number) {
    const next = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(next.getFullYear());
    setViewMonth(next.getMonth());
  }

  function goToday() {
    setViewYear(today.getFullYear());
    setViewMonth(today.getMonth());
    setSelectedDate(toIsoDate(today));
  }

  function handleDayClick(day: number) {
    const dateStr = toIsoDate(new Date(viewYear, viewMonth, day));
    setSelectedDate(dateStr);
  }

  return (
    <div className={styles.bookingsCalendarLayout}>
      <div className={styles.bookingsCalendarMain}>
        <div className={styles.calendarToolbar}>
          <div className={styles.calendarNav}>
            <button
              type="button"
              className={styles.buttonSecondary}
              onClick={() => shiftMonth(-1)}
              aria-label="Previous month"
            >
              Previous
            </button>
            <div className={styles.calendarMonthLabel}>
              {formatMonthYear(viewYear, viewMonth)}
            </div>
            <button
              type="button"
              className={styles.buttonSecondary}
              onClick={() => shiftMonth(1)}
              aria-label="Next month"
            >
              Next
            </button>
          </div>
          <button type="button" className={styles.buttonSecondary} onClick={goToday}>
            Today
          </button>
        </div>

        <div className={styles.calendarGrid}>
          {WEEKDAYS.map((label) => (
            <div key={label} className={styles.calendarWeekday}>
              {label}
            </div>
          ))}
          {cells.map((day, index) => {
            if (day === null) {
              return <div key={`empty-${index}`} className={styles.calendarDayOutside} />;
            }
            const dateStr = toIsoDate(new Date(viewYear, viewMonth, day));
            const dayGigs = gigsByDate.get(dateStr) ?? [];
            const isToday =
              today.getFullYear() === viewYear &&
              today.getMonth() === viewMonth &&
              today.getDate() === day;
            const isSelected = selectedDate === dateStr;

            return (
              <button
                key={dateStr}
                type="button"
                className={[
                  styles.calendarDay,
                  styles.bookingsCalendarDay,
                  isSelected ? styles.calendarDaySelected : "",
                  isToday && !isSelected ? styles.calendarDayToday : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => handleDayClick(day)}
              >
                <span className={styles.calendarDayNumber}>{day}</span>
                {dayGigs.length > 0 ? (
                  <div className={styles.calendarStatusDots}>
                    {dayGigs.slice(0, 3).map((gig) => (
                      <span
                        key={gig.id}
                        className={`${styles.statusDot} ${DOT_STATUS_CLASS[gigDotStatus(gig.status)]}`}
                        aria-hidden="true"
                      />
                    ))}
                    {dayGigs.length > 3 ? (
                      <span className={styles.calendarDotOverflow}>
                        +{dayGigs.length - 3}
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </button>
            );
          })}
        </div>

        <div className={styles.calendarLegend}>
          {LEGEND.map(({ key, label }) => (
            <span key={key} className={styles.calendarLegendItem}>
              <span className={`${styles.statusDot} ${DOT_STATUS_CLASS[key]}`} aria-hidden="true" />
              {label}
            </span>
          ))}
        </div>
      </div>

      <aside className={styles.bookingsCalendarSide}>
        <h2 className={styles.bookingsCalendarSideTitle}>
          {selectedDate
            ? new Date(`${selectedDate}T12:00:00`).toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
              })
            : "Select a date"}
        </h2>

        {!selectedDate ? (
          <p className={styles.slotMeta}>
            Click any day on the calendar to see gig requests scheduled for that date.
          </p>
        ) : selectedGigs.length === 0 ? (
          <p className={styles.slotMeta}>No gig requests for this date.</p>
        ) : (
          <div className={styles.slotList}>
            {selectedGigs.map((gig) => {
              const dotStatus = gigDotStatus(gig.status);
              const canRespond =
                gig.status === "pending_act_owner" || gig.status === "pending_payment";
              return (
                <article key={gig.id} className={styles.bookingsCalendarCard}>
                  <div>
                    <strong>
                      {gig.act_name} — {activityTypeLabel(gig.activity_type)}
                    </strong>
                    <div className={styles.slotMeta}>
                      From{" "}
                      {gig.is_group_gig && gig.booker_group_name
                        ? `Group — ${gig.booker_group_name} (${gig.group_party_size ?? "?"})`
                        : gig.booker_email}
                    </div>
                    <VerificationPill status={gig.booker_verification_status} />
                    {gig.scheduled_at ? (
                      <div className={styles.slotMeta}>Time: {formatTime(gig.scheduled_at)}</div>
                    ) : null}
                    {gig.note ? (
                      <div className={styles.slotMeta}>Note: {gig.note}</div>
                    ) : null}
                    <span
                      className={`${styles.statusBadge} ${BADGE_STATUS_CLASS[dotStatus]}`}
                    >
                      {gigStatusLabel(gig.status)}
                    </span>
                  </div>
                  {canRespond && onApprove && onDecline ? (
                    <div className={styles.buttonGroup}>
                      <button
                        type="button"
                        className={styles.button}
                        onClick={() => onApprove(gig)}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className={styles.buttonSecondary}
                        onClick={() => onDecline(gig)}
                      >
                        Decline
                      </button>
                    </div>
                  ) : gig.status === "approved" && onComplete ? (
                    <button
                      type="button"
                      className={styles.buttonSecondary}
                      onClick={() => onComplete(gig)}
                    >
                      Mark complete
                    </button>
                  ) : null}
                </article>
              );
            })}
          </div>
        )}
      </aside>
    </div>
  );
}
