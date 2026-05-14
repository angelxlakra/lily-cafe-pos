# Aesthetic Overhaul — Design Spec

**Date:** 2026-03-17
**Scope:** Full app — waiter-facing POS view + admin dashboard
**Status:** Draft

---

## Overview

A complete aesthetic overhaul of the Lily Cafe POS app. After 6 months of use the clients want a fresh look. The redesign replaces the existing coffee-brown/Quesha identity with a **Bright Artisan** direction — parchment backgrounds, deep terracotta primary, and a modern Fraunces + Plus Jakarta Sans type system.

The implementation uses a **token swap + targeted edit strategy**: the existing CSS variable architecture in `index.css` is preserved (same variable names), values are replaced, hardcoded hex values are updated in the same pass, and two CSS rule edits are made (h3 font override, h1 italic). No component `.tsx` files are expected to change.

---

## Design Direction

**Bright Artisan — Terracotta & Sand**

Airy, fresh, contemporary. Clean parchment whites, deep terracotta primary actions, warm sand borders. Evokes a sunlit artisan bakery cafe — a significant visual departure from the current dark coffee-brown palette, while staying warm and grounded.

---

## Typography

| Role | Font | Weight | Style | Notes |
|---|---|---|---|---|
| Display | Fraunces | 400 | Italic | Logo, hero moments |
| H1 Page Title | Fraunces | 400 | Italic | All page titles — `font-style: italic` added to `h1` rule |
| H2 Section Heading | Fraunces | 600 | Upright | Section headings |
| H3 Card Title | Plus Jakarta Sans | 600 | Upright | `h3 { font-family: var(--font-sans) }` rule added to override global h1–h3 block |
| Body | Plus Jakarta Sans | 400 | Upright | All body text |
| Eyebrow / Label | Plus Jakarta Sans | 600 | Upright | Uppercase, 0.18em tracking |
| Caption / Muted | Plus Jakarta Sans | 400 | Upright | Timestamps, secondary info |
| Button | Plus Jakarta Sans | 600 | Upright | All button text |

**Replaces:** Quesha (heading) + Inter (body)

**Delivery:** Google Fonts CDN via `@import` in `index.css`. The `<link rel="preconnect">` tags are **required** in `frontend/index.html` for first-paint performance on the waiter-facing view.

```css
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,600;1,9..144,400;1,9..144,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
```

Note: `0,9..144,400` (upright regular) is included so h1/h2 have a non-synthesised upright fallback if `font-style: italic` is ever removed. `1,9..144,400` (italic regular) is the primary h1 variant.

The existing `@font-face` block for Quesha is removed. The file `frontend/public/fonts/Quesha.ttf` is removed.

---

## Color System

### Light Mode

| Token (CSS var) | Value | Role |
|---|---|---|
| `--color-coffee-brown` | `#c04e30` | Primary actions, active states, eyebrow text |
| `--color-coffee-dark` | `#b5462a` | Primary hover, page title text |
| `--color-coffee-light` | `#e8906a` | Tinted surfaces, light accents |
| `--color-cream` | `#fdeee4` | Chip fill, interactive surface backgrounds |
| `--color-off-white` | `#fffaf6` | Card / panel surface background |
| `--color-lily-green` | `#3d7a50` | Success, served status |
| `--color-lily-green-light` | `#5a9a6e` | Success hover states |
| `--color-neutral-text-dark` | `#1e1208` | Headings, high-emphasis text |
| `--color-neutral-text-body` | `#5a3e28` | Body text |
| `--color-neutral-text-light` | `#6e5240` | Secondary text (between body and muted) |
| `--color-neutral-text-muted` | `#7a6258` | Captions, timestamps (rosewood — user-selected) |
| `--color-neutral-border` | `#e8d0c0` | Card borders, dividers, input borders |
| `--color-neutral-background` | `#fdf7f2` | Root page background |
| `--font-sans` | `'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif` | Body font stack |
| `--font-heading` | `'Fraunces', Georgia, serif` | Heading font stack |

Functional colors (`--color-success`, `--color-error`, `--color-warning`, `--color-info`) are **unchanged** in both light and dark mode.

### Dark Mode

