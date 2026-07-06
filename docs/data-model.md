# StageConnect data model

Trust-first gig marketplace schema (PostgreSQL). The diagram below matches the SQLAlchemy models in `backend/app/models/`.

```mermaid
erDiagram
    USER ||--o{ OAUTH_ACCOUNT : links
    USER ||--o{ ACT : owns
    USER ||--o{ OFFERING : creates
    USER ||--o{ INVITE_TOKEN : creates
    USER ||--o{ PROMOTER_CONNECTION : invites_as_owner
    USER ||--o{ PROMOTER_CONNECTION : joins_as_booker
    USER ||--o{ GIG_REQUEST : requests_as_booker
    USER ||--o{ GIG_REQUEST : hosts_as_act_owner
    USER ||--o{ VERIFICATION_RECORD : has
    USER ||--o{ PLATFORM_FLAG : flagged
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ MESSAGE : sends
    USER ||--o{ REVIEW : writes
    USER ||--o{ REVIEW : receives
    USER ||--o{ ADMIN_AUDIT_LOG : performs
    USER }o--o| USER : guardian_of

    GENRE ||--o{ ACT : classifies

    ACT ||--o{ OFFERING : featured_in
    ACT ||--o{ INVITE_TOKEN : scoped_to

    OFFERING ||--o{ OFFERING_PHOTO : has
    OFFERING ||--o{ OFFERING_AVAILABILITY_SLOT : has
    OFFERING ||--o{ GIG_REQUEST : generates

    INVITE_TOKEN ||--o{ PROMOTER_CONNECTION : redeems_into

    GIG_REQUEST ||--o| PAYMENT_TRANSACTION : may_have
    GIG_REQUEST ||--o| THREAD : has
    PROMOTER_CONNECTION ||--o| THREAD : has
    THREAD ||--o{ MESSAGE : contains
    GIG_REQUEST ||--o{ REVIEW : generates

    USER {
        uuid id PK
        string email UK
        string password_hash "nullable for OAuth-only"
        bool is_booker
        bool is_act_owner
        bool is_act_manager
        bool is_booking_coordinator
        bool manager_verified
        smallint booker_experience_level "nullable 1-5"
        bool is_admin
        enum verification_status
        bool is_minor
        uuid guardian_user_id FK
        string phone
        string first_name
        string last_name
        string profile_photo_storage_key
        datetime created_at
    }

    OAUTH_ACCOUNT {
        uuid id PK
        uuid user_id FK
        enum provider "google|facebook"
        string provider_user_id
        string provider_email
        bool provider_email_verified
        datetime created_at
    }

    VERIFICATION_RECORD {
        uuid id PK
        uuid user_id FK
        uuid actor_id FK
        string previous_status
        string new_status
        text note
        datetime created_at
    }

    GENRE {
        uuid id PK
        string name UK
        bool active_in_ui
    }

    ACT {
        uuid id PK
        uuid act_owner_id FK
        uuid genre_id FK
        string name
        string act_type
        int years_active
        text description
        float lat "private service-area anchor"
        float lng
        string address "never on public serializers"
        json photo_urls
        json genres
        datetime created_at
    }

    OFFERING {
        uuid id PK
        uuid act_id FK
        uuid act_owner_id FK
        enum activity_type
        decimal price
        text availability
        bool promoter_only_allowed
        bool active
        string slug UK
        string display_location "public venue area label"
        float public_lat "jittered map point"
        float public_lng
        smallint min_booker_experience
        int max_venue_capacity
        bool sound_system_required
        enum equipment_provided
        bool requires_21_plus
        datetime created_at
    }

    OFFERING_PHOTO {
        uuid id PK
        uuid offering_id FK
        string storage_key
        string thumbnail_key
        int sort_order
        bool is_primary
        enum moderation_status
        datetime created_at
    }

    OFFERING_AVAILABILITY_SLOT {
        uuid id PK
        uuid offering_id FK
        datetime start_at
        datetime end_at
        enum status "open|held|booked|blocked"
        int capacity
        datetime created_at
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
        datetime created_at
    }

    PROMOTER_CONNECTION {
        uuid id PK
        uuid act_owner_id FK
        uuid booker_id FK "nullable until redemption"
        uuid invite_token_id FK
        string invitee_email
        enum status
        datetime invited_at
        datetime accepted_at
        datetime owner_confirmed_at
        datetime guardian_approved_at
        datetime created_at
    }

    GIG_REQUEST {
        uuid id PK
        uuid offering_id FK
        uuid booker_id FK
        uuid act_owner_id FK
        uuid promoter_connection_id FK "nullable; required for free gigs"
        enum payment_type "paid|free"
        enum status
        datetime scheduled_at
        uuid availability_slot_id FK
        text note
        decimal counter_offer_price
        datetime counter_offer_scheduled_at
        text counter_offer_note
        json confirmed_snapshot
        datetime requested_at
    }

    PAYMENT_TRANSACTION {
        uuid id PK
        uuid gig_request_id FK
        uuid booker_id FK
        enum direction
        decimal amount
        string stripe_payment_intent_id
        datetime created_at
    }

    THREAD {
        uuid id PK
        uuid gig_request_id FK "nullable"
        uuid promoter_connection_id FK "nullable"
        datetime created_at
    }

    MESSAGE {
        uuid id PK
        uuid thread_id FK
        uuid sender_id FK
        text body
        datetime sent_at
    }

    REVIEW {
        uuid id PK
        uuid gig_request_id FK
        uuid reviewer_id FK
        uuid reviewee_id FK
        int rating
        text body
        enum moderation_status
        bool is_friend_ride
        smallint observed_booker_experience
        datetime published_at
        datetime created_at
    }

    PLATFORM_FLAG {
        uuid id PK
        uuid user_id FK
        enum flag_type
        json details
        datetime created_at
        datetime resolved_at
    }

    NOTIFICATION {
        uuid id PK
        uuid user_id FK
        string kind
        text body
        json payload
        datetime read_at
        datetime created_at
    }

    ADMIN_AUDIT_LOG {
        uuid id PK
        uuid actor_id FK
        enum action
        uuid target_user_id FK
        json metadata
        datetime created_at
    }

    EVENT {
        uuid id PK
        string event_type
        uuid user_id FK
        string src
        string offering_slug
        string invite_token
        json payload
        datetime created_at
    }
```

## Location privacy (core domain rule)

| Surface | Act (`acts`) | Offering (`offerings`) |
|---------|--------------|------------------------|
| Public pages / maps | Hidden | `display_location` + jittered `public_lat/lng` only |
| Authenticated verified bookers | Still hidden until gig approved | Venue area only until confirmed |
| Confirmed gig parties | Exact act service-area address may appear in post-approval flows | Full venue details per product policy |

Act home base / rehearsal location is **private** (service area). Event **venue** is **public at approximate precision** on listing pages — distinct from the equine marketplace pattern where animal address was fully fuzzed.

## Related documents

- [Data model additions](specs/data-model-additions.md)
- [Gig lifecycle spec](specs/gig-lifecycle-spec.md)
- [Public acts & invite links](specs/public-acts-and-invite-links-spec.md)
- [Anti-abuse](safety/anti-abuse.md)
