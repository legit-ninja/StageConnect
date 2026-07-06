# Anti-abuse and platform safety (music / gigs)

## Decision

StageConnect must not be usable for exploitation, off-platform booking scams, pay-to-play schemes that bypass platform oversight, or arrangements that hide who is connecting with whom. We prioritize verified bookers, act owners, and transparent gig records over opaque commercial exploitation.

## Product rules

1. **No off-platform escape hatches** — Features must not let two accounts fully leave the platform to transact or communicate. No open/anonymous direct messages; messaging only on gig or promoter-connection threads (`THREAD` model). A promoter-connection thread opens only after the connection is fully **active** (act-owner-confirmed, and guardian-approved where the booker is a minor).

2. **Verification gate** — Unverified users cannot create offerings, send gig requests, send promoter invites, create invite tokens, or redeem invite tokens.

3. **Auditable connections** — Gigs, promoter connections, invite-token redemptions, and payments log timestamps and actor IDs. No silent or anonymous actions.

4. **Owner-confirmed invite redemption** — Invite links can be forwarded; redemption never activates a promoter connection by itself. The act owner must confirm the specific verified identity that redeemed the token before the connection (and its message thread) goes active.

5. **Reporting** — Report control on every profile, offering, and gig; admin review queue (UI placeholders exist; policy enforced in API where implemented).

6. **Pattern flags (MVP, simple)** — `PlatformFlagType` examples:
   - `invite_redemption_rate` — owner exceeds invite-token rate limits (>10 active tokens, or >25 redemptions in 30 days).
   - `minor_connection_skew` — act owner / manager with disproportionate minor promoter connections.
   - `artist_fee_request` — signals around pay-to-play or improper fee solicitation (manual review).
   - `deposit_scam_pattern` — deposit requests inconsistent with listing terms.
   - `off_platform_contact` — new account attempting to move conversation off-platform.

## Public surfaces (offerings, public act pages, invite landing pages)

Public shareable pages are **inbound funnels only**:

- **Venue location (public):** Offerings expose `display_location` and jittered `public_lat/lng` (map circle). This is the **event venue area**, not the act's private service-area home base.
- **Act service area (private):** `acts.lat/lng/address` never appear on public serializers. Exact act base location is for confirmed parties only after an approved gig (or equivalent product rule).
- **No direct contact details** (phone, email, exact private address, social handles) on any public surface.
- **Identity minimization:** act owner shown as first name + last initial + verified badge on public pages. Full names for connected/booked counterparties only.
- **Structured fields only** on public pages until content moderation exists. Long-form `description` on acts/offerings renders only for authenticated, verified users so contact info cannot be smuggled onto the public surface.
- **EXIF stripped** from uploaded photos (GPS metadata would leak true locations).
- **Allowlist serialization:** public API endpoints use dedicated `PublicOffering` / public act response models. Never filter fields only in the frontend.

## Minors and 21+ venues

- Minors require a verified linked guardian before gig activity.
- Offerings with `requires_21_plus=true` block minor bookers from confirming gigs (`assert_booker_may_confirm_gig`).
- Promoter connections involving minors may enter `pending_guardian` until guardian approval is recorded.

## Pay-to-play and deposits

- UI copy must not encourage cash or off-platform payment.
- Platform deposits (when `payments_enabled=true`) flow through Stripe; `PAYMENTS_ENABLED=false` during free launch (see free-launch strategy).
- Flag patterns that look like "pay us to get the slot" off-platform.

## UI and copy

- Invite landing pages state that ID verification is required for everyone.
- Do not display owner/booker contact details in ways that bypass in-app messaging before a verified gig context exists.

## Related documents

- [Liability](liability.md)
- [Public acts & invite links spec](../specs/public-acts-and-invite-links-spec.md)
- [Data model additions](../specs/data-model-additions.md)
- [Free launch strategy](../strategy/free-launch-strategy.md)
- Engineering: `.cursor/rules/stageconnect-mvp.mdc`
