import Link from "next/link";

import { OfferingCard } from "@/components/marketplace/OfferingCard";
import type { OfferingSummary } from "@/lib/api";
import { getServerApiUrl } from "@/lib/server-api";

import styles from "./page.module.css";

const STEPS = [
  {
    icon: "🎤",
    title: "Create your profile",
    description:
      "Set your experience level and get verified. Act owners trust bookers who are transparent about their background.",
  },
  {
    icon: "🎵",
    title: "Browse verified offerings",
    description:
      "Explore live music gigs from trusted act owners. Filter by event type, genre, and price in your region.",
  },
  {
    icon: "🎸",
    title: "Book and perform",
    description:
      "Request a gig, coordinate with the act owner in-app, and enjoy a safe, vetted live music experience.",
  },
];

const VALUES = [
  {
    icon: "🛡",
    title: "Trust first",
    description:
      "Every booker is verified. Every act owner is vetted. Safety is not optional on StageConnect.",
  },
  {
    icon: "★",
    title: "Quality acts",
    description:
      "Curated offerings from passionate musicians and performers who care about their craft and audience.",
  },
  {
    icon: "🤝",
    title: "Community driven",
    description:
      "Built on promoter connections and verified relationships — not anonymous strangers.",
  },
];

async function loadFeaturedOfferings(): Promise<OfferingSummary[]> {
  try {
    const response = await fetch(`${getServerApiUrl()}/offerings`, { next: { revalidate: 60 } });
    if (!response.ok) return [];
    const offerings = (await response.json()) as OfferingSummary[];
    return offerings.slice(0, 6);
  } catch {
    return [];
  }
}

export default async function Home() {
  const offerings = await loadFeaturedOfferings();

  return (
    <div className={styles.home}>
      <section className={styles.hero}>
        <div className={styles.heroBackground} aria-hidden="true" />
        <div className={`${styles.heroOverlay} heroOverlay`} aria-hidden="true" />
        <div className={`${styles.heroContent} scrollFadeIn`}>
          <span className={styles.heroBadge}>Trust-first gig marketplace</span>
          <h1 className={`${styles.heroTitle} textBalance`}>
            Where bookers and acts connect with confidence
          </h1>
          <p className={styles.heroSubtitle}>
            Discover verified live music experiences from trusted act owners. Every offering is
            vetted, every booker is identity-checked.
          </p>
          <div className={styles.heroActions}>
            <Link href="/offerings" className={styles.primaryButton}>
              Browse offerings
            </Link>
            <Link href="/register" className={styles.secondaryButton}>
              Join as booker
            </Link>
          </div>
        </div>
      </section>

      <section id="how-it-works" className={styles.section}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeader}>
            <span className="sectionEyebrow">How it works</span>
            <h2 className={styles.sectionTitle}>A simpler way to book live music</h2>
          </div>
          <div className={styles.stepsGrid}>
            {STEPS.map((step, index) => (
              <article key={step.title} className={`${styles.stepCard} scrollFadeIn`}>
                <span className={styles.stepNumber}>{index + 1}</span>
                <div className={styles.stepIcon} aria-hidden="true">
                  {step.icon}
                </div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={`${styles.section} ${styles.featuredSection}`}>
        <div className={styles.sectionInner}>
          <div className={styles.featuredHeader}>
            <div>
              <span className="sectionEyebrow">Featured</span>
              <h2 className={styles.sectionTitle}>Curated acts</h2>
            </div>
            <Link href="/offerings" className={styles.viewAllLink}>
              View all →
            </Link>
          </div>
          {offerings.length > 0 ? (
            <div className={styles.featuredGrid}>
              {offerings.map((offering) => (
                <OfferingCard key={offering.id} offering={offering} />
              ))}
            </div>
          ) : (
            <p className={styles.emptyFeatured}>
              Offerings will appear here once act owners publish gigs. Try{" "}
              <Link href="/offerings">browsing all offerings</Link> or run{" "}
              <code>make seed</code> in development.
            </p>
          )}
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeader}>
            <span className="sectionEyebrow">Why StageConnect</span>
            <h2 className={styles.sectionTitle}>Built on trust</h2>
          </div>
          <div className={styles.valuesGrid}>
            {VALUES.map((value) => (
              <article key={value.title} className={styles.valueCard}>
                <div className={styles.valueIcon} aria-hidden="true">
                  {value.icon}
                </div>
                <h3>{value.title}</h3>
                <p>{value.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.ctaSection}>
        <div className={styles.ctaPanel}>
          <div className={styles.ctaBackground} aria-hidden="true" />
          <div className={styles.ctaContent}>
            <h2>Ready to book your next gig?</h2>
            <p>
              Join StageConnect today and connect with verified act owners for your next live
              music experience.
            </p>
            <div className={styles.ctaActions}>
              <Link href="/register" className={styles.primaryButton}>
                Create account
              </Link>
              <Link href="/offerings" className={`${styles.secondaryButton} ${styles.ctaSecondary}`}>
                Browse offerings
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
