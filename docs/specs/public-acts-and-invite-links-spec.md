# Spec — Public act pages & invite links

**Status:** Draft for implementation  
**Related:** `data-model-additions.md`, `anti-abuse.md`, `liability.md`, `free-launch-strategy.md`

## Purpose

StageConnect growth comes from existing scenes — venue bookers, promoters, band chats. Two inbound funnels:

1. **Public offering pages** — shareable URLs with Open Graph cards; booking gated behind signup + verification.
2. **Public act pages** — lightweight act profile at `/a/{slug}` for discovery (photos, genre, structured fields).
3. **Invite links** — tokenized promoter invites at `/i/{token}` without knowing the booker's account upfront.

Nothing here creates an off-platform escape hatch.

---

## Part 1 — Public offering pages

### Routes

| Route | Auth | Purpose |
|-------|------|---------|
| `GET /a/{slug}` (frontend) | Public | Public offering/act landing (SSR + OG) |
| `GET /api/public/offerings/{slug}` | Public | JSON via allowlisted serializer |
| `GET /api/offerings/{id}` | Verified | Full offering detail |

- `slug` is non-enumerable: `{kebab-act-name}-{6-char-base32}`.
- Deactivated offerings return friendly "no longer available" (200 + noindex), not 404.

### Visible (logged out)

- Act name, genre chips, primary photos, activity types, price line (or free-launch copy)
- **Venue area only:** `display_location` + optional map circle on jittered `public_lat/lng`
- Act owner first name + last initial, verified badge, member since
- Aggregate review stats when present
- CTA: **Sign up to request this gig**

### Never on public pages

- Act private service-area address or true act coordinates
- Owner phone, email, social links
- Unmoderated free-text descriptions (authenticated verified users only)
- Full calendar detail (tier label at most)

**Exact venue address disclosure:** only after gig `approved` (or active promoter connection where product allows), per anti-abuse doc.

### Open Graph

SSR on public routes (`generateMetadata`):

```
og:title        "{Act name} — {activity} in {display_location} | StageConnect"
og:description  "Book verified live music. Every member is ID-verified."
og:image        /api/og/{slug} share card
```

### Owner share affordances

On act-owner offering management: copy link, Facebook sharer URL, share-card preview.

### Instrumentation

`?src=` query params (`share_copy`, `share_fb`) → `events` table for funnel analytics.

---

## Part 2 — Invite links (promoter / verified-friend)

### Flow

1. Verified act owner creates **Invite a promoter/booker** → scope: one act or all acts → `https://stageconnect.app/i/{token}`
2. Recipient opens landing copy: verification required for everyone.
3. Sign up / log in → KYC → token redeemed → `PROMOTER_CONNECTION` in `pending_act_owner_confirm`.
4. Owner confirms identity → `active` (guardian step if minor) → free-eligible offerings unlocked; thread opens.

### Token rules

- Default expiry 14d (cap 30d), `max_uses` default 1 (cap 10).
- Redemption requires verified booker; atomic use count.
- Rate limits per `data-model-additions.md`.

---

## Part 3 — Public act page (`/a/{slug}`)

- Shows structured act metadata and approved photos.
- Links to public offerings for that act.
- Same location privacy: no act home address; offerings show venue area only.

## Safety boundaries

See [anti-abuse.md](../safety/anti-abuse.md) — public surfaces are inbound only; messaging and payments stay on-platform after verification.