| Token (CSS var) | Value | Notes |
|---|---|---|
| `--color-coffee-brown` | `#e07050` | Primary actions (lightened for dark bg) |
| `--color-coffee-dark` | `#f08060` | Primary hover |
| `--color-coffee-light` | `#a05040` | Muted accent surfaces |
| `--color-cream` | `#2a1c10` | Elevated chip/interactive surface |
| `--color-off-white` | `#241810` | Card surface (slightly darker than cream) |
| `--color-lily-green` | `#5a9a6e` | Success (brightened for dark bg) |
| `--color-lily-green-light` | `#7ab88a` | Success hover |
| `--color-neutral-text-dark` | `#f5ede4` | High-emphasis text |
| `--color-neutral-text-body` | `#c8a888` | Body text |
| `--color-neutral-text-light` | `#b08870` | Secondary text |
| `--color-neutral-text-muted` | `#b89070` | Captions — lightened to achieve ≥4.5:1 on `#1a1008` |
| `--color-neutral-border` | `#3d2a1e` | Borders, dividers |
| `--color-neutral-background` | `#1a1008` | Root background |

Dark mode functional color overrides (`--color-success: #66BB6A`, `--color-error: #EF5350`, `--color-warning: #FFA726`, `--color-info: #42A5F5`) are **preserved exactly** from the current `.dark` block.

---

## Component Mapping

All components continue to use the existing utility classes. Visual change flows through via CSS token replacement and hardcoded value updates in `index.css`.

| Utility Class | Light Mode Result | Notes |
|---|---|---|
| `btn-primary` | Terracotta `#c04e30` fill, white text | Hover deep stop updated (see Hardcoded Audit) |
| `btn-secondary` | Warm surface fill, terracotta border/text | Hover rgba updated |
| `btn-success` | Forest green `#3d7a50` fill | btn-success hardcoded hex replaced with token-aligned values |
| `btn-destructive` | Pale red fill, dark red text | Functional colours unchanged |
| `btn-ghost` | Transparent, rosewood `#7a6258` text | Muted text token updated |
| `btn-outline` | Transparent, terracotta text, white-tinted border | Token-driven, no hardcoded fix needed |
| `card` | Surface `#fffaf6`, sand border | Border uses `neutral-border` token |
| `chip` | `#fdeee4` fill, sand border | Active chip uses primary token |
| `chip.active` | Terracotta fill, white text | |
| `badge-*` | Semantic colours unchanged | |
| `input-field` | `#fdf7f2` fill, sand border, terracotta focus ring | Focus bg hardcoded `#FFFFFF` updated; focus shadow rgba updated |
| `surface-glass` | Parchment-tinted glass surface | Fully hardcoded — updated explicitly (see Hardcoded Audit) |
| `bg-gradient-primary` | `#c04e30` → `#b5462a` gradient | Token-driven |
| `bg-gradient-primary` (dark) | `#2a1c10` → `#1a1008` gradient | Hardcoded dark override updated |
| `sticky-category-header` (dark) | New dark bg values | Hardcoded — updated explicitly |

---

## Hardcoded Colour Audit

The following hardcoded values in `index.css` must be updated in the same implementation pass as the token swap. These will not change automatically.

### Utility classes (light mode)

