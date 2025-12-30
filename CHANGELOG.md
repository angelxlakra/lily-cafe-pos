# Changelog

All notable changes to the Lily Cafe POS System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.2.0] - 2025-12-30

### Added

#### 📦 Inventory Management System
- **WhatsApp Template Import Tool**
  - One-time bulk import from WhatsApp inventory templates
  - Supports 155+ items with mixed unit formats
  - Parses fractions (½, ¼, ¾), YES/NO, weights (50g, 4kg, 500ml)
  - Auto-creates categories and items with proper associations
  - Preview before import with validation

- **Mobile-First Daily Count UI** ⭐ *Primary Feature*
  - Touch-optimized interface for end-of-day stock counting
  - Replaces WhatsApp-based workflow with digital checklist
  - Items grouped by categories with sticky headers
  - Quick +/- buttons with 48px touch targets
  - Direct numeric input with mobile keyboard
  - Visual highlighting of changed quantities
  - Progress tracking (X of Y items counted)
  - Batch adjustment saves all changes atomically
  - Designed for <15 minute daily counts

- **Inventory Items Management**
  - Full CRUD operations for inventory items
  - Category associations with auto-categorization
  - Unit tracking (pcs, kg, L, etc.)
  - Min threshold configuration for low stock alerts
  - Cost per unit tracking
  - Active/inactive status toggle
  - Search and filter by category, name, stock level

- **Inventory Categories**
  - Full CRUD operations for categories
  - Unique name validation
  - Automatic timestamp management
  - Item count per category

- **Transaction Tracking**
  - **Purchase**: Record stock additions from suppliers
  - **Usage**: Track daily consumption and usage
  - **Adjustment**: Manual corrections for physical counts
  - **Batch Adjustment**: Daily Count saves create atomic adjustments
  - Audit trail with previous/new quantities
  - Transaction history with filtering by type and date
  - Recorded by staff tracking

- **Low Stock Alerts**
  - Real-time low stock detection
  - Visual badges on low stock items
  - Percentage remaining calculation
  - Configurable min_threshold per item
  - Dashboard summary of items needing restock

#### 💰 Cash Counter System
- **Daily Cash Counter**
  - Open counter with opening balance
  - Close counter with closing balance entry
  - Cannot open if already open (single counter per day)
  - Cannot close if not open
  - Date-based counter tracking

- **Owner Verification**
  - Password-protected verification workflow
  - Admin-only verification access
  - Verification status tracking
  - Verified timestamp and verified_by tracking

- **Variance Tracking**
  - Automatic variance calculation (actual - expected)
  - Expected closing based on day's orders
  - Visual highlighting of significant variances
  - Cash count history with variance trends
  - Notes field for explaining discrepancies

### Changed
- Admin sidebar now includes Inventory and Cash Counter menu items
- Dashboard updated with inventory and cash counter stats
- Navigation structure reorganized for new features

### Technical

#### Backend
- **New Database Tables** (4 tables)
  - `inventory_categories` - Category management
  - `inventory_items` - Item master with units and thresholds
  - `inventory_transactions` - Transaction audit trail
  - `daily_cash_counter` - Cash count records

- **New API Endpoints** (20+ endpoints)
  - `GET/POST/PATCH/DELETE /api/v1/inventory/categories`
  - `GET/POST/PATCH/DELETE /api/v1/inventory/items`
  - `GET /api/v1/inventory/items/low-stock`
  - `POST /api/v1/inventory/transactions/purchase`
  - `POST /api/v1/inventory/transactions/usage`
  - `POST /api/v1/inventory/transactions/adjustment`
  - `POST /api/v1/inventory/transactions/batch-adjustment`
  - `GET /api/v1/inventory/transactions`
  - `POST /api/v1/cash-counter/open`
  - `POST /api/v1/cash-counter/close`
  - `POST /api/v1/cash-counter/verify`
  - `GET /api/v1/cash-counter/today`
  - `GET /api/v1/cash-counter/history`

- **Pydantic v2 Migration**
  - All schemas updated to Pydantic v2 syntax
  - `model_validate()` with `from_attributes=True`
  - Schema Config uses `from_attributes` instead of `orm_mode`
  - Proper datetime validation for all timestamps

- **Database Migration Script**
  - `migrate_v01x_to_v020.py` - Unified migration script for all v0.2.0 changes
  - Adds `is_parcel` column to order_items (parcel feature)
  - Creates 4 new inventory/cash tables with proper constraints
  - Idempotent (safe to run multiple times)
  - Preserves existing data
  - Rollback-safe

#### Frontend
- **New Components**
  - `InventoryPage.tsx` - Main inventory management interface
  - `DailyCountTab.tsx` - Mobile-optimized daily count UI
  - `ItemCountRow.tsx` - Touch-optimized item counter
  - `CategorySection.tsx` - Collapsible category grouping
  - `TemplateImportModal.tsx` - WhatsApp template import
  - `InventoryTransactionsTab.tsx` - Transaction history
  - `CashCounterPage.tsx` - Cash counter management

