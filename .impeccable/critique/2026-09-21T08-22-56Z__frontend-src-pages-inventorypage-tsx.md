---
target: inventory management
total_score: 18
max_score: 40
na_heuristics: 
p0_count: 2
p1_count: 2
target_identity: "file:/Users/angel/projects/lily-cafe-pos/frontend/src/pages/InventoryPage.tsx"
target_fingerprint: "sha256:e3c9b4dd85355ee50ac7cd3907d4d176f1010a9249f4b7b7522f940d8e434175"
target_path: /Users/angel/projects/lily-cafe-pos/frontend/src/pages/InventoryPage.tsx
timestamp: 2026-09-21T08-22-56Z
slug: frontend-src-pages-inventorypage-tsx
---
Method: two separate assessments (a design review and a detector scan), plus a live browser check run after both finished.

## Design Health Score: 18/40 (Poor)
| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 2 | Progress only counts changed items; a correct shelf never counts |
| 2 | Match with the real world | 2 | Everything shows as "pcs" with two decimals; ½ appears as 0.50; raw codes in History |
| 3 | User control and freedom | 1 | Switching tabs silently throws away the count (confirmed live) |
| 4 | Consistency and standards | 2 | Browser alert/confirm popups despite ConfirmDialog; three modal styles; purchases under "History" |
| 5 | Error prevention | 1 | No warning when leaving mid-count, no check on big differences, silent rejects |
| 6 | Recognition over recall | 2 | Alphabetical rather than shelf order; 130-item dropdown with no search |
| 7 | Flexibility and efficiency | 2 | ±1/±5 are good; no "matches" tap, no jump, no "next uncounted" |
| 8 | Aesthetic and minimalist design | 2 | Each row about 175px; count page about 24,600px long |
| 9 | Error recovery | 2 | Entries kept on a failed save, but errors are raw alerts or console-only |
| 10 | Help and documentation | 2 | The import screen lists accepted formats; the count has no guidance |

## Design Specificity
Generic stock-management admin apart from the Daily Count tab, which has the right structure but was not designed for 11pm, one hand, 130 items.
Detector: side-tab at InventoryTransactionsTab.tsx:54 is real; border-accent-on-rounded at InventoryPage.tsx:87 is a false positive (a normal tab underline); a Tailwind class name built at runtime at InventoryTransactionsTab.tsx:56. Live overlay: muted text #8F8076 contrast about 3.6:1; the "Admin Portal" caption is 10.4px.

## Priority Issues
- [P0] Leaving mid-count wipes the count with no warning (confirmed live). DailyCountTab.tsx:38, InventoryPage.tsx:69. Fix: localStorage draft keyed by business date, a resume prompt, and a warning on unload or tab change. /impeccable harden
- [P0] "Counted" only means "changed". DailyCountTab.tsx:122, :55. Fix: track confirmed separately from changed, a one-tap ✓ per row, progress based on confirmed items. /impeccable shape
- [P1] The sticky page header hides the progress card and category headers (confirmed live). InventoryPage.tsx:20, DailyCountTab.tsx:203, CategorySection.tsx:42. Fix: one compact pinned count bar. /impeccable layout
- [P1] Saving is a browser popup with no review. DailyCountTab.tsx:94, :149. Fix: a review sheet before saving and a finish screen after. /impeccable delight
- [P2] Rows are too tall and busy; ½ shows as 0.50; negative numbers dropped silently. ItemCountRow.tsx:54-149. Fix: one line per item, ±5 on long-press. /impeccable distill

## Persona Red Flags
- Counter admin: the waiter bottom nav appears on the count screen; owner-only tabs are visible; alphabetical order; no finish.
- Casey: one stray tap wipes the count; −5/−1 at the left edge.
- Jordan: a bar stuck at 0%; Save greyed out with no reason; Adjustment vs Count unexplained.
- Sam: no tab markup; edit/delete only on hover; icon-only buttons without labels; inputs not tied to item names; muted text contrast.

## Minor Observations
- Bare "Daily count" note replaces the backend's prev → new note; recorded_by 'Staff' placeholder; History dates not in IST and capped at 20; an adjustment to 0 is blocked; bg-white/shadow-xl in the import modal; ⏳ emoji spinner; duplicate headings.

## Questions
- Walk order instead of alphabetical? Full-screen count mode? Count only the fast movers nightly?
