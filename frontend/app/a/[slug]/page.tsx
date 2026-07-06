import type { Metadata } from "next";
import Link from "next/link";

import { OfferingImage } from "@/components/marketplace/OfferingImage";
import { StarRating } from "@/components/marketplace/StarRating";
import { activityTypeLabel, genreLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import type { PublicAct } from "@/lib/api";
import { buildAuthQuery } from "@/lib/funnel";
import { getServerApiUrl } from "@/lib/server-api";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

async function loadOffering(slug: string): Promise<PublicAct | null> {
  const response = await fetch(`${getServerApiUrl()}/public/acts/${slug}`, {
    next: { revalidate: 60 },
  });
  if (!response.ok) return null;
  return (await response.json()) as PublicAct;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const offering = await loadOffering(slug);
  if (!offering) {
    return { title: "Offering not found — StageConnect" };
  }

  const activity = activityTypeLabel(offering.activity_type);
  const description = `${activity} with ${offering.act_name} near ${offering.display_location}`;

  return {
    title: `${offering.act_name} — StageConnect`,
    description,
    robots: offering.active ? { index: true, follow: true } : { index: false, follow: false },
    openGraph: {
      title: `${offering.act_name} on StageConnect`,
      description,
      images: [`${SITE_URL}/api/og/${slug}`],
      url: `${SITE_URL}/a/${slug}`,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: offering.act_name,
      description,
      images: [`${SITE_URL}/api/og/${slug}`],
    },
  };
}

function formatPrice(price: string | null): string {
  if (!price || Number(price) === 0) return "Contact for pricing";
  return `$${Number(price).toFixed(2)}`;
}

export default async function PublicActPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const offering = await loadOffering(slug);

  if (!offering) {
    return (
      <div className={styles.detailPage}>
        <h1>Offering not found</h1>
        <p>This gig may have been removed.</p>
        <Link href="/offerings">Browse gigs</Link>
      </div>
    );
  }

  const signupHref = `/register${buildAuthQuery({ src: "public_act", ref: slug, next: `/a/${slug}` })}`;
  const primaryPhoto = offering.photo_urls[0];

  return (
    <div className={styles.publicOfferingPage}>
      {!offering.active ? (
        <div className={styles.banner} role="status">
          This offering is not currently accepting requests.
        </div>
      ) : null}

      <div className={styles.publicHero}>
        <OfferingImage
          src={primaryPhoto}
          alt={offering.act_name}
          className={styles.publicHeroImage}
        />
        {offering.photo_urls.length > 1 ? (
          <div className={styles.photoStrip}>
            {offering.photo_urls.slice(1, 5).map((url) => (
              <OfferingImage key={url} src={url} alt="" className={styles.photoThumb} />
            ))}
          </div>
        ) : null}
      </div>

      <header className={styles.publicHeader}>
        <h1>{offering.act_name}</h1>
        <div className={styles.chipRow}>
          <span className={styles.chip}>{activityTypeLabel(offering.activity_type)}</span>
          <span className={styles.chip}>{formatPrice(offering.price)}</span>
          {offering.act_type ? <span className={styles.chip}>{offering.act_type}</span> : null}
          {offering.genres.map((style) => (
            <span key={style} className={styles.chip}>
              {genreLabel(style)}
            </span>
          ))}
        </div>
      </header>

      <section className={styles.detailSection}>
        <h2>Gig details</h2>
        {offering.min_booker_experience_label ? (
          <p>{offering.min_booker_experience_label}</p>
        ) : null}
        {offering.max_venue_capacity ? (
          <p>Max venue capacity: {offering.max_venue_capacity}</p>
        ) : null}
        <p>{offering.sound_system_required ? "Sound system required" : "Sound system optional"}</p>
        <p>{offering.equipment_provided_label}</p>
      </section>

      <section className={styles.detailSection}>
        <h2>Approximate location</h2>
        <p>{offering.display_location}</p>
        <p className={styles.cardMeta}>
          Map shows an approximate area (within several miles) to protect act owner privacy.
        </p>
      </section>

      {offering.review_count > 0 && offering.review_average !== null ? (
        <section className={styles.detailSection}>
          <h2>Reviews</h2>
          <StarRating value={offering.review_average} size="md" showValue />
          <p className={styles.cardMeta}>
            {offering.review_count} review
            {offering.review_count === 1 ? "" : "s"}
          </p>
        </section>
      ) : null}

      <section className={`${styles.detailSection} ${styles.actOwnerCard}`}>
        <h2>Act Owner</h2>
        <p>
          {offering.act_owner_first_name} {offering.act_owner_last_initial}.
          {offering.act_owner_verified ? (
            <span className={styles.verifiedBadge}> Verified act owner</span>
          ) : null}
          {offering.act_owner_manager_verified ? (
            <span className={styles.verifiedBadge}> Verified trainer</span>
          ) : null}
        </p>
        <p className={styles.cardMeta}>Member since {offering.act_owner_member_since}</p>
      </section>

      {offering.active ? (
        <section className={styles.publicCta}>
          <p>Sign up and verify your identity to request a gig on this offering.</p>
          <Link href={signupHref} className={styles.button}>
            Sign up to request a gig
          </Link>
          <p className={styles.cardMeta}>
            Already have an account?{" "}
            <Link href={`/login${buildAuthQuery({ src: "public_act", ref: slug, next: `/a/${slug}` })}`}>
              Sign in
            </Link>
          </p>
        </section>
      ) : null}
    </div>
  );
}
