# Liability and legal (live music / gigs)

## Context

Live events carry injury, property, noise, and alcohol-related risks. Marketplace operators typically need waivers, clear terms, and insurance disclosures. **This document is not legal advice** — require qualified counsel before public launch.

## Legal gate (launch blocker)

Prerequisites before public signup:

1. Counsel review of applicable venue liability and facilitator status for your launch state(s).
2. Lawyer-reviewed booker and act-owner waiver templates in pre-booking acknowledgment (guardian co-sign for minors).
3. Terms of service and privacy policy (verification records + audit logs retention).
4. Stripe Connect marketplace terms cleared before enabling `PAYMENTS_ENABLED`.

**Free launch:** zero-fee period does not relax waivers, guardian flows, or ToS (see [free-launch-strategy.md](../strategy/free-launch-strategy.md)).

## Working directions (pending legal review)

| Topic | Direction |
|-------|-----------|
| User waivers | Accept platform terms + activity waivers before first confirmed gig |
| Act owner insurance | Consider proof of liability coverage before listing (TBD) |
| Minors | Guardian linkage + co-signature on waivers |
| Platform role | Marketplace facilitator, not employer of acts or operator of venues |
| Public pages | Venue area approximate on public surfaces; private act base and exact venue details only to confirmed parties |

## MVP minimum

- Published ToS and privacy policy before public signup.
- In-app risk acknowledgment before booking confirmation.
- Admin ability to deactivate offerings and users violating safety policies.

## Related documents

- [Anti-abuse](anti-abuse.md)
- [Free launch strategy](../strategy/free-launch-strategy.md)
