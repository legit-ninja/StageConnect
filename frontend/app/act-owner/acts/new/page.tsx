"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  parseGenresFromForm,
  GenresFields,
  validateActGenres,
} from "@/components/marketplace/GenresFields";
import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  ActCategory,
  User,
  createActOwnerAct,
  fetchCurrentUser,
  fetchActCategories,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function NewActPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [categories, setCategories] = useState<ActCategory[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [categoryId, setCategoryId] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token).then(setUser);
    fetchActCategories().then((items) => {
      setCategories(items);
      if (items[0]) {
        setCategoryId(items[0].id);
      }
    });
  }, [router]);

  const selectedCategoryName =
    categories.find((item) => item.id === categoryId)?.name ?? categories[0]?.name ?? "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !categories[0]) return;
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const genres = parseGenresFromForm(form, selectedCategoryName);
    if (selectedCategoryName === "band") {
      const validationError = validateActGenres(genres);
      if (validationError) {
        setError(validationError);
        setBusy(false);
        return;
      }
    }
    try {
      await createActOwnerAct(token, {
        act_category_id: String(form.get("act_category_id")),
        name: String(form.get("name")),
        act_type: String(form.get("act_type") || "") || null,
        years_active: form.get("years_active") ? Number(form.get("years_active")) : null,
        description: String(form.get("description") || "") || null,
        lat: Number(form.get("lat")),
        lng: Number(form.get("lng")),
        address: String(form.get("address")),
        photo_urls: [],
        genres,
      });
      router.push("/act-owner/acts");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Failed to create act.");
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
      <h1>Add act</h1>
      <BlockedAction user={user} action="add acts" />
      {user.verification_status === "verified" ? (
        <form onSubmit={handleSubmit}>
          <label>
            Act category
            <select
              name="act_category_id"
              required
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
            >
              {categories.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <GenresFields categoryName={selectedCategoryName} />
          <label>
            Name
            <input name="name" required />
          </label>
          <label>
            Act type
            <input name="act_type" placeholder="e.g. Jazz trio, solo acoustic" />
          </label>
          <label>
            Years active
            <input name="years_active" type="number" min={0} />
          </label>
          <label>
            Description
            <textarea name="description" rows={3} />
          </label>
          <label>
            Address
            <input name="address" required defaultValue="Nashville, TN 37203" />
          </label>
          <label>
            Latitude
            <input name="lat" type="number" step="any" required defaultValue={36.1627} />
          </label>
          <label>
            Longitude
            <input name="lng" type="number" step="any" required defaultValue={-86.7816} />
          </label>
          {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy}>
            {busy ? "Saving…" : "Create act"}
          </button>
        </form>
      ) : null}
      <Link href="/act-owner/acts">Cancel</Link>
    </div>
  );
}
