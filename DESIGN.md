---
name: Lily Cafe POS
description: Order, bill and close-of-day tool for Lily Cafe by Mary's Kitchen.
colors:
  coffee-brown: "#6F4E37"
  coffee-dark: "#4A3728"
  coffee-light: "#A0826D"
  lily-green: "#8B9D83"
  lily-green-light: "#A8B89F"
  lily-green-deep: "#5A6655"
  lily-ink: "#5A6655"
  cream: "#F5E6D3"
  off-white: "#FAF8F5"
  neutral-background: "#FFFCF7"
  neutral-border: "#D4C4B0"
  neutral-text-dark: "#2C2420"
  neutral-text-body: "#43352D"
  neutral-text-light: "#6B5D54"
  neutral-text-muted: "#736459"
  success: "#276C2B"
  error: "#B3342A"
  warning: "#9E4A06"
  info: "#1565C0"
typography:
  display:
    fontFamily: "Quesha, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(2.75rem, 3vw + 1.75rem, 3.75rem)"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "0.06em"
  headline:
    fontFamily: "Quesha, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(1.85rem, 1.8vw + 1.2rem, 2.5rem)"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "0.05em"
  title:
    fontFamily: "Quesha, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(1.5rem, 1.2vw + 1rem, 2rem)"
    fontWeight: 400
    lineHeight: 1.25
    letterSpacing: "0.04em"
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.2
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "12px"
  2xl: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  touch: "48px"
components:
  button-primary:
    backgroundColor: "{colors.coffee-brown}"
    textColor: "{colors.cream}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.coffee-dark}"
    textColor: "{colors.cream}"
  button-secondary:
    backgroundColor: "{colors.cream}"
    textColor: "{colors.coffee-brown}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "48px"
  button-success:
    backgroundColor: "{colors.lily-green-deep}"
    textColor: "{colors.off-white}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "48px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.neutral-text-light}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "48px"
  card:
    backgroundColor: "{colors.off-white}"
    rounded: "{rounded.xl}"
    padding: "16px"
  input-field:
    backgroundColor: "{colors.off-white}"
    textColor: "{colors.neutral-text-dark}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
  chip:
    backgroundColor: "{colors.cream}"
    textColor: "{colors.neutral-text-dark}"
    rounded: "{rounded.full}"
    padding: "8px 16px"
  chip-active:
    backgroundColor: "{colors.coffee-brown}"
    textColor: "{colors.cream}"
  badge:
    rounded: "{rounded.full}"
    padding: "4px 10px"
    typography: "{typography.label}"
---

# Design System: Lily Cafe POS

## Overview

**Creative North Star: "Mary's Kitchen Notebook"**

The Quesha display face gives the app a handwritten, homely warmth. Everything underneath it is plain and practical: table numbers, running orders, bills and cash counts, set in a sturdy sans on warm cream paper. The notebook is the kitchen's own. It is warm and a little personal, but it stays orderly, because the counter has to settle bills from it in a queue.

Density is moderate. Screens run from a phone-first waiter floor (table grid, bottom navigation, cart drawer) to a desktop counter and owner layout (collapsible roasted-brown sidebar with cards on cream). There is a full dark mode, toggled by a `.dark` class, which re-tones the palette to warm espresso rather than switching to neutral grey.

The system currently layers depth through soft shadows, gradient-filled primary buttons and hover lift. That is recorded below exactly as implemented and flagged as drift. It is more ornament than a billing tool needs.

**Motion** explains what changed; it never decorates or makes anyone wait. One decelerating curve (`--ease-settle`, `cubic-bezier(0.16, 1, 0.3, 1)`) and short timings: presses 120ms, state changes 200ms, overlays 250ms, theme fades 300ms. Entrances are `animate-fade-in` (scrims, banners), `animate-scale-in` (dialogs), `animate-slide-up` (bottom sheets) and `animate-row-in` (list rows). Changes on live lists use `animate-arrive`, `animate-highlight` and `animate-depart`. Money counts to its new value with `useCountUp`, and a finished action gets one `animate-draw` checkmark. The screen's one authored moment is the bill settling in the payment modal. Under `prefers-reduced-motion`, movement becomes a plain fade while colour and state changes stay.

