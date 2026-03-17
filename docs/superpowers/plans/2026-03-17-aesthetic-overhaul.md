# Aesthetic Overhaul Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Lily Cafe POS coffee-brown/Quesha visual identity with the Bright Artisan Terracotta & Sand palette and Fraunces + Plus Jakarta Sans type system across both waiter POS and admin dashboard views.

**Architecture:** Token swap strategy — CSS variable names in `index.css` are preserved, only their values change. Hardcoded hex/rgba values in the same file are updated in a separate pass. Four CSS rule edits (h1 italic, h2 weight, h3 font-family, btn font-weight) complete the typography change. No `.tsx` component files are modified.

**Tech Stack:** Vite + React + TypeScript + Tailwind CSS v4. Build: `cd frontend && npm run build` (runs `tsc && vite build`). Dev server: `cd frontend && npm run dev`.

---

## Chunk 1: Font Infrastructure + Color Tokens

### Task 1: Establish build baseline

**Files:**
- Read: `frontend/src/index.css`
- Read: `frontend/index.html`

- [ ] **Step 1: Verify build passes before any changes**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0 with `✓ built in` output. If it fails, stop and investigate before proceeding.

---

### Task 2: Add Google Fonts preconnect to index.html

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add preconnect tags**

In `frontend/index.html`, add the following two lines immediately after `<meta name="viewport" ...>`:

```html
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
```

The `<head>` block should look like this after the edit:

```html
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <meta name="description" content="Lily Cafe POS System - Point of Sale for Mary's Kitchen" />
    <title>Lily Cafe POS</title>
  </head>
```

- [ ] **Step 2: Verify build still passes**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0.

---

### Task 3: Swap font setup in index.css

**Files:**
- Modify: `frontend/src/index.css` (lines 1–12)
- Delete: `frontend/public/fonts/Quesha.ttf`

- [ ] **Step 1: Replace @import and @font-face in index.css**

Replace the entire top section (lines 1–12) of `frontend/src/index.css`:

Old (exact):
```css
@import "tailwindcss";

/* Override dark mode to use class selector instead of system preference */
@custom-variant dark (&:where(.dark, .dark *));

@font-face {
  font-family: "Quesha";
  src: url("/fonts/Quesha.ttf") format("truetype");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

New:
```css
@import "tailwindcss";
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,600;1,9..144,400;1,9..144,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* Override dark mode to use class selector instead of system preference */
@custom-variant dark (&:where(.dark, .dark *));
```

- [ ] **Step 2: Delete Quesha font file**

```bash
rm /Users/angelxlakra/dev/lily-cafe-pos/frontend/public/fonts/Quesha.ttf
```

- [ ] **Step 3: Verify build still passes**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0. There should be no references to Quesha in any `.tsx` file — if the build fails mentioning Quesha, grep for it: `grep -r "Quesha" frontend/src/`.

- [ ] **Step 4: Commit**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/index.html frontend/src/index.css && git rm frontend/public/fonts/Quesha.ttf && git commit -m "chore(fonts): replace Quesha+Inter with Fraunces+Plus Jakarta Sans"
```

---

### Task 4: Update @theme color and font token values

**Files:**
- Modify: `frontend/src/index.css` (the `@theme { ... }` block, lines ~15–52)

- [ ] **Step 1: Replace the full @theme block**

Find the existing `@theme { ... }` block in `index.css` (starts with `/* Custom theme configuration for Lily Cafe */`) and replace it entirely with:

```css
/* Custom theme configuration for Lily Cafe — Terracotta & Sand */
@theme {
  /* Terracotta & Sand palette - Light Mode */
  --color-coffee-brown: #c04e30;
  --color-coffee-dark: #b5462a;
  --color-coffee-light: #e8906a;

  --color-cream: #fdeee4;
  --color-off-white: #fffaf6;

  --color-lily-green: #3d7a50;
  --color-lily-green-light: #5a9a6e;

  /* Functional colors — unchanged */
  --color-success: #4CAF50;
  --color-error: #F44336;
  --color-warning: #FF9800;
  --color-info: #2196F3;

  /* Neutral colors - Light Mode */
  --color-neutral-text-dark: #1e1208;
  --color-neutral-text-body: #5a3e28;
  --color-neutral-text-light: #6e5240;
  --color-neutral-text-muted: #7a6258;
  --color-neutral-border: #e8d0c0;
  --color-neutral-background: #fdf7f2;

  /* Custom fonts */
  --font-sans: 'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  --font-heading: 'Fraunces', 'Georgia', 'Times New Roman', serif;

  /* Custom spacing (8px grid) */
  --spacing-18: 4.5rem;
  --spacing-88: 22rem;

  /* Touch-friendly minimums (48px = 3rem) */
  --min-height-touch: 3rem;
  --min-width-touch: 3rem;
}
```

