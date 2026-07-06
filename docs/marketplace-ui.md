# Marketplace UI

Trust-first marketplace for bookers and act owners — browse offerings, request gigs, and host verified live music.

## Dev logins

After `make seed`, all email users use password `password123`:

| Email | Roles | Verification | Use for |
|-------|-------|--------------|---------|
| `booker.verified@example.com` | booker | verified | Browse, request paid gigs |
| `act_owner.verified@example.com` | act owner | verified | Approve gigs, promoter invites |
| `both.verified@example.com` | booker + act owner | verified | Dual-role flows |
| `act_owner.verified2@example.com` | act owner | verified | Many offerings, admin flag fixtures |
| `booker.unverified@example.com` | booker | unverified | Blocked booking flow |
| `act_owner.pending@example.com` | act owner | pending | Blocked hosting |
| `oauth.only@example.com` | — | unverified | OAuth only (no password) |

**Admin login** (from `.env`, not seed):

| Email | Password | After login |
|-------|----------|-------------|
| `ADMIN_EMAIL` (default `admin@example.com`) | `ADMIN_PASSWORD` | `/admin` |

**Bulk accounts** (`bulk.booker.*`, `bulk.act_owner.*`, `bulk.both.*`) populate admin pagination — see [admin-ui.md](admin-ui.md). Password: `password123`.

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Landing + featured offerings |
| `/login`, `/register` | Auth |
| `/dashboard` | Role-aware hub |
| `/calendar` | Schedule + open slots + weather |
| `/offerings` | Browse offerings |
| `/offerings/[id]` | Detail + request gig |
| `/a/[slug]` | Public offering/act page |
| `/i/[token]` | Invite redemption landing |
| `/booker/gigs` | Booker gig requests |
| `/act-owner/acts` | Act CRUD |
| `/act-owner/offerings` | Offering CRUD + slots |
| `/act-owner/gigs` | Owner gig inbox |
| `/act-owner/promoters` | Promoter connections |

## Verification gates

- Auth ≠ verification — OAuth does not satisfy KYC.
- Unverified users cannot create offerings, send gig requests, or redeem invites.
- Minors require verified guardian linkage.
- UI shows explicit blocked states with next steps.

## Gig flow (summary)

1. Verified booker opens offering → request (slot or inquiry).
2. Paid path may await payment when enabled; promoter-only requires active connection.
3. Owner approves, declines, counter-offers, or cancels — see [gig-lifecycle-spec.md](specs/gig-lifecycle-spec.md).
4. Payments stay on-platform when `PAYMENTS_ENABLED=true`.

## Promoter invites

1. Verified act owner invites by email or share link.
2. Invitee verifies → owner confirms → connection active.
3. Unlocks promoter-only (free) offerings between the pair.

## Related docs

- [Design system](design-system.md)
- [Admin UI](admin-ui.md)
- [Data model](data-model.md)
- [OAuth design](oauth-design.md)
- `.cursor/rules/stageconnect-mvp.mdc`