| Location | Current Value | Replacement |
|---|---|---|
| `btn-primary` hover deep stop | `#35261c` | `#8a2e18` (deep terracotta) |
| `btn-secondary` hover bg | `rgba(245, 230, 211, 0.9)` | `rgba(253, 238, 228, 0.9)` |
| `btn-success` gradient stops | `#8b9d83`, `#6f8365`, `#54614f` | `#3d7a50`, `#2e6040`, `#1e4830` |
| `btn-success` box-shadow | `rgba(80, 110, 90, 0.45)` | `rgba(61, 122, 80, 0.45)` |
| `@utility chip` hover shadow | `rgba(44, 36, 32, 0.08)` | `rgba(30, 18, 8, 0.08)` |
| `chip.active` box-shadow | `rgba(111, 78, 55, 0.3)` | `rgba(192, 78, 48, 0.3)` |
| `input-field` focus bg | `#FFFFFF` | `#fffaf6` |
| `input-field` focus shadow layer 1 | `rgba(111, 78, 55, 0.08)` | `rgba(192, 78, 48, 0.08)` |
| `input-field` focus shadow layer 2 | `rgba(44, 36, 32, 0.06)` | `rgba(30, 18, 8, 0.06)` |
| `surface-glass` bg | `rgba(250, 248, 245, 0.85)` | `rgba(255, 250, 246, 0.85)` |
| `surface-glass` border | `rgba(212, 196, 176, 0.3)` | `rgba(232, 208, 192, 0.3)` |
| `surface-glass` shadow | `rgba(44, 36, 32, 0.08)` | `rgba(30, 18, 8, 0.08)` |
| `@utility card` shadow | `rgba(44, 36, 32, ...)` | `rgba(30, 18, 8, ...)` (all occurrences) |
| `@utility card-hover` shadow | `rgba(44, 36, 32, ...)` | `rgba(30, 18, 8, ...)` (all occurrences) |
| `@utility card-interactive` shadow | `rgba(44, 36, 32, ...)` | `rgba(30, 18, 8, ...)` (all occurrences) |
| `@utility shadow-soft` | `rgba(44, 36, 32, ...)` | `rgba(30, 18, 8, ...)` (all occurrences) |
| `@utility shadow-medium` | `rgba(44, 36, 32, ...)` | `rgba(30, 18, 8, ...)` (all occurrences) |
| `@utility shadow-strong` | `rgba(44, 36, 32, ...)` | `rgba(30, 18, 8, ...)` (all occurrences) |
| `@utility sticky-category-header` light shadow | `rgba(44, 36, 32, 0.1)` | `rgba(30, 18, 8, 0.1)` |
| `@utility btn` base hover shadow | `rgba(79, 50, 35, 0.45)` | `rgba(192, 78, 48, 0.45)` |
| `@utility btn` base active shadow | `rgba(79, 50, 35, 0.4)` | `rgba(192, 78, 48, 0.4)` |
| `btn-primary` base shadow | `rgba(79, 50, 35, 0.6)` | `rgba(192, 78, 48, 0.6)` |
| Scrollbar light mode | `rgba(111, 78, 55, ...)` | `rgba(192, 78, 48, ...)` |

### Dark mode override block (lines 82–203 of index.css)

These `!important` rules are not driven by CSS tokens and must be updated explicitly.

| Selector | Property | Current Value | Replacement |
|---|---|---|---|
| `.dark .bg-coffee-brown` | `background-color` | `#2A2419` | `#2a1c10` |
| `.dark .bg-coffee-dark` | `background-color` | `#1C1812` | `#1a1008` |
| `.dark .bg-cream` | `background-color` | `#3A3128` | `#2a1c10` |
| `.dark header.bg-gradient-primary *` etc. | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark .bg-coffee-dark *` | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark header .text-cream` etc. | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark .bg-white` | `background-color` | `#2A2419` | `#2a1c10` |
| `.dark .bg-off-white .text-neutral-text-light` etc. | `color` | `#C5B8A8` | `#b08870` |
| `.dark .bg-off-white .text-neutral-text-dark` etc. | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark input[type="text"]::placeholder` | `color` | `#9B8977` | `#b89070` |
| `.dark .bg-cream button` | `background-color` | `rgba(184,145,106,0.15)` | `rgba(224,112,80,0.15)` |
| `.dark .bg-cream button` | `border-color` | `rgba(184,145,106,0.3)` | `rgba(224,112,80,0.3)` |
| `.dark .bg-cream button:not(:disabled):hover` | `background-color` | `rgba(184,145,106,0.25)` | `rgba(224,112,80,0.25)` |
| `.dark .bg-cream button` | `color` | `#B8916A` | `#e07050` |
| `.dark .bg-gradient-primary *` | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark nav .bg-gradient-primary *` | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark button.bg-gradient-primary *` | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark nav .bg-cream` | `background-color` | `#F5F0E8` | `#f5ede4` |
| `.dark input.input-field` etc. | `background-color` | `#3A3128` | `#2a1c10` |
| `.dark input.input-field` etc. | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark input.input-field` etc. | `border-color` | `#4A4034` | `#3d2a1e` |
| `.dark input::placeholder` | `color` | `#9B8977` | `#b89070` |
| `.dark .chip` | `background-color` | `#3A3128` | `#2a1c10` |
| `.dark .chip` | `color` | `#F5F0E8` | `#f5ede4` |
| `.dark .chip` | `border-color` | `#4A4034` | `#3d2a1e` |
| `.dark .chip.active` | `background-color` | `#B8916A` | `#e07050` |
| `.dark .chip.active` | `color` | `#1C1812` | `#1a1008` |
| `.dark .chip.active` | `border-color` | `#B8916A` | `#e07050` |
| `.dark .card` | `border` | `rgba(184,145,106,0.15)` | `rgba(224,112,80,0.15)` |
| `.dark .bg-gradient-primary` | gradient stops | `#2A2419` / `#1C1812` | `#2a1c10` / `#1a1008` |
| Scrollbar dark mode | `scrollbar-color` etc. | `rgba(184, 145, 106, ...)` | `rgba(224, 112, 80, ...)` |
| `.dark .sticky-category-header` | `background-color` | `#2A2419` | `#2a1c10` |
| `.dark .sticky-category-header` | `border-bottom-color` | `#1C1812` | `#1a1008` |

