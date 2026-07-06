# Admin UI

Trust-first operations console for StageConnect moderators.

## Access

1. Set admin credentials in `.env`:
   ```
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=change-me-admin
   ```
2. Sign in at http://localhost:3000/login
3. Navigate to http://localhost:3000/admin

Use `act_owner.pending@example.com` (password `password123`) for verification queue testing after `make seed`.

**Bulk preview accounts** (~50 users):

| Pattern | Count |
|---------|-------|
| `bulk.booker.{01-25}@example.com` | 25 |
| `bulk.act_owner.{01-15}@example.com` | 15 |
| `bulk.both.{01-10}@example.com` | 10 |

Password: `password123`. Expect 60+ users on `/admin/users`.

## Routes

| Route | Purpose |
|-------|---------|
| `/admin` | Dashboard — verification queue, inactive offerings, signups |
| `/admin/users` | Search accounts |
| `/admin/users/[id]` | Detail — verification, roles, guardian, counts |
| `/admin/users/[id]?review=1` | Focused verification workflow |
| `/admin/verification` | Queue |
| `/admin/offerings` | Activate/deactivate offerings |
| `/admin/audit` | Admin action history |
| `/admin/flags` | Platform pattern flags |
| `/admin/bookings` | Gig oversight (placeholder / partial) |
| `/admin/reports` | Reports queue (placeholder) |

## Verification workflow

1. Open **Verification** (badge shows queue count).
2. **Review** user → check OAuth vs KYC, minor/guardian, marketplace activity.
3. Approve, pending, or reject (reject confirms); actions audit-logged.

## Trust rules in UI

- OAuth sign-in never implies gig eligibility.
- No copy encouraging off-platform payment or contact.
- Destructive actions require confirmation.

## Related docs

- [Design system](design-system.md)
- [OAuth design](oauth-design.md)
- [Data model](data-model.md)
- `.cursor/rules/stageconnect-mvp.mdc`
