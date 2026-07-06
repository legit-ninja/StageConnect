# Free Launch Strategy — config-gated monetization

**Decision:** StageConnect launches with **no booking fees** and **payments disabled by default** for all participants. Commission and Stripe are deferred, not abandoned. The free period buys liquidity and trust in local music scenes.

## Why free-first

- Incumbent behavior (DMs, Facebook event posts, word of mouth) is free. Asking for platform commission before value is proven reads as a middleman tax.
- The product at launch is **verification and auditability**; reviews and completed gig history are the compounding assets.
- "Free at launch, everyone verified" is a stronger pitch to venues and bookers than any price point.

## Implementation: turn payments off with config, not schema changes

Keep the entire `gig_requests` / `payment_transactions` model intact. The switch is configuration:

| Setting | Default (launch) | Purpose |
|---------|------------------|---------|
| `PAYMENTS_ENABLED=false` | off | Skip Stripe checkout; paid gigs may enter `pending_payment` stub or skip deposit recording per router logic |
| `PLATFORM_COMMISSION_PERCENT` | 10 | Used when payments turn on |
| Stripe env vars empty | — | Defer Connect onboarding for act owners |

- **KYC / admin verification is not deferred.** Free launch changes pricing, never the verification gate.
- When payments are off, avoid writing meaningless `$0` transaction rows; the completed `GIG_REQUEST` with `confirmed_snapshot` is the audit record.
- Tell users the truth: ToS and marketing say **"free during our founding period"**, not free forever.

## Social proof mechanics

1. **Reviews** — booking-gated, one per (gig, reviewer). Label promoter/free gigs on display so paid gig reviews are not diluted.
2. **Verified badge + gig count** on public share cards — trust signal for group chats and social posts.
3. **Milestones (later)** — share cards after completed gigs or reviews.

## Community incentives (status-based)

- **Founding booker / founding act owner badge** for users verified during the free-launch window.
- **Scene ambassador** outreach to venue bookers and promoters (manual, pre-payments).

## Monetization trigger (decide thresholds in writing)

Turn on payments when, in a launch region:

- Sufficient verified act owners and monthly **completed** gigs, and
- Repeat booking rate shows retention.

Flip sequence: announce to founding members first with grace period → enable Stripe onboarding prompts → default new offerings to paid-capable.

## What this does not change

- **Liability:** free gigs still need waivers, guardian flows, and legal gate before public launch (see `safety/liability.md`).
- **Anti-abuse:** all rules in `anti-abuse.md` apply with full force during free launch.
