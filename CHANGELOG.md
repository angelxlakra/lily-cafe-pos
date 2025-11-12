# Changelog

All notable changes to the Lily Cafe POS System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (v0.2 - In Development)
- Dark mode theme toggle with persistent preferences
- Inventory categories management (add, edit, delete)
- Inventory items management with units and thresholds
- Purchase tracking for stock additions
- Daily usage recording for inventory consumption
- Physical count adjustments for inventory corrections
- Low stock alerts on admin dashboard
- Inventory transaction history with audit trail
- Daily cash counter with opening/closing balance tracking
- Owner verification system for cash counter
- Cash variance calculations

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