- [ ] **Step 2: Update the .dark {} token block**

Find the `/* Dark Mode Theme */` block and replace it entirely with:

```css
/* Dark Mode Theme — Terracotta & Sand */
.dark {
  /* Terracotta & Sand palette - Dark Mode */
  --color-coffee-brown: #e07050;
  --color-coffee-dark: #f08060;
  --color-coffee-light: #a05040;

  --color-cream: #2a1c10;
  --color-off-white: #241810;

  --color-lily-green: #5a9a6e;
  --color-lily-green-light: #7ab88a;

  /* Functional colors - Dark Mode (preserved exactly) */
  --color-success: #66BB6A;
  --color-error: #EF5350;
  --color-warning: #FFA726;
  --color-info: #42A5F5;

  /* Neutral colors - Dark Mode */
  --color-neutral-text-dark: #f5ede4;
  --color-neutral-text-body: #c8a888;
  --color-neutral-text-light: #b08870;
  --color-neutral-text-muted: #b89070;
  --color-neutral-border: #3d2a1e;
  --color-neutral-background: #1a1008;
}
```

- [ ] **Step 3: Verify build still passes**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0.

- [ ] **Step 4: Commit**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/index.css && git commit -m "feat(theme): swap color tokens to Terracotta & Sand palette"
```

---

## Chunk 2: Hardcoded Value Updates + CSS Rule Edits

### Task 5: CSS rule edits — typography

**Files:**
- Modify: `frontend/src/index.css` (h1/h2/h3 element rules ~lines 238–259, btn utility ~line 303)

- [ ] **Step 1: Add font-style: italic to h1**

Find the `h1 {` rule block in `index.css`. It currently reads:

```css
h1 {
  font-size: clamp(2.25rem, 2vw + 1.5rem, 3rem);
  line-height: 1.1;
}
```

Replace with:

```css
h1 {
  font-size: clamp(2.25rem, 2vw + 1.5rem, 3rem);
  line-height: 1.1;
  font-style: italic;
}
```

- [ ] **Step 2: Add font-weight: 600 to h2**

Find the `h2 {` rule block:

```css
h2 {
  font-size: clamp(1.75rem, 1.5vw + 1.1rem, 2.25rem);
  line-height: 1.2;
}
```

Replace with:

```css
h2 {
  font-size: clamp(1.75rem, 1.5vw + 1.1rem, 2.25rem);
  line-height: 1.2;
  font-weight: 600;
}
```

- [ ] **Step 3: Add h3 sans-serif override after the h1, h2, h3 shared block**

Find the line `h1,` that begins the `h1, h2, h3 {` block. After that entire block (which ends with `}`), add a new rule immediately after:

```css
h3 {
  font-family: var(--font-sans);
}
```

- [ ] **Step 4: Update btn base font-weight**

Find this exact line inside `@utility btn`:

```css
  font-weight: 500;
```

Replace with:

```css
  font-weight: 600;
```

- [ ] **Step 5: Verify build passes**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0.

- [ ] **Step 6: Commit**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/index.css && git commit -m "feat(typography): apply Fraunces italic h1, h2 weight, h3 sans, btn weight"
```

---

### Task 6: Update light-mode hardcoded values in utility classes

**Files:**
- Modify: `frontend/src/index.css` (utility class bodies)

Apply each replacement below using the Edit tool. Work through them in order — each is a unique string in the file so there is no ambiguity.

- [ ] **Step 1: btn-primary hover deep stop**

Find:
```css
      background: linear-gradient(135deg, var(--color-coffee-dark), #35261c);
```
Replace with:
```css
      background: linear-gradient(135deg, var(--color-coffee-dark), #8a2e18);
```

- [ ] **Step 2: btn-secondary hover bg**

Find:
```css
      background-color: rgba(245, 230, 211, 0.9);
```
Replace with:
```css
      background-color: rgba(253, 238, 228, 0.9);
```

- [ ] **Step 3: btn-success gradient stops and shadow**

Find:
```css
  background: linear-gradient(135deg, #8b9d83, #6f8365);
  color: #f6f1ea;
  box-shadow: 0 8px 16px -10px rgba(80, 110, 90, 0.45);

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #6f8365, #54614f);
  }
```
Replace with:
```css
  background: linear-gradient(135deg, #3d7a50, #2e6040);
  color: #f6f1ea;
  box-shadow: 0 8px 16px -10px rgba(61, 122, 80, 0.45);

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #2e6040, #1e4830);
  }
```

- [ ] **Step 4: btn base hover and active shadows**

Find:
```css
  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 10px 18px -8px rgba(79, 50, 35, 0.45);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 6px 12px -6px rgba(79, 50, 35, 0.4);
  }
```
Replace with:
```css
  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 10px 18px -8px rgba(192, 78, 48, 0.45);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 6px 12px -6px rgba(192, 78, 48, 0.4);
  }
```

- [ ] **Step 5: btn-primary base shadow**

Find:
```css
  box-shadow: 0 8px 16px -10px rgba(79, 50, 35, 0.6);
```
Replace with:
```css
  box-shadow: 0 8px 16px -10px rgba(192, 78, 48, 0.6);
```

- [ ] **Step 6: card shadows (card, card-hover, card-interactive, shadow-soft, shadow-medium, shadow-strong, sticky-category-header, surface-glass)**

These all use `rgba(44, 36, 32, ...)`. Replace every occurrence of `rgba(44, 36, 32,` with `rgba(30, 18, 8,` in `index.css`. Use a targeted search-and-replace across the file — this covers card, card-hover, card-interactive, shadow-soft, shadow-medium, shadow-strong, sticky-category-header light shadow, surface-glass shadow, and input-field focus shadow layer 2 in one pass.

Replace all using the Edit tool with `replace_all: true`:
- Find: `rgba(44, 36, 32,`
- Replace: `rgba(30, 18, 8,`

- [ ] **Step 7: chip hover shadow**

The chip hover shadow uses `rgba(44, 36, 32, 0.08)` — this is already covered by the replace-all in Step 6.

Verify it was replaced:
```bash
grep "rgba(44, 36, 32," /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 0 results.

- [ ] **Step 8: chip.active box-shadow**

Find:
```css
    box-shadow: 0 4px 12px rgba(111, 78, 55, 0.3);
```
Replace with:
```css
    box-shadow: 0 4px 12px rgba(192, 78, 48, 0.3);
```

- [ ] **Step 9: input-field focus bg and shadow layer 1**

Find:
```css
    border-color: var(--color-coffee-brown);
    background-color: #FFFFFF;
    box-shadow: 0 0 0 3px rgba(111, 78, 55, 0.08),
```
Replace with:
```css
    border-color: var(--color-coffee-brown);
    background-color: #fffaf6;
    box-shadow: 0 0 0 3px rgba(192, 78, 48, 0.08),
```

- [ ] **Step 10: surface-glass hardcoded values**

Find:
```css
  background: rgba(250, 248, 245, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(212, 196, 176, 0.3);
  box-shadow: 0 4px 20px rgba(44, 36, 32, 0.08);
```
Note: `rgba(44, 36, 32, 0.08)` in surface-glass was already replaced in Step 6. Replace the remaining two values:

Find (after Step 6):
```css
  background: rgba(250, 248, 245, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(212, 196, 176, 0.3);
  box-shadow: 0 4px 20px rgba(30, 18, 8, 0.08);
```
Replace with:
```css
  background: rgba(255, 250, 246, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(232, 208, 192, 0.3);
  box-shadow: 0 4px 20px rgba(30, 18, 8, 0.08);
```

- [ ] **Step 11: light mode scrollbar**

Replace remaining `rgba(111, 78, 55,` values (3 scrollbar rules — chip.active was handled in Step 8, input-field in Step 9):

Verify count before replacing:
```bash
grep -c "rgba(111, 78, 55," /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 3 occurrences (scrollbar-color, -webkit-scrollbar-thumb, -webkit-scrollbar-thumb:hover).

Use Edit tool with `replace_all: true`:
- Find: `rgba(111, 78, 55,`
- Replace: `rgba(192, 78, 48,`

Verify 0 remain:
```bash
grep "rgba(111, 78, 55," /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 0 results.

- [ ] **Step 12: Verify build passes**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0.

- [ ] **Step 13: Commit**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/index.css && git commit -m "feat(theme): update light-mode hardcoded colours to terracotta palette"
```

---

### Task 7: Update dark mode override block (lines 82–203)

**Files:**
- Modify: `frontend/src/index.css` (the `!important` override block)

These rules bypass the CSS token system and must be updated explicitly.

- [ ] **Step 1: Replace bg-coffee-brown/dark/cream background overrides**

Find:
```css
.dark .bg-coffee-brown {
  background-color: #2A2419 !important;
}

.dark .bg-coffee-dark {
  background-color: #1C1812 !important;
}

.dark .bg-cream {
  background-color: #3A3128 !important;
}
```
Replace with:
```css
.dark .bg-coffee-brown {
  background-color: #2a1c10 !important;
}

.dark .bg-coffee-dark {
  background-color: #1a1008 !important;
}

.dark .bg-cream {
  background-color: #2a1c10 !important;
}
```

- [ ] **Step 2: Replace all hardcoded #F5F0E8 (old dark text) with #f5ede4**

Note: `#F5F0E8` appears in `color:` properties throughout the dark override block AND in one `background-color:` property (`.dark nav .bg-cream { background-color: #F5F0E8 }` — this is an intentional near-white background for the bottom nav indicator in dark mode). The spec maps both to `#f5ede4`. The blanket replace-all is correct.

Verify count first:
```bash
grep -c "#F5F0E8" /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 9 occurrences.

Use Edit tool with `replace_all: true`:
- Find: `#F5F0E8`
- Replace: `#f5ede4`

After replace, verify 0 remain:
```bash
grep "#F5F0E8" /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 0 results.

- [ ] **Step 3: Replace .dark .bg-white background**

Find:
```css
.dark .bg-white {
  background-color: #2A2419 !important;
}
```
Replace with:
```css
.dark .bg-white {
  background-color: #2a1c10 !important;
}
```

- [ ] **Step 4: Replace .dark text overrides for bg-off-white and bg-white**

Find:
```css
.dark .bg-off-white .text-neutral-text-light,
.dark .bg-white .text-neutral-text-light {
  color: #C5B8A8 !important;
}
```
Replace with:
```css
.dark .bg-off-white .text-neutral-text-light,
.dark .bg-white .text-neutral-text-light {
  color: #b08870 !important;
}
```

- [ ] **Step 5: Replace .dark .bg-coffee-dark background (second occurrence)**

After Step 1 the first occurrence of `#2A2419` is replaced. The block at lines 102–105 contains a duplicate for `.dark .bg-coffee-dark`. Check it was caught by Step 1 — both selectors appear in the same find/replace block. If a `#2A2419` still exists outside Step 1's block:

```bash
grep "#2A2419" /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
If any results appear, replace them with `#2a1c10` using a targeted Edit.

- [ ] **Step 6: Replace all remaining old dark bg values #1C1812 and #3A3128**

```bash
grep -E "#1C1812|#3A3128|#4A4034|#9B8977|#B8916A|#C5B8A8" /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```

For each match found, apply the replacement per the dark mode audit table:
- `#1C1812` → `#1a1008`
- `#3A3128` → `#2a1c10`
- `#4A4034` → `#3d2a1e`
- `#9B8977` → `#b89070`
- `#B8916A` → `#e07050`
- `#C5B8A8` → already replaced in Step 4

Use `replace_all: true` on the Edit tool for each.

After all replacements, verify the above values are gone:
```bash
grep -E "#1C1812|#3A3128|#4A4034|#9B8977|#B8916A" /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 0 results.

- [ ] **Step 7: Replace dark mode rgba tints (old coffee brown)**

Find all `rgba(184, 145, 106,` and replace with `rgba(224, 112, 80,`:

```bash
grep -c "rgba(184, 145, 106," /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 5 occurrences (bg-cream button, button hover, card border, dark scrollbar × 2).

Use Edit tool with `replace_all: true`:
- Find: `rgba(184, 145, 106,`
- Replace: `rgba(224, 112, 80,`

Verify:
```bash
grep "rgba(184, 145, 106," /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected: 0 results.

- [ ] **Step 8: Update .dark .bg-gradient-primary gradient stops**

`#2A2419` and `#1C1812` should already be replaced by Steps 1 and 6. Verify:
```bash
grep -A2 "dark .bg-gradient-primary {" /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected to show `#2a1c10` and `#1a1008`. If not, apply this replacement:

Find:
```css
.dark .bg-gradient-primary {
  background: linear-gradient(135deg, #2A2419 0%, #1C1812 100%);
}
```
Replace with:
```css
.dark .bg-gradient-primary {
  background: linear-gradient(135deg, #2a1c10 0%, #1a1008 100%);
}
```

- [ ] **Step 9: Update .dark .sticky-category-header**

Verify `#2A2419` / `#1C1812` are already replaced by Steps 1 and 6:
```bash
grep -A4 "dark .sticky-category-header" /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```
Expected to show `#2a1c10` and `#1a1008`. If not, apply these replacements:

Find:
```css
.dark .sticky-category-header {
  background-color: #2A2419;
  border-bottom-color: #1C1812;
}
```
Replace with:
```css
.dark .sticky-category-header {
  background-color: #2a1c10;
  border-bottom-color: #1a1008;
}
```

- [ ] **Step 10: Verify build passes**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0.

- [ ] **Step 11: Commit**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/index.css && git commit -m "feat(theme): update dark mode !important overrides to terracotta palette"
```

---

## Chunk 3: Verification

### Task 8: Final audit and visual check

**Files:**
- Read: `frontend/src/index.css` (verify no old values remain)

- [ ] **Step 1: Run the grep allow-list check**

Run each command below. Each should return 0 results. A non-zero result means a value was missed and must be fixed before proceeding.

```bash
# Old coffee-brown values (should all be gone)
grep -n "#6F4E37\|#4A3728\|#A0826D\|#F5E6D3\|#FAF8F5\|#8B9D83\|#A8B89F" \
  /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css

# Old dark text
grep -n "#F5F0E8\|#E8DFD3\|#C5B8A8\|#9B8977" \
  /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css

# Old dark backgrounds
grep -n "#2A2419\|#1C1812\|#3A3128\|#4A4034" \
  /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css

# Old rgba bases
grep -n "rgba(44, 36, 32,\|rgba(79, 50, 35,\|rgba(111, 78, 55,\|rgba(184, 145, 106," \
  /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```

Expected: all return 0 lines. If any lines appear, cross-reference against the Hardcoded Colour Audit table in the spec (`docs/superpowers/specs/2026-03-17-aesthetic-overhaul-design.md`) and apply the appropriate replacement.

- [ ] **Step 2: Confirm known survivors are present (sanity check)**

```bash
# These SHOULD still exist — confirm they do
grep -n "#f6f1ea\|#c0392b\|#a93226" \
  /Users/angelxlakra/dev/lily-cafe-pos/frontend/src/index.css
```

Expected: 3+ results (btn-success text, btn-destructive reds). If 0 results, something went wrong in Task 6.

- [ ] **Step 3: Run full build and type-check**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
```

Expected: exits 0 with no TypeScript errors.

- [ ] **Step 4: Visual check — start dev server**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run dev
```

Open http://localhost:5173 (or whatever port Vite reports) in a browser. Check:

- [ ] Page background is parchment (`#fdf7f2`), not off-white/cream from old design
- [ ] Primary buttons are terracotta (`#c04e30`), not coffee brown
- [ ] Page titles (h1) are in italic Fraunces — e.g. login page, order page headers
- [ ] Section headings (h2) are in upright Fraunces, bold
- [ ] Body text and card content is in Plus Jakarta Sans (clean, geometric — not serif)
- [ ] Dark mode toggle: backgrounds are deep warm dark (`#1a1008`), primary actions lighten to `#e07050`
- [ ] Chips in light mode: parchment fill with terracotta active state
- [ ] Cart buttons in dark mode: terracotta-tinted (not old coffee brown)

- [ ] **Step 5: Final commit**

```bash
cd /Users/angelxlakra/dev/lily-cafe-pos && git add -p && git commit -m "feat(theme): aesthetic overhaul — Terracotta & Sand complete"
```

---

## Summary of Commits

| Commit | What changes |
|---|---|
| `chore(fonts): replace Quesha+Inter with Fraunces+Plus Jakarta Sans` | index.html preconnect, @font-face removed, Google Fonts @import added, Quesha.ttf deleted |
| `feat(theme): swap color tokens to Terracotta & Sand palette` | @theme + .dark {} CSS variable values |
| `feat(typography): apply Fraunces italic h1, h2 weight, h3 sans, btn weight` | h1/h2/h3/btn CSS rule edits |
| `feat(theme): update light-mode hardcoded colours to terracotta palette` | All rgba/hex in utility classes |
| `feat(theme): update dark mode !important overrides to terracotta palette` | Dark override block lines 82–203 |
| `feat(theme): aesthetic overhaul — Terracotta & Sand complete` | Any cleanup items from verification |