### Known intentional survivors (grep allow-list)

After all replacements above, the following hardcoded values are expected to remain and are intentionally not changed:

| Value | Location | Reason |
|---|---|---|
| `#f6f1ea` | `btn-success` text color | Warm white text on green — functional, palette-agnostic |
| `#c0392b`, `#a93226` | `btn-destructive` text | Functional error reds — unchanged per spec |
| `rgba(255, 255, 255, 0.1)` | `btn-ghost` hover bg | White transparency — palette-agnostic |
| `rgba(255, 252, 247, 0.15)` | `btn-outline` hover bg | Warm white transparency — palette-agnostic |
| `rgba(244, 67, 54, ...)` | `btn-destructive` bg and border | Functional error colour — unchanged per spec |
| `rgba(255, 255, 255, 0.65)` | `btn-outline` base border | Pure white transparency — palette-agnostic |
| `rgba(255, 255, 255, 0.9)` | `btn-outline` hover border | Pure white transparency — palette-agnostic |
| `rgba(0, 0, 0, 0.2)`, `rgba(0, 0, 0, 0.15)` | `.dark .card` box-shadow | Pure black transparencies — palette-agnostic |

---

## CSS Rule Edits

The following CSS rule changes are required in `index.css` beyond token value replacement:

1. **`h1` italic** — add `font-style: italic` to the `h1` rule block so page titles render in Fraunces italic as designed.
2. **`h2` weight** — add `font-weight: 600` to the `h2` rule block. The existing `h1, h2, h3` shared block does not set font-weight; without an explicit override `h2` would render at Fraunces weight 400 (too light for section headings).
3. **`h3` sans-serif** — add `h3 { font-family: var(--font-sans); }` after the global `h1, h2, h3` block so card titles use Plus Jakarta Sans rather than Fraunces.
4. **`btn` font-weight** — update `font-weight: 500` to `font-weight: 600` in the `@utility btn` base. The Typography table specifies button text at Plus Jakarta Sans 600. The h1 upright fallback (weight 400 is in the font URL) is intentionally available but renders at that weight only if `font-style: italic` is later removed from `h1` — no additional rule change needed for that case.

---

## Files Changed

| File | Change |
|---|---|
| `frontend/src/index.css` | Font `@import`, Quesha `@font-face` removed, `@theme` token values, dark mode `.dark` block, all hardcoded hex audit items, `h1` italic rule, `h3` font-family override |
| `frontend/index.html` | Add `<link rel="preconnect" href="https://fonts.googleapis.com">` and `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` |
| `frontend/public/fonts/Quesha.ttf` | Delete |

No backend files change. No `.tsx` component files expected to change.

---

## Design Notes

**`--color-off-white` vs `--color-cream` elevation:** In light mode, `--color-off-white` (`#fffaf6`) is lighter than `--color-cream` (`#fdeee4`) — off-white is the cleaner card surface, cream is the warmer interactive/chip surface. In dark mode the roles invert: `--color-off-white` (`#241810`) is darker than `--color-cream` (`#2a1c10`). This inversion is intentional — in dark mode the elevated surface is the warmer, lighter one. Implementors should not attempt to normalise this.

**`font-display: swap`:** The Google Fonts `@import` URL includes `&display=swap`, which preserves the existing `font-display: swap` behaviour from the Quesha `@font-face` block being removed. No additional `font-display` setting is needed.

---

## Out of Scope

- Layout changes (covered by the 2026-03-13 admin dashboard redesign spec)
- New components or page restructuring
- Print / receipt styling
- Any backend API changes
