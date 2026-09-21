---
target: inventory management
total_score: 28
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 1
target_identity: "file:/Users/angel/projects/lily-cafe-pos/frontend/src/pages/InventoryPage.tsx"
target_fingerprint: "sha256:0199f246b2bc58f420178691d304b38857d86e3f73108ab1222bd2725bb90427"
target_path: /Users/angel/projects/lily-cafe-pos/frontend/src/pages/InventoryPage.tsx
timestamp: 2026-09-21T15-47-59Z
slug: frontend-src-pages-inventorypage-tsx
---
Method: two separate assessments (a design review and a detector scan with a live-page overlay). Re-score after Phases 1–6.

## Design Health Score: 28/40 (Good). It was 18/40.
| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of status | 3 | "The owner has been emailed" only means SMTP is on, not that the email was sent |
| 2 | Match with the real world | 3 | Import modal wording ("Parse Template", "Min Threshold") |
| 3 | User control and freedom | 3 | Exit doesn't visibly say the count is kept |
| 4 | Consistency and standards | 2 | Import modal off-system; ½ accepted only in the count; IST only in the Stock log |
| 5 | Error prevention | 2 | Can save 0/130; a count after midnight lands on tomorrow; count-order saves race |
| 6 | Recognition over recall | 3 | Ordinary changes aren't listed at review |
| 7 | Flexibility and efficiency | 3 | No "move to top" in the count-order editor |
| 8 | Aesthetic and minimalist design | 3 | Item name gets about 118px on a 360px phone |
| 9 | Error recovery | 3 | The import reports success even when some items failed |
| 10 | Help and documentation | 2 | Nothing explains what ✓ means to a first-timer |

## Detector
The static scan of the inventory code is clean (0 findings). Live pages: the progress bar animates width (true positive); the category fold animates grid rows (deliberate); "Admin Portal" caption is 10.4px (sidebar); Inter and cream are false positives.

## Priority Issues
- [P0] A count saved after midnight is filed under the next day (`business_today()` has no cutoff), so the next night shows "Counted tonight". inventory.py:667, business_day.py:31
- [P1] A count can be saved with 0 of 130 counted. InventoryCountPage.tsx:310, CountReviewSheet.tsx:141
- [P2] The count row is cramped on a phone, and ✓ is only 8px from −. CountRow.tsx:100-187
- [P2] Screen-reader feedback: steppers are silent, the live region reads a bare "13/130", sheets don't trap or return focus, and the category header is a button that does nothing. CountRow.tsx, InventoryCountPage.tsx:198,265
- [P2] Count-order saves can race and leave a stale order on the server. CountOrderEditor.tsx:152

## Minor Observations
DESIGN.md still mentions sticky category headers; the pinned bars use backdrop-blur; "Count again" leaves duplicate date rows; the Stock log detects counts by matching note text; ✓ stores the system quantity at the moment of the tap; the import textarea autofocuses; the review sheet overrides headings with ! classes.