**Key Characteristics:**
- Quesha, the handwritten display face, is used for headings and table numbers only. Everything operational is set in sans.
- Warm roasted-brown primaries on cream and off-white paper, with lily green for positive and settled states.
- Every tappable control is at least 48px. The floor is a touch surface.
- Money and counts are set in monospace or tabular numerals.
- Dark mode is espresso-warm, never cool grey.
- Motion is short, decelerating and informative: counts roll, finished things get one checkmark, nothing bounces.

## Colors

A roasted-coffee palette on cream paper, with one botanical green borrowed from the lily logo.

### Primary
- **Roasted Coffee** (coffee-brown): primary actions, active chips, sticky inventory category headers, focus borders on inputs. It is the colour of "do this".
- **Espresso** (coffee-dark): the sidebar background and the deep end of the primary gradient. Hover state for primary buttons.
- **Milky Latte** (coffee-light): sidebar dividers, secondary button borders, hover borders on chips.

### Secondary
- **Lily Leaf** (lily-green): fills and tints for paid or settled states, available tables and positive indicators. Taken from the lily mark. Too light for text (2.7:1).
- **Pale Lily Leaf** (lily-green-light): lighter tints behind green states.
- **Deep Lily Leaf** (lily-green-deep): filled "done" controls with white icons, such as the count's ✓ and the success button.
- **Lily Ink** (lily-ink): Lily Leaf for text and icons on paper. It re-tones to a pale green in dark mode.

### Neutral
- **Cream Paper** (cream): secondary button fill, chips at rest, soft gradient backgrounds, text on dark brown.
- **Notebook White** (off-white): card and input surfaces.
- **Warm Page** (neutral-background): the page background under everything.
- **Pencil Rule** (neutral-border): input strokes, card hairlines and dividers.
- **Ink** (neutral-text-dark): headings and primary figures.
- **Body Ink** (neutral-text-body): default running text.
- **Faded Ink** (neutral-text-light) and **Margin Note** (neutral-text-muted): secondary labels, placeholders and meta.

### Functional
- **success / error / warning / info**: deep green, brick red, burnt amber and blue, used for status text, badges and destructive affordances, and as `/10` tints behind them. They are dark enough to read as text (at least 4.5:1 on paper, page and cream). In dark mode they re-tone lighter, so text on a solid status fill switches to dark (`dark:text-neutral-background`). They are semantic signals, not brand colours.

### Named Rules
**The Brown Means Go Rule.** Roasted Coffee is the only colour for the primary action on a screen. Settled or paid outcomes get Lily Leaf, not brown.

**The Readable Signal Rule.** Status and Lily Leaf text always uses a token that passes 4.5:1 (`text-success`, `text-warning`, `text-error`, `text-info`, `text-lily-ink`). Never hard-code a hex to get a darker shade.

**The Espresso Dark Rule.** Dark mode re-tones every token to warm brown-black (page `#1C1812`, surface `#2A2419`, raised `#3A3128`, text `#F5F0E8`). Never introduce neutral greys (`neutral-800` and similar) in dark mode.

## Typography

**Display Font:** Quesha, self-hosted at `/fonts/Quesha.ttf` (fallback: Georgia, serif)
**Body Font:** Inter (fallback: ui-sans-serif, system-ui). Inter is declared but not loaded, so in practice this renders in the system sans.
**Label/Mono Font:** the system monospace via `font-mono`, for prices, totals, order numbers and counts.

**Character:** a handwritten notebook heading over a plain working hand. The contrast is the brand. Quesha supplies the personality so that nothing else has to.

### Hierarchy
- **Display** (Quesha 400, clamp(2.75rem → 3.75rem), line-height 1.05, tracking 0.06em): page heroes via `heading-display`, and the big table numbers on the waiter grid.
- **Headline** (Quesha 400, clamp(1.85rem → 2.5rem), 1.2, 0.05em): section titles via `heading-section`.
- **Title** (Quesha 400, clamp(1.5rem → 2rem), 1.25, 0.04em): sub-sections and modal titles via `heading-sub`. Plain `h1` to `h3` also get Quesha globally.
- **Body** (sans 400, 1rem, 1.6): all operational copy, menu item names and form text.
- **Label** (sans 600, 0.75rem): badges, bottom-nav labels and sidebar sub-captions. The sidebar caption is uppercase with 0.3em tracking.

