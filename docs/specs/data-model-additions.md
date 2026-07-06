# Data model additions — public offerings, invites, threads, reviews

Companion to [data-model.md](../data-model.md). Documents entities and constraints beyond the base sketch; aligns with Alembic migrations in `backend/alembic/versions/`.

```mermaid
erDiagram
    USER ||--o{ INVITE_TOKEN : creates
    USER ||--o{ REVIEW : writes
    USER ||--o{ REVIEW : receives
    USER ||--o{ MESSAGE : sends

    ACT ||--o{ INVITE_TOKEN : scoped_to
    OFFERING ||--o{ OFFERING_PHOTO : has

    INVITE_TOKEN ||--o{ PROMOTER_CONNECTION : redeems_into

    GIG_REQUEST ||--o| THREAD : has
    PROMOTER_CONNECTION ||--o| THREAD : has
    THREAD ||--o{ MESSAGE : contains

    GIG_REQUEST ||--o{ REVIEW : generates

    OFFERING {
        uuid id PK
        string slug UK "kebab-act + base32; public URL id"
        string display_location "public venue label"
        float public_lat "jittered >= ~5km from true venue anchor"
        float public_lng
        smallint min_booker_experience
        int max_venue_capacity
        bool sound_system_required
        enum equipment_provided
        bool requires_21_plus
        bool promoter_only_allowed
    }

    ACT {
        uuid id PK
        float lat "private service area — never public"
        float lng
        string address "never public"
    }

    OFFERING_PHOTO {
        uuid id PK
        uuid offering_id FK
        string storage_key
        int sort_order
        bool is_primary
        enum moderation_status
    }

    INVITE_TOKEN {
        uuid id PK
        uuid act_owner_id FK
        uuid act_id FK "nullable = all acts"
        string token UK
        int max_uses
        int use_count
        datetime expires_at
        datetime revoked_at
    }

    PROMOTER_CONNECTION {
        uuid id PK
        uuid act_owner_id FK
        uuid booker_id FK
        uuid invite_token_id FK
        enum status "pending_act_owner_confirm|pending_guardian|active|declined|revoked"
        datetime owner_confirmed_at
        datetime guardian_approved_at
    }

    THREAD {
        uuid id PK
        uuid gig_request_id FK
        uuid promoter_connection_id FK
    }

    MESSAGE {
        uuid id PK
        uuid thread_id FK
        uuid sender_id FK
        text body
    }

    REVIEW {
        uuid id PK
        uuid gig_request_id FK
        uuid reviewer_id FK
        uuid reviewee_id FK
        int rating
        bool is_friend_ride
        smallint observed_booker_experience
        enum moderation_status
    }

    GIG_REQUEST {
        decimal counter_offer_price
        datetime counter_offer_scheduled_at
        text counter_offer_note
        json confirmed_snapshot
    }
```

## Migration & constraint notes

### THREAD (replaces MESSAGE → GIG FK)

- Check constraint: exactly one parent — `(gig_request_id IS NULL) <> (promoter_connection_id IS NULL)`.
- Partial unique indexes: one thread per gig / per promoter connection.
- Promoter thread opens only when `PROMOTER_CONNECTION.status = active`.

### INVITE_TOKEN

- Generate with `secrets.token_urlsafe(24)`; do not log plaintext tokens.
- Atomic redemption: increment `use_count` only when under `max_uses`, not revoked, not expired.
- Rate limits: ≤10 active tokens per owner; ≤25 redemptions per owner per 30 days → admin queue.

### Public location split (StageConnect-specific)

- **Offering** public fields describe **where the gig happens** (venue area).
- **Act** coordinates describe **private service area** (home base / travel origin) and must never serialize on `/api/public/*`.
- `LOCATION_JITTER_SECRET` (or `service_area_default_secret` in config) supports deterministic jitter per entity id.

### REVIEW

- Unique `(gig_request_id, reviewer_id)`.
- Completed gigs only; promoter/free gigs flagged `is_friend_ride` on display.
- `observed_booker_experience` — owner observation of booker skill (optional).

### GIG counter-offer & snapshot

- Counter-offer columns nullable until used.
- `confirmed_snapshot` written once at approval; treat as immutable terms record for disputes.

### Platform flags

- `minor_connection_skew`, `invite_redemption_rate`, `artist_fee_request`, `deposit_scam_pattern`, `off_platform_contact`.

### Manager roles

- `is_act_manager`, `is_booking_coordinator`, `manager_verified` — delegated access; host capability remains on verified act owners.

## Related documents

- [Gig lifecycle spec](gig-lifecycle-spec.md)
- [Public acts & invite links](public-acts-and-invite-links-spec.md)
- [Anti-abuse](../safety/anti-abuse.md)