- **New Utilities**
  - `unitParser.ts` - Parse mixed WhatsApp formats
  - Functions: `parseQuantity()`, `parseWhatsAppTemplate()`, `extractCategory()`

- **New API Clients**
  - `api/inventory.ts` - Inventory API integration
  - `api/cashCounter.ts` - Cash counter API integration

- **New Hooks**
  - `useInventory.ts` - Inventory state management
  - `useCashCounter.ts` - Cash counter state management
  - React Query integration for all endpoints

### Fixed
- Category creation now properly sets timestamps (resolved 500 errors)
- Adjustment endpoint accepts optional notes (resolved 422 errors)
- Items properly associated with categories during import
- All Pydantic v2 compatibility issues resolved
- Response validation works correctly for all endpoints

### Database Schema Changes
```sql
-- Modified Tables (v0.1.3 feature included)
ALTER TABLE order_items ADD COLUMN is_parcel BOOLEAN DEFAULT 0 NOT NULL;

-- New Tables
CREATE TABLE inventory_categories (
  id INTEGER PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE inventory_items (
  id INTEGER PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  unit VARCHAR(20) NOT NULL,
  current_quantity DECIMAL(10,2) NOT NULL DEFAULT 0,
  min_threshold DECIMAL(10,2) NOT NULL DEFAULT 0,
  cost_per_unit DECIMAL(10,2),
  category_id INTEGER REFERENCES inventory_categories(id),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE inventory_transactions (
  id INTEGER PRIMARY KEY,
  item_id INTEGER REFERENCES inventory_items(id),
  transaction_type VARCHAR(20) NOT NULL,
  quantity DECIMAL(10,2) NOT NULL,
  notes VARCHAR(500),
  recorded_by VARCHAR(100) NOT NULL,
  previous_quantity DECIMAL(10,2) NOT NULL,
  new_quantity DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_cash_counter (
  id INTEGER PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  opening_balance DECIMAL(10,2) NOT NULL,
  closing_balance DECIMAL(10,2),
  expected_closing DECIMAL(10,2),
  variance DECIMAL(10,2),
  notes TEXT,
  opened_by VARCHAR(100) NOT NULL,
  closed_by VARCHAR(100),
  verified_by VARCHAR(100),
  is_verified BOOLEAN DEFAULT FALSE,
  opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  closed_at TIMESTAMP,
  verified_at TIMESTAMP
);
```

### Migration Instructions
1. **Backup database**: `cp restaurant.db restaurant_pre_v0.2.0_backup.db`
2. **Checkout code**: `git checkout v0.2.0`
3. **Backend dependencies**: `cd backend && uv sync`
4. **Run migration**: `uv run python scripts/migrate_v01x_to_v020.py`
5. **Frontend dependencies**: `cd ../frontend && npm install`
6. **Build frontend**: `npm run build`
7. **Restart services**: Restart backend and frontend servers
8. **Verify**: Check that new tables and columns exist, API is accessible

### Breaking Changes
- None (fully backward compatible)

### Performance
- Daily Count UI optimized for 155+ items with smooth scrolling
- React Query caching reduces API calls
- Batch adjustments processed atomically
- Mobile-first responsive design

### Known Issues
- None

---

## [0.1.3] - 2025-12-30

**Note:** All v0.1.3 features are included in v0.2.0. If upgrading from v0.1.2, you can skip directly to v0.2.0.

### Added
- **Edit served quantity by clicking status badge**
  - Admins can now click on order item status badges (Done, Partial, or Pending) to edit the absolute number of items served
  - New modal interface with slider to set exact quantity served
  - Direct editing capability alongside incremental "Serve" button
  - Status badges now have hover effects indicating they're clickable
  - Validates quantity is between 0 and total ordered quantity

- **Item-level parcel marking**
  - Individual order items can now be marked as parcel/takeaway
  - Parcel items print on separate kitchen chits
  - Visual indicator for parcel items in order view

### Changed
- Status badges on Active Orders page are now clickable for direct quantity editing
- "Serve" button remains available for incremental serving workflow

### Technical
- Backend: New CRUD function `set_order_item_served_quantity()`
- Backend: New API endpoint `PUT /orders/{order_id}/items/{item_id}/served-quantity`
- Backend: Added `is_parcel` column to `order_items` table
- Frontend: New component `EditServedQuantityModal.tsx`
- Frontend: New React Query hook `useSetItemServedQuantity()` with optimistic updates
- Frontend: New API client method `setItemServedQuantity()`

### Database Changes
```sql
ALTER TABLE order_items ADD COLUMN is_parcel BOOLEAN DEFAULT 0 NOT NULL;
```

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
- **v0.1.3** (Dec 30, 2025) - Edit served quantity via status badge click
- **v0.2.0** (Dec 30, 2025) - Inventory management & cash counter system

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
