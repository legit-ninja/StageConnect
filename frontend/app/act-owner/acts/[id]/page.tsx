"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  parseGenresFromForm,
  GenresFields,
  validateActGenres,
} from "@/components/marketplace/GenresFields";
import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  Act,
  ApiError,
  ActCategory,
  User,
  fetchCurrentUser,
  fetchActOwnerActs,
  fetchActCategories,
  updateActOwnerAct,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function EditActPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [user, setUser] = useState<User | null>(null);
  const [act, setAct] = useState<Act | null | undefined>(undefined);
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
    Promise.all([fetchCurrentUser(token), fetchActCategories(), fetchActOwnerActs(token)])
      .then(([currentUser, categoryList, acts]) => {
        setUser(currentUser);
        setCategories(categoryList);
        const found = acts.find((item) => item.id === id) ?? null;
        setAct(found);
        if (found) {
          setCategoryId(found.act_category_id);
        }
      })
      .catch(() => setError("Unable to load act."));
  }, [id, router]);

  const selectedCategoryName =
    categories.find((item) => item.id === categoryId)?.name ?? "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
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
      await updateActOwnerAct(token, id, {
        act_category_id: String(form.get("act_category_id")),
        name: String(form.get("name")),
        act_type: String(form.get("act_type") || "") || null,
        description: String(form.get("description") || "") || null,
        address: String(form.get("address")),
        genres,
      });
      router.push("/act-owner/acts");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!user || act === undefined) {
    return (
      <div className={styles.formPage}>
        <LoadingState variant="table" count={4} label="Loading act" />
      </div>
    );
  }

  if (act === null) {
    return (
      <div className={styles.formPage}>
        <EmptyState
          title="Act not found"
          description="This act may have been removed or you do not have access."
          action={{ label: "Back to acts", href: "/act-owner/acts" }}
        />
      </div>
    );
  }

  return (
    <div className={styles.formPage}>
      <h1>Edit {act.name}</h1>
      <BlockedAction user={user} action="edit acts" />
      {user.verification_status === "verified" ? (
        <form onSubmit={handleSubmit}>
          <label>
            Act category
            <select
              name="act_category_id"
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
          <GenresFields
            categoryName={selectedCategoryName}
            defaultGenres={act.genres}
          />
          <label>
            Name
            <input name="name" required defaultValue={act.name} />
          </label>
          <label>
            Act type
            <input name="act_type" defaultValue={act.act_type ?? ""} />
          </label>
          <label>
            Description
            <textarea name="description" rows={3} defaultValue={act.description ?? ""} />
          </label>
          <label>
            Address
            <input name="address" required defaultValue={act.address} />
          </label>
          {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy}>
            Save
          </button>
        </form>
      ) : null}
      <Link href="/act-owner/acts">Back</Link>
    </div>
  );
}
