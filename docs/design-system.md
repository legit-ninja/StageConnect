# StageConnect design system

Semantic tokens, theme modes, and visual conventions for the StageConnect frontend.

## Stack

- Next.js App Router + TypeScript
- CSS modules (`admin.module.css`, `marketplace.module.css`, `auth.module.css`)
- Shared utilities in `frontend/app/utilities.css`
- **No Tailwind / shadcn** — colors via CSS custom properties in `frontend/app/globals.css`

## Theme modes

| Preference | `data-theme` on `<html>` | Behavior |
|------------|--------------------------|----------|
| Light | `light` | Warm studio palette |
| Dark | `dark` | Default — deep background, gold accent |
| System | `light` or `dark` | Follows OS `prefers-color-scheme` |
| High contrast | `high-contrast` | Accessibility mode |

Toggle: site header theme control. Persistence: `localStorage` key `stageconnect-theme`. Inline script in `app/layout.tsx` prevents FOUC.

## Token reference

Hex values live only in [`frontend/app/globals.css`](../frontend/app/globals.css). Use `var(--token-name)` in modules.

### Color (dark-first defaults)

| Token | Purpose |
|-------|---------|
| `--background` / `--foreground` | Page surface and text |
| `--muted` / `--muted-foreground` | Subtle backgrounds |
| `--primary` / `--primary-hover` | Gold accent CTAs |
| `--destructive` | Danger actions |
| `--success-*`, `--warning-*`, `--info-*`, `--error-*` | Status badges |
| `--card` / `--card-border` | Cards and panels |

### Spacing & typography

| Token | Value |
|-------|-------|
| `--space-1` … `--space-6` | 4–32 px |
| `--content-max-admin` | 1200 px |
| `--content-max-marketplace` | 960 px |
| `--font-sans` / `--font-heading` | Loaded via `next/font/google` in layout |

## Module boundaries

| Module | Used by |
|--------|---------|
| `globals.css` | Tokens only |
| `admin.module.css` | `/admin/*` |
| `marketplace.module.css` | Marketplace routes |
| `auth.module.css` | Login / register |

Share **tokens**, not cross-import admin/marketplace components.

## Manual test matrix

Run `make dev-api` + `cd frontend && npm run dev`. Spot-check `/login`, `/`, `/dashboard`, `/offerings`, `/act-owner/*`, `/admin/*` in all four theme preferences: persistence, focus rings, badge contrast.

## Related

- [Marketplace UI](marketplace-ui.md)
- [Admin UI](admin-ui.md)
- `.cursor/rules/stageconnect-mvp.mdc`