### Named Rules
**The Quesha Is a Heading Rule.** Quesha is only for headings, brand wordmarks and table numbers. Never use it for prices, buttons, form labels or anything someone has to read under pressure.

**The Honest Numbers Rule.** Rupee amounts, quantities and order numbers use `font-mono` or `tabular-nums`, so that columns of money line up.

## Layout

The layout is mobile-first and follows an 8px rhythm. Tailwind's default spacing scale is used, with 4, 8, 16, 24 and 32px dominating. `--spacing-18` (72px) and `--spacing-88` (352px) are the only custom steps.

- **Waiter floor (phone):** a table grid that steps from 2 to 5 columns (`grid-cols-2 sm:3 md:4 lg:5`, 16px gap). There is a fixed bottom navigation bar with 48px items and a floating cart button, and content keeps a `pb-24` bottom pad to clear the bar.
- **Counter and owner (desktop):** a left sidebar that collapses to an icon rail, becomes an overlay drawer below `lg` (1024px), and has content cards on the Warm Page background.
- **Breakpoints:** Tailwind defaults (sm 640, md 768, lg 1024, xl 1280). `lg` is the sidebar and bottom-nav switch.
- **Inventory count:** a single scrolling column with sticky Roasted Coffee category headers and full-width rows.

**The 48px Floor Rule.** Every interactive control has a hit area of at least 48 × 48px (`--min-height-touch`, `touch-target-large`). This is non-negotiable on the waiter and count screens.

## Elevation & Depth

The system is currently a **soft-lift hybrid**. Cards carry a two-layer ambient shadow at rest. Primary buttons carry a coloured drop shadow and a gradient, and they rise by 1px on hover. Interactive cards rise by 2 to 3px, and `surface-glass` adds a 12px backdrop blur. Dark mode swaps shadows for a faint warm border (`rgba(184,145,106,0.15)`).

> **Flagged as drift.** Depth is expressed four ways at once: three shadow levels, gradients, hover lift and glass. That exceeds what a counter tool needs, and lift-on-hover does nothing on the touch devices where most use happens. Future work should converge on a flatter, tonal model rather than add more elevation.

### Shadow Vocabulary
- **Soft** (`0 2px 8px rgba(44,36,32,0.06), 0 4px 16px rgba(44,36,32,0.04)`): the default `<Card>`.
- **Medium** (`0 4px 12px rgba(44,36,32,0.08), 0 8px 24px rgba(44,36,32,0.06)`): the hover state of interactive cards.
- **Strong** (`0 8px 20px rgba(44,36,32,0.12), 0 16px 40px rgba(44,36,32,0.08)`): modals and prominent panels.
- **Button drop** (`0 8px 16px -10px rgba(79,50,35,0.6)`): primary button at rest.

### Named Rules
**The No New Shadows Rule.** Don't add shadow levels, glass surfaces or gradients. Reuse Soft, Medium and Strong, or go flat.

## Shapes

Corners are gently rounded and never sharp. Buttons are 6px (`btn`) or 8px (`rounded-lg`, the most common radius in the codebase). Inputs are 10px, cards and panels are 12px (`rounded-xl`), and large modals are 16px. Chips, badges, avatars and the sidebar collapse toggle are full pills or circles. Borders are thin hairlines in Pencil Rule. Inputs and chips use a slightly heavier 1.5px stroke so they read as touchable.

## Components

### Buttons
Tactile and confident, and sized for a thumb.
- **Shape:** gently rounded (6px), minimum 48 × 48px, 16px horizontal padding, weight 500.
- **Primary** (`btn-primary`): a 135° gradient from Roasted Coffee to Espresso, with Cream Paper text and a coloured drop shadow.
- **Hover / Active:** hover rises 1px and deepens the gradient. Active returns to 0. Disabled drops to 55% opacity with no shadow.
- **Secondary** (`btn-secondary`): Cream Paper fill, Roasted Coffee text and a Milky Latte border.
- **Success** (`btn-success`): a Lily Leaf gradient. Used for confirm payment, mark served and save count.
- **Destructive** (`btn-destructive`): a 12% red tint with a red border. Not solid red.
- **Ghost** (`btn-ghost`): transparent with Faded Ink text.
- **Divergent:** the `<Button>` React component (used 4 times) has its own variant set (solid `bg-success` or `bg-error`, `rounded-lg`, a focus ring). It is not canonical. The `.btn-*` utilities are the source of truth.

