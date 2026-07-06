"use client";

import styles from "@/components/marketplace/marketplace.module.css";
import { GENRE_OPTIONS, genreLabel } from "@/components/marketplace/marketplaceLabels";
import type { Genre } from "@/lib/api";

interface GenresFieldsProps {
  categoryName: string;
  defaultGenres?: Genre[];
}

export function GenresFields({
  categoryName,
  defaultGenres = [],
}: GenresFieldsProps) {
  if (categoryName !== "band") {
    return null;
  }

  return (
    <fieldset className={styles.ridingStylesFieldset}>
      <legend>Genres</legend>
      <p className={styles.cardMeta}>Select at least one genre bookers can expect from this act.</p>
      <div className={styles.ridingStylesOptions}>
        {GENRE_OPTIONS.map((genre) => (
          <label key={genre} className={styles.ridingStyleOption}>
            <input
              type="checkbox"
              name="genres"
              value={genre}
              defaultChecked={defaultGenres.includes(genre)}
            />
            {genreLabel(genre)}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function parseGenresFromForm(
  form: FormData,
  categoryName: string,
): Genre[] {
  if (categoryName !== "band") {
    return [];
  }
  return form.getAll("genres").map(String) as Genre[];
}

export function validateActGenres(genres: Genre[]): string | null {
  if (genres.length === 0) {
    return "Select at least one genre (Jazz, Rock, Pop, Country, or Classical).";
  }
  return null;
}
