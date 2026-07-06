"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { OfferingCard } from "@/components/marketplace/OfferingCard";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ActivityType,
  ActCategory,
  Genre,
  OfferingSummary,
  fetchActCategories,
  fetchOfferings,
} from "@/lib/api";
import { GENRE_OPTIONS, genreLabel } from "@/components/marketplace/marketplaceLabels";

const ACTIVITY_OPTIONS: { value: ActivityType | ""; label: string }[] = [
  { value: "", label: "All event types" },
  { value: "private_gig", label: "Private gig" },
  { value: "corporate", label: "Corporate event" },
  { value: "wedding", label: "Wedding" },
  { value: "festival", label: "Festival" },
];

const PRICE_BANDS: { label: string; min?: number; max?: number }[] = [
  { label: "Any price" },
  { label: "Under $500", max: 499.99 },
  { label: "$500–$1,500", min: 500, max: 1500 },
  { label: "Over $1,500", min: 1500.01 },
];

export default function OfferingsPage() {
  const [offerings, setOfferings] = useState<OfferingSummary[]>([]);
  const [categories, setCategories] = useState<ActCategory[]>([]);
  const [activityType, setActivityType] = useState<ActivityType | "">("");
  const [categoryId, setCategoryId] = useState("");
  const [priceBand, setPriceBand] = useState(0);
  const [genre, setGenre] = useState<Genre | "">("");
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActCategories()
      .then((items) => {
        setCategories(items);
        if (items[0]) {
          setCategoryId(items[0].id);
        }
      })
      .catch(() => {
        setError("Unable to load act categories.");
      });
  }, []);

  useEffect(() => {
    if (!categoryId) return;
    setLoading(true);
    const band = PRICE_BANDS[priceBand];
    fetchOfferings({
      activity_type: activityType || undefined,
      act_category_id: categoryId || undefined,
      min_price: band?.min,
      max_price: band?.max,
      genre: genre || undefined,
    })
      .then(setOfferings)
      .catch(() => {
        setError("Unable to load offerings.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [activityType, categoryId, priceBand, genre]);

  function clearFilters() {
    setActivityType("");
    setPriceBand(0);
    setGenre("");
  }

  const hasFilters =
    activityType !== "" ||
    priceBand !== 0 ||
    genre !== "" ||
    searchQuery.trim() !== "";

  const visibleOfferings = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return offerings;
    return offerings.filter(
      (offering) =>
        offering.act_name.toLowerCase().includes(query) ||
        offering.display_location.toLowerCase().includes(query),
    );
  }, [offerings, searchQuery]);

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Browse gigs"
        description="Verified live music offerings from trusted act owners."
      />

      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      <div className={styles.searchRow}>
        <input
          type="search"
          className={styles.searchInput}
          placeholder="Search by act name or location…"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          aria-label="Search offerings"
        />
      </div>

      <div className={styles.filters}>
        <select
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value)}
          aria-label="Act category"
        >
          {categories.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <select
          value={genre}
          onChange={(event) => setGenre(event.target.value as Genre | "")}
          aria-label="Genre"
        >
          <option value="">All genres</option>
          {GENRE_OPTIONS.map((g) => (
            <option key={g} value={g}>
              {genreLabel(g)}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.filterChips} role="group" aria-label="Event type">
        {ACTIVITY_OPTIONS.map((option) => (
          <button
            key={option.value || "all"}
            type="button"
            className={
              activityType === option.value
                ? `${styles.chip} ${styles.chipActive}`
                : styles.chip
            }
            onClick={() => setActivityType(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className={styles.filterChips} role="group" aria-label="Price range">
        {PRICE_BANDS.map((band, index) => (
          <button
            key={band.label}
            type="button"
            className={
              priceBand === index
                ? `${styles.chip} ${styles.chipActive}`
                : styles.chip
            }
            onClick={() => setPriceBand(index)}
          >
            {band.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState label="Loading offerings" />
      ) : visibleOfferings.length === 0 ? (
        <EmptyState
          title="No offerings found"
          description="Try adjusting your filters or run make seed to load dev data."
          action={
            hasFilters
              ? { label: "Clear filters", href: "#" }
              : undefined
          }
        >
          {hasFilters ? (
            <button
              type="button"
              className={styles.buttonSecondary}
              onClick={() => {
                clearFilters();
                setSearchQuery("");
              }}
            >
              Clear filters
            </button>
          ) : null}
        </EmptyState>
      ) : (
        <div className={styles.grid}>
          {visibleOfferings.map((offering) => (
            <OfferingCard key={offering.id} offering={offering} />
          ))}
        </div>
      )}
    </div>
  );
}