### Chips
- **Style:** pill, Cream Paper fill, 1.5px Pencil Rule border, 14px weight 500. Used for menu category filters and date quick filters.
- **State:** active switches to the Roasted Coffee gradient with Cream Paper text. Dark active flips to a light coffee fill with espresso text.

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** Notebook White with a 50% Pencil Rule hairline. The `filled` variant uses Cream Paper.
- **Shadow Strategy:** Soft at rest, Medium on interactive hover (see Elevation & Depth).
- **Internal Padding:** 16px on phone and 24px from `sm` up. The `lg` variant is 24 to 32px.

### Inputs / Fields
- **Style:** full width, Notebook White, 1.5px Pencil Rule stroke, 10px radius, 12 × 16px padding, 1rem text.
- **Focus:** the border turns Roasted Coffee, the fill goes to white, and a soft 3px coffee halo appears.
- **Disabled:** Pencil Rule fill at 60% opacity.
- **Count input:** centred, bold 1.125rem numerals, spinners removed, max 100px wide. Used for inventory counts.

### Navigation
- **Sidebar (counter and owner):** Espresso background, with a lily logo and a Quesha wordmark at 0.18em tracking over an uppercase caption. Items are 8px-rounded rows with icons, and it collapses to an icon rail with hover tooltips. It becomes an overlay drawer with a 50% black scrim below 1024px.
- **Bottom nav (waiter):** fixed and equal-width, with 24px icons over 12px semibold labels. The active tab has a Roasted Coffee gradient fill and a Cream Paper indicator bar along the top edge.

### Table Tile (signature)
This is the waiter's entry point. A square card carries the table number in Quesha display with a status pill underneath. Occupied tables show a soft blurred Lily Leaf glow in the corner. Tiles sit in a responsive 2 to 5 column grid.

### Count Row (signature)
One line per stock item in Tonight's Count. The name and a status line sit on the left. On the right, in right-thumb reach, are a 48px ✓ ("matches") and a `− value +` stepper with press-and-hold. Values display as ½, ¼ and ¾. The row tints Lily Leaf when checked and Cream when changed, and big differences get a burnt-amber warning. Finished categories fold into a one-line summary.

### Settling Bill (signature)
The payment modal's Remaining tile counts down as payments are added. When it lands on ₹0, the tile turns Lily Leaf, reads "Fully paid", a checkmark draws in, and Complete fills with brown from left to right. The button is enabled by the real balance, not by the animation.

### Badges
Pill-shaped, 12px weight 600, with semantic tints for order and payment status.

### Icons
Phosphor Icons. `duotone` is the default weight, with `bold` for emphasis and `fill` for active states. The payment method icons (cash, card, UPI) are PNGs in `/public/icons`.

## Do's and Don'ts

### Do:
- **Do** use the `.btn-*`, `card`, `chip`, `badge` and `input-field` utilities from `index.css` before writing new Tailwind stacks.
- **Do** keep every interactive control at 48px or larger.
- **Do** set rupee amounts and counts in `font-mono` or `tabular-nums`.
- **Do** use Lily Leaf for paid, served and available states, and Roasted Coffee for the next action.
- **Do** define dark-mode colours by re-toning tokens under `.dark`, keeping them warm.
- **Do** use the shared motion utilities (`animate-*`, `useCountUp`, `useListPresence`) and `--ease-settle` rather than new keyframes or curves.
- **Do** give every async surface a plain-language error with a retry (`describeApiError`), and never lose what someone typed.

### Don't:
- **Don't** set prices, buttons or form labels in Quesha.
- **Don't** introduce cool neutral greys (`neutral-800`, `bg-white` without a dark override) in either theme.
- **Don't** add new shadow levels, glass panels or gradients. Depth is already over-expressed.
- **Don't** extend the `<Button>` component's divergent variant set. Align it with `.btn-*` or use the utilities directly.
- **Don't** add more `!important` dark-mode patches to `index.css`. Fix the token instead.
- **Don't** use bounce or elastic curves, infinite loops, hover lift, or staggered reveals across long lists.
- **Don't** use browser `alert`/`confirm`. Use `ConfirmDialog` or an inline message.
- **Don't** mark a card with a thick coloured left edge. Use a thin tinted border.
