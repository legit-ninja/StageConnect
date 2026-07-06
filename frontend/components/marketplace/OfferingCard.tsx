import Link from "next/link";

import { OfferingSummary } from "@/lib/api";

import { OfferingImage } from "./OfferingImage";
import { StarRating } from "./StarRating";
import { activityTypeLabel, genreLabel } from "./marketplaceLabels";
import styles from "./marketplace.module.css";

function formatPrice(price: string, promoterOnly: boolean): string {
  const amount = Number(price);
  if (promoterOnly && amount === 0) {
    return "Promoter connections only";
  }
  return `$${amount.toFixed(2)}`;
}

interface OfferingCardProps {
  offering: OfferingSummary;
  rating?: number | null;
}

export function OfferingCard({ offering, rating }: OfferingCardProps) {
  const photo = offering.photo_urls[0];

  return (
    <Link href={`/a/${offering.slug}`} className={`${styles.card} cardHover`}>
      <OfferingImage src={photo} alt={offering.act_name} className={styles.cardImage} />
      <div className={styles.cardBody}>
        <div className={styles.cardTitle}>{offering.act_name}</div>
        {offering.promoter_only_allowed ? (
          <span className={styles.badgeFriendsOnly}>Promoter connection only</span>
        ) : null}
        <div className={styles.cardMeta}>
          {activityTypeLabel(offering.activity_type)} · {offering.display_location}
        </div>
        {offering.genres.length > 0 ? (
          <div className={styles.chipRow}>
            {offering.genres.map((genre) => (
              <span key={genre} className={styles.chip}>
                {genreLabel(genre)}
              </span>
            ))}
          </div>
        ) : null}
        {rating != null && rating > 0 ? (
          <StarRating value={rating} showValue />
        ) : null}
        {offering.availability ? (
          <div className={styles.cardMeta}>{offering.availability}</div>
        ) : null}
        <div className={styles.cardPrice}>
          {formatPrice(offering.price, offering.promoter_only_allowed)}
        </div>
      </div>
    </Link>
  );
}
