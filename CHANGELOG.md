# Changelog

All notable changes to the Lily Cafe POS System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (v0.3 - In Development)
- Inventory categories management (add, edit, delete) - _Planned_
- Inventory items management with units and thresholds - _Planned_
- Purchase tracking for stock additions - _Planned_
- Daily usage recording for inventory consumption - _Planned_
- Physical count adjustments for inventory corrections - _Planned_
- Low stock alerts on admin dashboard - _Planned_
- Inventory transaction history with audit trail - _Planned_
- Daily cash counter with opening/closing balance tracking - _Planned_
- Owner verification system for cash counter - _Planned_
- Cash variance calculations - _Planned_

---

## [0.1.2] - 2025-12-27

### Added
- **Partial serving with quantity tracking**
  - New `quantity_served` field in OrderItem model
  - Track how many items have been served vs ordered (e.g., 2 out of 5)
  - Visual slider modal to select quantity to serve
  - Quick buttons: None, Half, All
  - Status badges show: Done (✓), Partial (X/Y), or Pending
  - Real-time progress tracking per order item
  - Database migration script for existing installations

- **Payment method editing in order history**
  - Edit payment modes for completed orders
  - Replace/modify payment methods (e.g., change Cash to UPI)
  - Split payments differently after order completion
  - Modal with payment method selector and live validation
  - "Add remaining" quick button for convenience
  - Visual feedback ensures total matches order amount
  - Admin authentication required

- **Claude Code development guidelines**
  - Added CLAUDE.md with Python environment instructions
  - Standardized use of `uv` for all backend operations

### Changed
- Active Orders page: Replaced checkbox with status badges
- Active Orders page: Replaced Price column with Serve button
- Order History page: Added Edit button for payment methods
- API endpoint `/orders/{id}/items/{item_id}/served` now accepts `quantity_to_serve` parameter
- Payment update endpoint uses `refetchQueries` for immediate UI updates

### Fixed
- Preserved `quantity_served` count when adding duplicate items to order
  - Previously reset to 0, now maintains serving progress
- Status badge styling now uses lily-green theme color
  - Replaced generic green with app's coffee shop theme
  - Added `whitespace-nowrap` to prevent text wrapping in badges

### Technical
- Backend: New CRUD function `update_order_item_served_quantity()`
- Backend: New CRUD function `replace_order_payments()`
- Backend: New API endpoint `PUT /orders/{id}/payments`
- Frontend: New component `PartialServeModal.tsx`
- Frontend: New component `EditPaymentsModal.tsx`
- Frontend: New React Query hook `useUpdatePayments()`
- Database: Added `quantity_served INTEGER DEFAULT 0` column

---

## [0.1.1] - 2025-01-12

### Added
- **Dark mode theme toggle** with persistent preferences (localStorage)
  - Light/Dark/System theme options
  - Smooth 300ms transitions between themes
  - Warm coffee-themed dark mode colors
  - System preference detection (respects OS settings)
  - Theme toggle in admin sidebar
  - Floating theme toggle on waiter pages
  - All existing components fully support dark mode

### Fixed
- Comprehensive text visibility improvements across all dark mode interfaces
  - Fixed header text visibility on all pages (Tables, Active Orders, Order pages)
  - Fixed sidebar text visibility with proper contrast
  - Fixed cart drawer text and button visibility
  - Fixed floating cart button text visibility
  - Fixed bottom navigation active tab visibility
  - Fixed menu item plus/minus button visibility
  - Fixed search bar and input field backgrounds (warmer brown instead of black)
  - Fixed chip (category filter) backgrounds and active states

---

## [0.1.0] - 2025-11-11

### Added
- Initial MVP release
- Admin authentication with JWT tokens
- Menu management (CRUD operations)
- Category management
- Table grid view with active/empty status
- Order taking interface for waiters
- Cart system with floating button and drawer
- Active orders dashboard
- Order editing and cancellation (admin)
- Payment processing with split payment support
- Receipt generation and printing (80mm & 58mm thermal)
- Kitchen chit printing with auto-print
- Order history with date filtering
- Item serving status tracking
- GST calculation (18%) with SGST/CGST split
- Smart rounding (customer-friendly)
- Order number generation (ORD-YYYYMMDD-####)
- Dashboard statistics
- Multi-printer support (Windows/USB/Serial)
- QR codes on receipts for feedback
- Comprehensive documentation (15 guides)
- Deployment scripts for macOS/Linux/Windows

### Technical
- Backend: FastAPI + Python 3.11+
- Frontend: React 18 + TypeScript + Vite
- Database: SQLAlchemy ORM + SQLite
- Authentication: JWT with bcrypt password hashing
- API: RESTful design with /api/v1/ versioning
- UI: Tailwind CSS v4 with coffee theme
- State Management: React Query with caching
- Printer: ESC/POS protocol support

### Database Schema
- `categories` - Menu categories
- `menu_items` - Menu items with pricing
- `orders` - Customer orders with status tracking
- `order_items` - Order line items with snapshots
- `payments` - Payment records with split payment support

---

## Version History Summary

- **v0.1.0** (Nov 11, 2025) - Initial MVP with core POS functionality
- **v0.1.1** (Jan 12, 2025) - Dark mode theme toggle
- **v0.1.2** (Dec 27, 2025) - Partial serving & payment editing
- **v0.2.0** (Planned) - Inventory management and cash counter

---

## Release Notes Format

### [Version] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes in existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security improvements
