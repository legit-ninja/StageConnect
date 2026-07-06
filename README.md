# StageConnect

Trust-first gig marketplace connecting bookers with verified acts and act owners for live music experiences.

## Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, Alembic
- **Frontend:** Next.js, TypeScript

## Local development

### Quick start (recommended)

```bash
cp .env.example .env
make up          # docker-compose up -d --no-recreate
make doctor      # verify API + web health
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

### If `docker-compose up` fails with "permission denied"

This machine uses **snap Docker**, which can block stopping containers. Symptoms:

```
Error response from daemon: cannot stop container: ... permission denied
```

**Full reset** (run in your terminal):

```bash
sudo snap restart docker
sleep 3
cd stageconnect
docker-compose down
docker-compose up --build -d
```

Or print the same steps: `make reset-docker`

**Workaround without resetting Docker** — run API in Docker, frontend on the host:

```bash
make dev-split
cd frontend && npm run dev
```

Use `docker-compose up -d --no-recreate` (via `make up`) instead of plain `docker-compose up` when containers are already running.

### Default admin login (dev)

Set in `.env`:

```
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-me-admin
```

Sign in at http://localhost:3000/login

### Dev seed data

After migrations, load sample users, acts, and offerings:

```bash
make up    # start db (+ api/web) if not already running
make migrate
make seed
```

If the `api` container cannot reach `db` (common with snap Docker), `make migrate` and `make seed` automatically fall back to the host using `localhost:5432` while the `db` container is running.

**If login fails with "Is the API running?"** — the API may be down. Start it on the host:

```bash
make dev-api    # terminal 1 — API at http://localhost:8000
```

Ensure `db` is running (`make up` or `docker-compose up -d db`). The Docker `api` service often cannot reach `db` on snap Docker; `make dev-api` avoids that.

All seeded email/password users use password `password123`. See [marketplace-ui.md](docs/marketplace-ui.md) for the full persona login table (bookers, act owners, dual-role, and gig scenarios).

**Bulk admin-preview accounts** (`bulk.booker.*`, `bulk.act_owner.*`, `bulk.both.*`) also use `password123` — see [admin-ui.md](docs/admin-ui.md). These populate `/admin/users` pagination and act owner act counts; they are not persona walkthrough accounts.

| Email | Role | Verification |
|-------|------|--------------|
| `both.verified@example.com` | booker + act owner | verified |
| `act_owner.verified@example.com` | act owner | verified |
| `booker.verified@example.com` | booker | verified |
| `act_owner.verified2@example.com` | act owner | verified (many offerings) |
| `booker.unverified@example.com` | booker | unverified (blocked) |
| `act_owner.pending@example.com` | act owner | pending (blocked from hosting) |

OAuth-only dev user: `oauth.only@example.com` (no password; remains unverified).

Set `SEED_DEV_DATA=true` or `ENVIRONMENT=development` in `.env` for the seed script to run.

### Environment variables

| Template | Copy to | Used by |
|----------|---------|---------|
| `.env.example` | `.env` | Backend / Docker |
| `frontend/.env.local.example` | `frontend/.env.local` | Next.js (host dev) |

**Never commit** `.env` or `.env.local`.

## License

Copyright © 2026 Sound Strategy Management. All rights reserved.

See [LICENSE](LICENSE).

## Documentation

- [Data model](docs/data-model.md)
- [Design system](docs/design-system.md) — tokens, themes, spacing
- [Public acts & invite links spec](docs/specs/public-acts-and-invite-links-spec.md)
- [Data model additions](docs/specs/data-model-additions.md)
- [Admin UI](docs/admin-ui.md)
- [Marketplace UI](docs/marketplace-ui.md)
