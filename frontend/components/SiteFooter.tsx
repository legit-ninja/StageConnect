import Link from "next/link";

import styles from "./SiteFooter.module.css";

function StageIcon() {
  return (
    <svg
      className={styles.brandMark}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      aria-hidden="true"
    >
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  );
}

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.grid}>
          <div>
            <Link href="/" className={styles.brandRow}>
              <StageIcon />
              StageConnect
            </Link>
            <p className={styles.tagline}>
              A trust-first gig marketplace connecting verified bookers with act owners
              for unforgettable live music experiences.
            </p>
            <p className={styles.trustRow}>Verified bookers and trusted act owners</p>
          </div>

          <div>
            <h2 className={styles.columnTitle}>Explore</h2>
            <ul className={styles.linkList}>
              <li>
                <Link href="/offerings">Browse offerings</Link>
              </li>
              <li>
                <Link href="/#how-it-works">How it works</Link>
              </li>
              <li>
                <Link href="/register">Create account</Link>
              </li>
            </ul>
          </div>

          <div>
            <h2 className={styles.columnTitle}>For act owners</h2>
            <ul className={styles.linkList}>
              <li>
                <Link href="/act-owner/offerings">Manage offerings</Link>
              </li>
              <li>
                <Link href="/act-owner/offerings/new">Create offering</Link>
              </li>
              <li>
                <Link href="/#how-it-works">Safety and trust</Link>
              </li>
            </ul>
          </div>
        </div>

        <div className={styles.bottom}>
          <p>&copy; {year} StageConnect. All rights reserved.</p>
          <p>Built with trust at the core</p>
        </div>
      </div>
    </footer>
  );
}
