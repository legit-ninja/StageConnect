# Spec — Gig lifecycle (counter-offer, snapshot, cancellation)

**Status:** Implemented in `backend/app/routers/gigs.py` and `backend/app/services/gig_lifecycle.py`  
**Related:** `docs/data-model.md`, `docs/strategy/free-launch-strategy.md`

## Purpose

Define how a booker moves from browse → request → (optional payment) → act-owner decision → confirmed gig → completion or cancellation, including counter-offers and immutable confirmation snapshots.

## States (`GigStatus`)

| Status | Meaning |
|--------|---------|
| `pending_payment` | Paid offering with slot selected; awaiting deposit/checkout when payments enabled |
| `pending_act_owner` | Awaiting act owner action (inquiry or free path) |
| `counter_offered` | Owner proposed new price/time/note; booker must accept |
| `approved` | Confirmed gig; `confirmed_snapshot` populated |
| `declined` | Owner declined |
| `cancelled` | Owner cancelled (slot released if held) |
| `completed` | Gig marked complete (reviews eligible) |

## Creation paths

1. **Slot booking** — booker selects `availability_slot_id` → `scheduled_at` from slot; status `pending_payment` (paid) or `pending_act_owner` (promoter-only/free).
2. **Inquiry** — no slot; requires `note` ≥ 10 characters; status `pending_act_owner`.

Additional rules:

- Booker cannot book own offering.
- Promoter-only offerings require active `PROMOTER_CONNECTION` (`payment_type=free`).
- Minors blocked from confirming `requires_21_plus` offerings.

## Counter-offer flow

**Actor:** act owner only, from `pending_act_owner` or `pending_payment`.

1. Owner POSTs status `counter_offer` with optional `counter_offer_price`, `counter_offer_scheduled_at`, `counter_offer_note`.
2. Defaults: price → listing price; time → current `scheduled_at`.
3. Gig → `counter_offered`.

**Acceptance:** booker POSTs status `approved` while `counter_offered` → runs `_confirm_gig`.

## Approval (no counter-offer)

**Actor:** act owner from `pending_act_owner` or `pending_payment` → status `approved` → `_confirm_gig`.

## Confirmation (`_confirm_gig`)

On approve (direct or counter-offer accept):

1. `confirmed_snapshot` = JSON from `build_confirmed_snapshot`:
   - offering id, act name, activity type, confirmed price, scheduled time, payment type, `requires_21_plus`, counter-offer note
2. `scheduled_at` ← confirmed time (counter-offer time if set)
3. Status → `approved`
4. Availability slot → `booked` if applicable
5. If payments enabled → record booker platform deposit via `record_booker_platform_deposit`
6. Event log + optional manager minor-skew flag

**Price/time resolution:** counter-offer fields override listing defaults when present (`confirmed_price`, `confirmed_scheduled_at`).

## Decline / cancel / complete

**Actor:** act owner (except counter-offer accept).

| Action | Effect |
|--------|--------|
| `declined` | Status declined; slot reopened |
| `cancelled` | Status cancelled; slot reopened |
| `completed` | Status completed (reviews unlocked per review rules) |

**Cancellation policy (config):** `CANCELLATION_CUTOFF_HOURS` (default 48) reserved for future booker-side cancellation windows; owner cancel always releases slot in current MVP.

## Messaging

Creating a gig opens a `THREAD` linked to `gig_request_id` (see threads router). No DMs outside thread parents.

## Payments interaction

When `PAYMENTS_ENABLED=false`, deposit recording is skipped but snapshot and approval flow still run so gigs are auditable.

## Frontend expectations

- Act owner inbox: show counter-offer fields and booker experience warning when `min_booker_experience` not met.
- Booker gigs list: surface `counter_offered` with accept action → `approved`.
- Display `confirmed_snapshot` on approved/completed gigs as read-only terms of record.
