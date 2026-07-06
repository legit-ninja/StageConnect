import type { Metadata } from "next";
import Link from "next/link";

import styles from "@/components/marketplace/marketplace.module.css";
import { InviteRedeemPanel } from "@/components/marketplace/InviteActions";
import type { PublicInvitePreview } from "@/lib/api";
import { buildAuthQuery } from "@/lib/funnel";
import { getServerApiUrl } from "@/lib/server-api";

async function loadInvite(token: string): Promise<PublicInvitePreview> {
  const response = await fetch(`${getServerApiUrl()}/public/invites/${token}`, {
    next: { revalidate: 30 },
  });
  if (!response.ok) {
    return {
      act_owner_first_name: "",
      act_owner_verified: false,
      act_names: [],
      token_valid: false,
      expired: false,
      revoked: false,
    };
  }
  return (await response.json()) as PublicInvitePreview;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ token: string }>;
}): Promise<Metadata> {
  const { token } = await params;
  const invite = await loadInvite(token);
  const title = invite.act_owner_first_name
    ? `Invite from ${invite.act_owner_first_name} — StageConnect`
    : "Promoter connection — StageConnect";
  return {
    title,
    robots: { index: false, follow: false },
  };
}

export default async function InviteLandingPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const invite = await loadInvite(token);
  const signupHref = `/register${buildAuthQuery({ src: "invite", ref: token, next: `/i/${token}` })}`;
  const loginHref = `/login${buildAuthQuery({ src: "invite", ref: token, next: `/i/${token}` })}`;

  return (
    <div className={styles.inviteHero}>
      <span className="sectionEyebrow">Verified promoter connection</span>
      <h1>You&apos;re invited to connect</h1>

      {!invite.token_valid ? (
        <div className={styles.banner} role="alert">
          {invite.expired
            ? "This invite link has expired."
            : invite.revoked
              ? "This invite link was revoked."
              : "This invite link is not valid."}
        </div>
      ) : (
        <>
          <p>
            <strong>{invite.act_owner_first_name}</strong>
            {invite.act_owner_verified ? " (verified act owner)" : ""} invited you to connect for
            free-gig eligibility.
          </p>
          {invite.act_names.length > 0 ? (
            <p>
              Acts: {invite.act_names.join(", ")}
            </p>
          ) : null}
          <p className={styles.cardMeta}>
            You must complete identity verification before redeeming this invite. The act owner
            confirms each redemption for safety.
          </p>
        </>
      )}

      <section className={styles.publicCta}>
        <Link href={signupHref} className={styles.button}>
          Create account to redeem
        </Link>
        <p className={styles.cardMeta}>
          Already verified? <Link href={loginHref}>Sign in</Link>
        </p>
        {invite.token_valid ? <InviteRedeemPanel token={token} /> : null}
      </section>
    </div>
  );
}
