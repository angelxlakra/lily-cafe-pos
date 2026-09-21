# Lily Cafe POS System - Master Project Document

**Project Name:** Lily Cafe Point of Sale System  
**Client:** Lily Cafe by Mary's Kitchen  
**Project Type:** Restaurant Management Software  
**Deployment Model:** Self-hosted, Local Network  
**Status:** In Development  
**Last Updated:** October 30, 2024

---

## 📑 Table of Contents

1. [Project Overview](#project-overview)
2. [Business Requirements](#business-requirements)
3. [Technical Architecture](#technical-architecture)
4. [Core Principles & Decisions](#core-principles--decisions)
5. [Design System](#design-system)
6. [Version Roadmap](#version-roadmap)
7. [Data Model](#data-model)
8. [User Roles & Permissions](#user-roles--permissions)
9. [Deployment Strategy](#deployment-strategy)
10. [Success Metrics](#success-metrics)
11. [Known Constraints](#known-constraints)
12. [Future Considerations](#future-considerations)

---

## 🎯 Project Overview

### Purpose
Build a comprehensive, locally-hosted restaurant management system for Lily Cafe that helps owners manage food orders, billing with GST compliance, inventory management, and business analytics while keeping all data private on their own infrastructure.

### Key Objectives
1. **Replace manual processes** with digital order tracking
2. **Ensure GST compliance** with proper tax calculations and receipts
3. **Improve operational efficiency** for waiters and reception staff
4. **Enable data-driven decisions** through analytics and reporting
5. **Maintain data privacy** with local-only hosting
6. **Build learning foundation** for Python/LLM/MCP server skills

### Project Philosophy
- **Ship incrementally** - Deliver value early and often
- **Mobile-first for operations** - Waiters use phones, admin uses desktop
- **Local-first architecture** - No cloud dependency, works on local network
- **Privacy by design** - All data stays on cafe's hardware
- **Simple over complex** - Start simple, add complexity only when needed
- **Learn while building** - Balance client delivery with skill development

---

## 💼 Business Requirements

### Client Context
**Business:** Lily Cafe by Mary's Kitchen (small-medium cafe)  
**Current Process:** Manual order taking, paper-based tracking  
**Pain Points:**
- Difficult to track active orders across tables
- Manual GST calculations prone to errors
- No inventory visibility leading to stockouts
- Limited business insights for decision making
- Paper receipts can be lost or damaged

### Must-Have Features (All Versions)
1. ✅ Digital order taking and tracking
2. ✅ GST-compliant billing (rate configurable, 5% by default)
3. ✅ Receipt printing (thermal printer support)
4. ✅ Menu management
5. ✅ Order history
6. ✅ Table-based order tracking
7. ✅ Split payment support
8. ✅ Multi-user access (staff + admin)

### Nice-to-Have Features (Future Versions)
1. 📦 Inventory tracking and alerts
2. 🍳 Kitchen display system
3. 📊 Advanced analytics and reporting
4. 🍜 Menu item modifiers & add-ons (Extra soup, size variations, toppings)
5. 👥 Customer management
6. 📱 Mobile app for owners
7. ☁️ Optional cloud backup
8. 🤖 AI-powered insights via MCP
9. 🏪 Multi-location support

### Critical Business Rules
1. **One active order per table** - No duplicate orders on same table
2. **Orders are not billed immediately** - Customers order multiple times, pay at end
3. **GST is configurable** - 5% by default, set by the owner on the Settings page and applied to all items uniformly
4. **Prices are whole numbers** - No decimal pricing (₹80, not ₹80.50)
5. **Quantities are integers** - No fractional quantities (2 items, not 1.5 items)
6. **Payment can be split** - Customer can pay with multiple methods
7. **All data stays local** - No external data transmission

---

## 🏗️ Technical Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────┐
│  Frontend Layer (React/TypeScript)          │
│  - Waiter Interface (Mobile)                │
│  - Admin Interface (Desktop/Mobile)         │
│  - Responsive Design                        │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────┐
│  Backend Layer (FastAPI/Python)             │
│  - REST API Endpoints                       │
│  - Business Logic                           │
│  - Authentication & Authorization           │
│  - PDF Generation                           │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴─────────┬────────────────┐
        │                    │                │
┌───────▼────────┐  ┌────────▼──────┐  ┌─────▼──────┐
│ SQLite/        │  │ File Storage  │  │ MCP Server │
│ PostgreSQL     │  │ (receipts,    │  │ (v1.5+)    │
│ Database       │  │  backups)     │  │            │
└────────────────┘  └───────────────┘  └────────────┘
```

### Technology Stack

#### Frontend
- **Framework:** React 18+ with TypeScript
- **Build Tool:** Vite
- **Routing:** React Router DOM
- **State Management:** TanStack Query (React Query)
- **HTTP Client:** Axios
- **Styling:** Tailwind CSS
- **UI Components:** Custom components + Headless UI
- **Notifications:** React Hot Toast
- **Forms:** React Hook Form (future)

#### Backend
- **Framework:** FastAPI (Python 3.11+)
- **ORM:** SQLAlchemy 2.0
- **Database:** SQLite (v0.1-0.5) → PostgreSQL (v2.0+)
- **Validation:** Pydantic v2
- **Authentication:** JWT (python-jose)
- **Password Hashing:** Bcrypt (passlib)
- **PDF Generation:** ReportLab
- **Server:** Uvicorn (ASGI)

#### Infrastructure
- **Hosting:** Self-hosted on cafe laptop
- **Network:** Local WiFi network
- **Database:** File-based (SQLite) on local disk
- **Backups:** Local file copies (automated in v0.5+)
- **Printer:** USB thermal printer (80mm)

#### Development Tools
- **Version Control:** Git
- **Package Management:** uv (Python), npm (JavaScript)
- **Environment Management:** uv (automatic .venv management)
- **Code Formatting:** Black (Python), Prettier (JavaScript)
- **API Documentation:** FastAPI auto-generated (Swagger/OpenAPI)

---

## 🎨 Design System

### Brand Identity
**Brand:** Lily Cafe by Mary's Kitchen  
**Logo:** Minimalist lily flower design  
**Theme:** Coffee-inspired, minimal, natural

### Color Palette
```css
/* Primary Colors - Coffee Theme */
--coffee-brown: #6F4E37;      /* Main brand color */
--dark-brown: #4A3728;         /* Dark backgrounds */
--light-brown: #A0826D;        /* Hover states */

/* Secondary Colors */
--cream: #F5E6D3;              /* Light backgrounds */
--off-white: #FAF8F5;          /* Page background */
--lily-green: #8B9D83;         /* Accent from lily */

/* Functional Colors */
--success: #4CAF50;            /* Confirmations */
--error: #F44336;              /* Errors, destructive */
--warning: #FF9800;            /* Warnings, alerts */
--info: #2196F3;               /* Information */

/* Neutral Colors */
--text-dark: #2C2420;          /* Primary text */
--text-light: #6B5D54;         /* Secondary text */
--border: #D4C4B0;             /* Borders, dividers */
--background: #FFFCF7;         /* Card backgrounds */
```

### Typography
```css
/* Font Family */
Primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif
Monospace: 'JetBrains Mono', monospace (for numbers/codes)

/* Type Scale */
--text-xs: 12px;     /* Labels, captions */
--text-sm: 14px;     /* Body small */
--text-base: 16px;   /* Body text */
--text-lg: 18px;     /* Subheadings */
--text-xl: 20px;     /* Section titles */
--text-2xl: 24px;    /* Page titles */
--text-3xl: 30px;    /* Hero text */
--text-4xl: 36px;    /* Display text */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing System (8px base)
```css
--space-1: 4px;      /* Tight spacing */
--space-2: 8px;      /* Base unit */
--space-3: 12px;     /* Small gaps */
--space-4: 16px;     /* Default spacing */
--space-5: 20px;     /* Medium spacing */
--space-6: 24px;     /* Large spacing */
--space-8: 32px;     /* Section spacing */
--space-10: 40px;    /* Major sections */
--space-12: 48px;    /* Page spacing */
--space-16: 64px;    /* Large separations */
```

### Component Standards

#### Buttons
```
Primary: coffee-brown background, cream text, 48px height
Secondary: cream background, coffee-brown text, outlined
Tertiary: Text only, coffee-brown color
Disabled: 50% opacity

Border radius: 8px (medium), 12px (large)
Padding: 12px 24px (horizontal)
```

#### Cards
```
Background: off-white
Border: 1px solid border color
Border radius: 12px
Padding: 20px
Shadow: 0 4px 6px rgba(0,0,0,0.07)
```

#### Forms
```
Input height: 48px
Input padding: 12px 16px
Input border: 1px solid border
Input focus: 2px coffee-brown outline
Label: text-sm, font-medium, text-dark
Error text: text-sm, error color
```

#### Mobile Navigation
```
Bottom nav height: 60px
Icon size: 24px
Active: coffee-brown background
Inactive: text-light color
```

### Design Principles
1. **Mobile-first** - Design for small screens, enhance for large
2. **Touch-friendly** - 48px minimum touch targets
3. **High contrast** - Ensure readability (WCAG AA minimum)
4. **Consistent spacing** - Use 8px grid system
5. **Minimal cognitive load** - One primary action per screen
6. **Instant feedback** - Loading states, toasts, animations
7. **Forgiving UX** - Easy undo, clear confirmations

---

## 🗺️ Version Roadmap

### Version 0.1 - "The Order Taker" (MVP) ✅ In Progress
**Timeline:** 2-3 weeks  
**Status:** Specification Complete, Development Starting

**Core Features:**
- ✅ Table-based order management
- ✅ Menu display with categories
- ✅ Order taking (waiter mobile interface)
- ✅ Bill generation with GST (rate configurable, 5% by default)
- ✅ Receipt printing (80mm thermal)
- ✅ Split payment support
- ✅ Basic menu management (admin)
- ✅ Order history (today's orders)
- ✅ Admin authentication

**User Stories:**
- As a waiter, I can select a table and add items to an order
- As a waiter, I can view all active orders
- As a cashier, I can generate a bill and collect payment
- As an admin, I can manage menu items
- As an admin, I can view order history

**Success Criteria:**
- Waiter can take orders on phone without errors
- Bills print correctly with GST details
- Admin can manage menu effectively
- System runs reliably on local network

---

### Version 0.2 - "The Inventory Tracker"
**Timeline:** 1 week  
**Status:** Planned

**New Features:**
- 📦 Ingredient inventory management
- 📦 Recipe definitions (dish → ingredients mapping)
- 📦 Automatic stock deduction on orders
- 📦 Low-stock alerts
- 📦 Manual inventory adjustments
- 📦 Wastage tracking

**Technical Additions:**
- New tables: `inventory_items`, `recipe_ingredients`, `inventory_transactions`
- Background tasks for stock alerts
- Inventory audit log

**Success Criteria:**
- No unexpected stockouts of key ingredients
- Accurate inventory tracking
- Clear visibility of stock levels

---

### Version 0.3 - "The Business Intelligence"
**Timeline:** 1-2 weeks
**Status:** Planned

**New Features:**
- 📊 Sales reports (daily/weekly/monthly)
- 📊 Popular items dashboard
- 📊 GST reports for filing
- 📊 Data export (Excel/CSV)
- 📊 Profit margin tracking
- 📊 Peak hours analysis
- 🍜 Menu item modifiers/add-ons system (optional enhancement)

**Technical Additions:**
- Pandas for data analysis
- Chart library (recharts)
- Report scheduling
- Export functionality
- Modifiers database schema (if implementing add-ons)

**Success Criteria:**
- Owner makes data-driven menu decisions
- Easy GST filing with generated reports
- Clear visibility into business performance
- (Optional) Customers can customize orders with add-ons

---

### Version 0.4 - "The Team Collaboration"
**Timeline:** 2 weeks  
**Status:** Planned

**New Features:**
- 👥 Multiple user accounts
- 👥 Role-based permissions (Admin, Manager, Waiter, Kitchen)
- 👥 Table management (assign servers)
- 👥 Order status workflow (Placed → Preparing → Ready → Served)
- 👥 Kitchen display system (KDS)
- 👥 Real-time order updates (WebSocket)

**Technical Additions:**
- User management system
- Permission middleware
- WebSocket for real-time updates
- Kitchen display interface

**Success Criteria:**
- Multiple staff members can use system simultaneously
- Clear order workflow from taking to serving
- Kitchen sees orders in real-time

---

### Version 0.5 - "The Data Fortress"
**Timeline:** 1 week  
**Status:** Planned

**New Features:**
- 💾 Automated daily backups
- 💾 Data export/import functionality
- 💾 Audit logs (who did what, when)
- 💾 Data validation and integrity checks
- 💾 Recovery tools
- 💾 Database optimization

**Technical Additions:**
- Backup scheduler
- Audit logging middleware
- Data validation layer
- Optional PostgreSQL migration path

**Success Criteria:**
- System recovers from laptop failure
- Complete audit trail for accountability
- Data integrity maintained

---

### Version 1.0 - "The Production Release"
**Timeline:** 1 week  
**Status:** Planned

**Focus:** Polish & Hardening
- 🔒 Security audit and fixes
- ⚡ Performance optimization
- 🐛 Bug fixes and stability
- 📚 User documentation
- 🎓 Training materials
- ⚙️ Configuration UI (change settings without .env)
- 🌐 Offline mode (graceful degradation)

**Success Criteria:**
- Zero critical bugs in production
- System runs stable for 30+ days
- Complete documentation
- Staff fully trained

---

### Version 1.5 - "The AI Assistant" 🤖 (Learning Project)
**Timeline:** 2 weeks  
**Status:** Concept

**New Features:**
- 🤖 MCP server integration
- 🤖 Natural language queries via Claude
- 🤖 AI-generated insights
- 🤖 Automated report generation
- 🤖 Voice-to-order (optional)
- 🤖 Predictive analytics

**MCP Tools to Expose:**
```
📊 get_daily_sales(date)
📦 check_inventory_status(threshold)
📈 generate_custom_report(criteria)
🔍 search_orders(filters)
💡 suggest_menu_optimizations()
📋 create_purchase_order(items)
🎯 predict_demand(date, items)
```

**Learning Objectives:**
- Deep understanding of MCP protocol
- LLM integration patterns
- Tool design for AI consumption
- JSON-RPC communication

**Success Criteria:**
- Owner can ask Claude business questions
- AI provides accurate answers from cafe data
- Useful insights generated automatically

---

### Version 2.0 - "The Cloud Hybrid" (Future)
**Timeline:** TBD  
**Status:** Concept

**New Features:**
- ☁️ Optional cloud backup
- 📱 Mobile app for owners (React Native)
- 🏪 Multi-location support
- 👤 Customer loyalty program
- 🛒 Online ordering integration
- 🔄 Data synchronization
- 📡 API for third-party integrations

**Technical Changes:**
- PostgreSQL migration
- Cloud sync service
- API gateway
- Mobile app development

**Success Criteria:**
- Scales to multiple cafe locations
- Owner can monitor business remotely
- Maintains local-first architecture

---

## 💾 Data Model

### Core Entities

#### Menu Items
```
Entity: MenuItem
Purpose: Represents a dish/item that can be ordered
Lifecycle: Created by admin, soft-deleted when removed
Key Attributes:
- name: Display name
- price: Integer (in paise)
- category: Category name
- is_available: Soft delete flag
```

#### Orders
```
Entity: Order
Purpose: Represents a customer's order at a table
Lifecycle: Active → Paid or Canceled
Key Attributes:
- order_number: Unique identifier (ORD-YYYYMMDD-####)
- table_number: Table location
- status: active | paid | canceled
- total_amount: Calculated total with GST
Key Rules:
- One active order per table at a time
- Cannot be deleted, only canceled
- Totals calculated server-side
```

#### Order Items
```
Entity: OrderItem
Purpose: Line item in an order (quantity of a menu item)
Lifecycle: Created with order, snapshots menu item details
Key Attributes:
- menu_item_name: Snapshot of name
- unit_price: Snapshot of price
- quantity: Integer quantity
Key Rules:
- Stores snapshot to preserve historical data
- Quantity always positive integer
```

#### Payments
```
Entity: Payment
Purpose: Records a payment made for an order
Lifecycle: Created when payment collected
Key Attributes:
- payment_method: upi | cash | card
- amount: Integer (in paise)
Key Rules:
- Multiple payments can exist for one order (split payment)
- Sum of payments must equal order total
```

#### Categories
```
Entity: Category
Purpose: Grouping for menu items
Lifecycle: Created by admin, soft-deleted if unused
Key Attributes:
- name: Unique category name
Key Rules:
- Cannot delete if menu items reference it
```

### Relationships
```
Order (1) ──── (many) OrderItem
OrderItem (many) ──── (1) MenuItem
Order (1) ──── (many) Payment
MenuItem (many) ──── (1) Category
```

### Data Integrity Rules
1. **Referential Integrity:** Foreign keys enforced
2. **Price Consistency:** Prices stored as integers (paise)
3. **Historical Preservation:** Snapshots prevent data loss
4. **Soft Deletes:** Never hard delete transactional data
5. **Audit Trail:** Track created_at, updated_at timestamps
6. **Validation:** All inputs validated via Pydantic schemas

---

## 👤 User Roles & Permissions

### Role Hierarchy
```
Admin (Full Access)
  ├── Manager (Most Access)
  │     ├── Waiter (Order Access)
  │     └── Kitchen (Kitchen Access)
  └── Guest (Read-Only)
```

### Role Definitions

#### Admin/Owner
**Access Level:** Full system access  
**Responsibilities:** System management, business oversight  
**Permissions:**
- ✅ All waiter permissions
- ✅ Generate bills and collect payments
- ✅ Manage menu items (CRUD)
- ✅ Manage categories (CRUD)
- ✅ Edit/cancel any order
- ✅ View complete order history
- ✅ Access analytics and reports
- ✅ Manage user accounts (v0.4+)
- ✅ Configure system settings
- ✅ View audit logs (v0.5+)

**Authentication:**
- v0.1: Hardcoded credentials (admin/changeme123)
- v0.4+: Database-managed user account

---

#### Waiter/Staff (v0.1)
**Access Level:** Order management only  
**Responsibilities:** Take orders, serve customers  
**Permissions:**
- ✅ View table status
- ✅ Create new orders
- ✅ Add items to existing orders
- ✅ View all active orders (read-only)
- ❌ Cannot generate bills
- ❌ Cannot edit menu
- ❌ Cannot cancel orders
- ❌ Cannot view order history

**Authentication:**
- v0.1: No login required (open access)
- v0.4+: Individual login credentials

---

#### Manager (v0.4+)
**Access Level:** Operations management  
**Responsibilities:** Day-to-day operations, staff supervision  
**Permissions:**
- ✅ All waiter permissions
- ✅ Generate bills and collect payments
- ✅ Edit/cancel orders
- ✅ View order history
- ✅ View reports
- ❌ Cannot manage menu
- ❌ Cannot manage users
- ❌ Cannot change system settings

---

#### Kitchen Staff (v0.4+)
**Access Level:** Kitchen operations only  
**Responsibilities:** Prepare orders  
**Permissions:**
- ✅ View incoming orders (KDS)
- ✅ Mark order status (Preparing, Ready)
- ❌ Cannot view prices
- ❌ Cannot cancel orders
- ❌ Cannot access billing

---

### Permission Matrix

| Feature | Admin | Manager | Waiter | Kitchen |
|---------|-------|---------|--------|---------|
| Take orders | ✅ | ✅ | ✅ | ❌ |
| View active orders | ✅ | ✅ | ✅ | ✅ |
| Edit orders | ✅ | ✅ | ❌ | ❌ |
| Cancel orders | ✅ | ✅ | ❌ | ❌ |
| Generate bills | ✅ | ✅ | ❌ | ❌ |
| Manage menu | ✅ | ❌ | ❌ | ❌ |
| View history | ✅ | ✅ | ❌ | ❌ |
| View reports | ✅ | ✅ | ❌ | ❌ |
| Manage users | ✅ | ❌ | ❌ | ❌ |
| System settings | ✅ | ❌ | ❌ | ❌ |

---

## 🚀 Deployment Strategy

### Hosting Architecture
**Model:** Self-hosted, on-premises  
**Hardware:** Customer's laptop (Windows/Ubuntu)  
**Network:** Local WiFi (cafe broadband)  
**Access:** Internal network only (no internet exposure)

### Deployment Components
```
Cafe Laptop (Primary Server)
├── Backend (FastAPI on port 8000)
├── Frontend (Vite dev server on port 5173)
├── Database (SQLite file: restaurant.db)
└── Thermal Printer (USB connected)

WiFi Network (Local)
├── Staff Phones (Access frontend via IP)
├── Reception Computer (Admin access)
└── Future: Kitchen Display Tablet
```

### Network Configuration
```
Laptop IP: 192.168.1.X (DHCP or static)
Backend: http://192.168.1.X:8000
Frontend: http://192.168.1.X:5173

Access from phones:
http://192.168.1.X:5173
(Bookmark this URL)
```

### Installation Process
1. **Prerequisites Setup**
   - Install Python 3.11+
   - Install Node.js 18+
   - Connect thermal printer, set as default

2. **Application Setup**
   - Clone/extract project files
   - Configure .env with cafe details
   - Install backend dependencies
   - Install frontend dependencies
   - Initialize database
   - Seed menu data

3. **Service Startup**
   - Start backend (uvicorn)
   - Start frontend (vite dev)
   - Verify network access from phones

4. **Ongoing Operations**
   - Services run continuously during business hours
   - Restart services on laptop reboot (via startup script)
   - Daily backups (automated in v0.5+)

### Backup Strategy
**v0.1-0.4:** Manual backups
- Copy `restaurant.db` file daily
- Store on external USB drive
- Keep last 7 days of backups

**v0.5+:** Automated backups
- Scheduled daily at 2 AM
- Automatic file rotation
- Backup to multiple locations
- Recovery testing monthly

### Disaster Recovery
**Scenarios:**
1. **Laptop failure:** Restore from backup to new laptop
2. **Database corruption:** Restore from last backup
3. **Power outage:** System restarts automatically
4. **Network failure:** Graceful degradation (show error, retry)
5. **Printer failure:** Manual receipt writing until replacement

**Recovery Time Objective (RTO):** 4 hours  
**Recovery Point Objective (RPO):** 24 hours (daily backups)

---

## 📊 Success Metrics

### v0.1 Success Criteria
**Operational Metrics:**
- ✅ Orders taken digitally (target: 95%+ of orders)
- ✅ Bills printed correctly (target: 100% accuracy)
- ✅ System uptime during business hours (target: 99%+)
- ✅ Average order taking time (target: <2 minutes)

**User Satisfaction:**
- ✅ Staff comfortable using system (target: 4/5 rating)
- ✅ Zero critical bugs in first week
- ✅ Owner satisfied with basic functionality

**Technical Metrics:**
- ✅ Response time <500ms for API calls
- ✅ Zero data loss incidents
- ✅ Successful receipt prints (target: 95%+)

### v0.2-1.0 Success Criteria
**Business Impact:**
- 📦 Reduced food wastage (target: 20% reduction)
- 📊 Data-driven menu decisions (track item performance)
- ⏱️ Faster service times (target: 10% improvement)
- 💰 Accurate GST filing (zero errors)

**System Maturity:**
- 🔒 Zero security incidents
- 💾 Successful disaster recovery tests
- 👥 Multiple staff trained and using system
- 📈 System handles peak hours without issues

### v1.5+ Success Criteria (Learning Goals)
**Technical Learning:**
- 🤖 Functional MCP server implementation
- 🤖 AI provides accurate business insights
- 🤖 Natural language queries work reliably
- 📚 Deep understanding of LLM integration patterns

---

## ⚠️ Known Constraints

### Technical Constraints
1. **Single Server Architecture**
   - One laptop runs entire system
   - No redundancy in v0.1
   - Laptop failure = system downtime

2. **Local Network Only**
   - No remote access
   - Requires cafe WiFi
   - No internet backup (initially)

3. **SQLite Limitations**
   - Single writer at a time
   - No built-in replication
   - File-based (not client-server)

4. **No Built-in Redundancy**
   - Single point of failure
   - Manual backups initially
   - No automatic failover

### Business Constraints
1. **Learning Curve**
   - Staff needs training
   - Resistance to change possible
   - Initial slowdown expected

2. **Hardware Dependency**
   - Laptop must be reliable
   - Printer must be maintained
   - Network must be stable

3. **Limited Budget**
   - Optimize for existing hardware
   - Avoid expensive third-party services
   - Minimize operational costs

### Regulatory Constraints
1. **GST Compliance**
   - Must follow Indian GST rules
   - Receipt format requirements
   - Tax filing requirements

2. **Data Privacy**
   - Customer data must be protected
   - No unauthorized access
   - Comply with data protection laws

### Accepted Trade-offs (v0.1)
✅ **Accepted for MVP:**
- Hardcoded admin credentials
- No audit logging
- No rate limiting
- No HTTPS (local network)
- Limited error recovery
- Basic security measures

❌ **Will Address Later:**
- Multi-user authentication (v0.4)
- Advanced security (v1.0)
- Cloud backup (v2.0)
- High availability (v2.0)

---

## 🔮 Future Considerations

### Potential Enhancements (Post v2.0)

#### Customer-Facing Features
- 📱 QR code menu viewing
- 🛎️ Digital table calling
- ⭐ Customer feedback system
- 🎁 Loyalty program
- 📧 Email receipts
- 💳 Online payment integration
- 🍜 **Menu Item Modifiers/Add-ons System** (v0.3+)
  - Customizable menu items with paid add-ons
  - Examples: Extra soup (+₹20), Extra noodles (+₹30), Double cheese (+₹40)
  - Size variations (Small/Medium/Large with different prices)
  - Free customizations (Spice level: Mild/Medium/Hot)
  - Modifier groups with min/max selections
  - Clear display of add-on prices in cart and receipt

#### Operational Features
- 📊 Real-time dashboard
- 📈 Predictive inventory
- 🔔 Staff performance tracking
- 📅 Reservation system
- 🚚 Supplier management
- 💼 Employee scheduling

#### Technical Enhancements
- 🔐 Advanced security (2FA, encryption)
- 🌐 Progressive Web App (PWA)
- 🔄 Real-time sync across devices
- 📡 API for third-party integration
- 🤖 Advanced AI features
- 📱 Native mobile apps

#### Scaling Considerations
- 🏪 Multi-location support
- ☁️ Cloud-hybrid architecture
- 🔁 Data replication
- 🚀 Microservices architecture
- 🐳 Containerization (Docker)
- ☸️ Kubernetes orchestration

### Technology Evolution Path
```
v0.1: SQLite + Local
  ↓
v0.5: SQLite + Backups
  ↓
v1.0: SQLite + Optimization
  ↓
v2.0: PostgreSQL + Optional Cloud
  ↓
v3.0: Microservices + Multi-location
```

---

## 🍜 Feature Deep Dive: Menu Item Modifiers & Add-ons

**Planned Version:** v0.3 or v0.4
**Priority:** Medium-High (Revenue enhancement feature)
**Status:** Design phase

### Business Value
This feature enables customers to customize their orders with add-ons and modifiers, driving additional revenue through upselling while providing better customer experience.

**Revenue Impact:**
- Average order value increase: 15-25% (industry standard)
- Common upsells: Extra ingredients, size upgrades, premium toppings
- Example: Ramen with extra soup (+₹20) and extra noodles (+₹30) = +₹50 per order

### Use Cases

#### 1. Paid Add-ons (Ramen Example)
```
Base Item: Chicken Ramen (₹300)

Available Add-ons:
├── Extra Soup (+₹20)
├── Extra Noodles (+₹30)
├── Extra Vegetables (+₹25)
└── Add Egg (+₹15)

Customer selects: Extra Soup + Extra Noodles
Final Price: ₹350
```

#### 2. Size Variations (Coffee Example)
```
Item: Filter Coffee

Size Options:
├── Small (₹30)  [base price]
├── Medium (+₹10) = ₹40
└── Large (+₹20) = ₹50

Customer selects: Large
Final Price: ₹50
```

#### 3. Free Customizations (Spice Level)
```
Item: Masala Dosa (₹80)

Customizations (No extra cost):
├── Spice Level: Mild / Medium / Hot
└── Extra Chutney: Yes / No

Customer selects: Hot, Extra Chutney
Final Price: ₹80 (unchanged)
```

#### 4. Multiple Modifier Groups
```
Item: Pizza (₹200)

Modifier Groups:
1. Size (Required, select 1):
   ├── Regular (included)
   └── Large (+₹50)

2. Toppings (Optional, select up to 3):
   ├── Extra Cheese (+₹40)
   ├── Olives (+₹30)
   ├── Mushrooms (+₹35)
   └── Paneer (+₹50)

3. Crust (Required, select 1):
   ├── Regular (included)
   ├── Thin (+₹20)
   └── Stuffed (+₹60)

Customer selects: Large, Extra Cheese, Regular crust
Final Price: ₹200 + ₹50 + ₹40 = ₹290
```

### Technical Architecture

#### Database Schema

```sql
-- Modifier Groups (e.g., "Ramen Add-ons", "Pizza Toppings")
CREATE TABLE modifier_groups (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    min_selections INTEGER DEFAULT 0,  -- 0 = optional
    max_selections INTEGER DEFAULT 1,  -- 1 = single choice, NULL = unlimited
    is_required BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    updated_at DATETIME
);

-- Link modifier groups to menu items
CREATE TABLE menu_item_modifier_groups (
    id INTEGER PRIMARY KEY,
    menu_item_id INTEGER NOT NULL,
    modifier_group_id INTEGER NOT NULL,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id),
    FOREIGN KEY (modifier_group_id) REFERENCES modifier_groups(id)
);

-- Individual modifiers (e.g., "Extra Soup +₹20")
CREATE TABLE modifiers (
    id INTEGER PRIMARY KEY,
    modifier_group_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    price_adjustment INTEGER NOT NULL,  -- In paise, can be 0 for free options
    is_available BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (modifier_group_id) REFERENCES modifier_groups(id)
);

-- Track which modifiers were selected for each order item
CREATE TABLE order_item_modifiers (
    id INTEGER PRIMARY KEY,
    order_item_id INTEGER NOT NULL,
    modifier_id INTEGER NOT NULL,
    modifier_name TEXT NOT NULL,      -- Snapshot for history
    price_adjustment INTEGER NOT NULL, -- Snapshot for history
    quantity INTEGER DEFAULT 1,        -- Some modifiers can be added multiple times
    FOREIGN KEY (order_item_id) REFERENCES order_items(id),
    FOREIGN KEY (modifier_id) REFERENCES modifiers(id)
);
```

#### API Endpoints

```
GET  /api/menu/{item_id}/modifiers
     → Returns all modifier groups and options for a menu item

POST /api/modifiers/groups  🔒 (Admin)
     → Create new modifier group

POST /api/modifiers  🔒 (Admin)
     → Add modifier to a group

PUT  /api/modifiers/{id}  🔒 (Admin)
     → Update modifier (price, availability)

DELETE /api/modifiers/{id}  🔒 (Admin)
     → Soft delete modifier

POST /api/orders
     → Enhanced to accept modifiers in items array
     Request body:
     {
       "table_number": 5,
       "items": [
         {
           "menu_item_id": 1,
           "quantity": 2,
           "modifiers": [
             {"modifier_id": 10, "quantity": 1},  // Extra Soup
             {"modifier_id": 11, "quantity": 1}   // Extra Noodles
           ]
         }
       ]
     }
```

#### Frontend Components

**New Components Needed:**
1. `ModifierSelector.tsx` - Modal/drawer for selecting modifiers
2. `ModifierGroup.tsx` - Single modifier group UI
3. `ModifierOption.tsx` - Individual modifier checkbox/radio
4. `ModifierSummary.tsx` - Display selected modifiers in cart
5. `ModifierManagement.tsx` - Admin interface for managing modifiers

**UX Flow:**
```
1. User adds item to cart
2. If item has modifiers → Show ModifierSelector modal
3. Display each modifier group with constraints
4. Calculate total price in real-time
5. Add to cart with selected modifiers
6. Show modifiers in cart drawer
7. Allow editing modifiers from cart
```

#### Receipt Display

```
================================
    Lily Cafe by Mary's Kitchen
================================

Order #: ORD-20241030-0001
Table: 5

--------------------------------
Item          Qty  Price   Amt
--------------------------------
Chicken Ramen  1   300.00  300.00
  + Extra Soup      20.00   20.00
  + Extra Noodles   30.00   30.00
                           ------
                           350.00

Filter Coffee  1    50.00   50.00
  (Large)
--------------------------------
              Subtotal:  400.00
             CGST(2.5%):   10.00
             SGST(2.5%):   10.00
--------------------------------
         TOTAL:  420.00
================================
```

### Implementation Phases

#### Phase 1: Core Infrastructure (Week 1)
- [ ] Database schema implementation
- [ ] Backend API endpoints
- [ ] Basic CRUD operations for modifiers

#### Phase 2: Waiter Interface (Week 2)
- [ ] Modifier selection UI (mobile-optimized)
- [ ] Real-time price calculation
- [ ] Cart integration with modifiers
- [ ] Order placement with modifiers

#### Phase 3: Admin Interface (Week 3)
- [ ] Modifier management page
- [ ] Create/edit modifier groups
- [ ] Assign modifiers to menu items
- [ ] Pricing configuration

#### Phase 4: Polish & Testing (Week 4)
- [ ] Receipt printing with modifiers
- [ ] Order history with modifiers
- [ ] Analytics for modifier performance
- [ ] Staff training materials

### Workaround for v0.1 (Current Version)

Until the modifiers system is implemented, use separate menu items:

**Instead of:**
- Ramen (₹300) with add-ons

**Create:**
- Chicken Ramen - Regular (₹300)
- Chicken Ramen - Extra Soup (₹320)
- Chicken Ramen - Extra Noodles (₹330)
- Chicken Ramen - Extra Both (₹350)

**Pros:**
- ✅ Works with current system
- ✅ No code changes needed
- ✅ Simple for staff

**Cons:**
- ❌ Menu becomes cluttered
- ❌ Limited combinations
- ❌ Hard to track add-on performance
- ❌ Difficult to manage pricing

### Success Metrics

**Business Metrics:**
- Average order value increase: Target +15%
- Modifier attachment rate: Target 30% of orders
- Most popular add-ons tracked
- Revenue from add-ons tracked separately

**Technical Metrics:**
- Modifier selection time: <30 seconds
- Order accuracy with modifiers: 99%+
- No performance degradation on order page

**User Satisfaction:**
- Staff comfortable using modifier system
- Customer complaints about incorrect modifiers: <1%
- Kitchen receives clear modifier instructions

### Future Enhancements (Post-Launch)

1. **Conditional Modifiers**
   - Show certain modifiers only if other modifiers selected
   - Example: "Extra Cheese" only if "Cheese" is selected

2. **Default Selections**
   - Pre-select common choices (e.g., "Medium" spice level)
   - Customer can change if desired

3. **Combo Pricing**
   - Discount when multiple add-ons selected
   - Example: "Extra Soup + Extra Noodles" bundle at ₹45 instead of ₹50

4. **Ingredient-Based Pricing**
   - Link to inventory system (v0.2)
   - Adjust prices based on ingredient costs

5. **AI Recommendations** (v1.5+)
   - Suggest popular add-on combinations
   - "Customers who ordered this also added..."

---

## 🎓 Learning Objectives

### For Developer (You)

#### Python & Backend Skills
- ✅ FastAPI framework mastery
- ✅ SQLAlchemy ORM patterns
- ✅ Pydantic validation
- ✅ JWT authentication
- ✅ RESTful API design
- ✅ Database modeling
- ✅ PDF generation
- ✅ Background tasks

#### Frontend Skills
- ✅ React + TypeScript patterns
- ✅ TanStack Query (data fetching)
- ✅ Mobile-first design
- ✅ Responsive layouts
- ✅ State management
- ✅ Performance optimization

#### Advanced Topics (v1.5+)
- 🤖 MCP protocol implementation
- 🤖 LLM integration patterns
- 🤖 JSON-RPC communication
- 🤖 Tool design for AI
- 🤖 Prompt engineering
- 🤖 AI-powered analytics

#### DevOps & Deployment
- 🚀 Local deployment strategies
- 🚀 Environment management
- 🚀 Backup and recovery
- 🚀 System monitoring
- 🚀 User training

---

## 📚 Reference Documents

### Project Documentation
1. **Technical Specification (v0.1)** - `lily-cafe-pos-v0.1-technical-spec.md`
   - Detailed API endpoints
   - Database schema
   - User flows
   - Component specs
   - Testing checklist

2. **Master Project Document (This File)** - `lily-cafe-pos-master-project-document.md`
   - High-level overview
   - Architecture decisions
   - Version roadmap
   - Design system

### External Resources
1. **FastAPI Documentation** - https://fastapi.tiangulo.com
2. **React Documentation** - https://react.dev
3. **SQLAlchemy Documentation** - https://docs.sqlalchemy.org
4. **Tailwind CSS** - https://tailwindcss.com
5. **MCP Documentation** - https://modelcontextprotocol.io
6. **Indian GST Rules** - https://gst.gov.in

---

## 🔄 Document Maintenance

### Change Log
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-10-30 | Initial creation | [Your Name] |
| | | | |
| | | | |

### Review Schedule
- **After each version release:** Update roadmap, mark completed features
- **Monthly:** Review constraints and technical decisions
- **Quarterly:** Assess success metrics and adjust priorities
- **Annually:** Major architecture review

### Document Ownership
**Primary Owner:** [Your Name]  
**Stakeholders:** Lily Cafe Owner, Development Team  
**Last Review:** October 30, 2024  
**Next Review:** After v0.1 completion

---

## ✅ Quick Reference Checklist

### Starting Development on a New Version
- [ ] Review this master document
- [ ] Review previous version's technical spec
- [ ] Review user feedback from previous version
- [ ] Check version roadmap for planned features
- [ ] Review data model changes needed
- [ ] Plan API endpoint additions
- [ ] Design new UI components
- [ ] Update testing checklist
- [ ] Create version-specific technical spec

### Before Version Release
- [ ] All features from roadmap implemented
- [ ] Testing checklist completed
- [ ] Documentation updated
- [ ] Deployment guide updated
- [ ] User training materials ready
- [ ] Backup strategy verified
- [ ] Performance benchmarks met
- [ ] Security review completed

### After Version Release
- [ ] Collect user feedback
- [ ] Monitor for bugs
- [ ] Update master document
- [ ] Document lessons learned
- [ ] Plan next version features
- [ ] Update success metrics
- [ ] Archive version artifacts

---

## 📞 Contact & Support

**Project Lead:** [Your Name]  
**Email:** [Your Email]  
**Phone:** [Your Phone]  
**Repository:** [Git URL]

**Client Contact:**  
**Cafe:** Lily Cafe by Mary's Kitchen  
**Owner:** [Owner Name]  
**Phone:** [Owner Phone]  
**Location:** [Cafe Address]

---

## 🎯 Core Principles (Never Compromise)

1. **Data Privacy First** - All customer data stays local, no external transmission
2. **Reliability Over Features** - A working system beats a feature-rich broken one
3. **User Experience Matters** - Staff should love using it, not tolerate it
4. **Incremental Value** - Ship working software early and often
5. **Learn While Building** - Balance client needs with skill development
6. **Document Everything** - Future you will thank present you
7. **Test Thoroughly** - Bugs in production hurt the business
8. **Keep It Simple** - Complexity is the enemy of reliability

---

**Document Version:** 1.0  
**Status:** Active  
**Classification:** Internal - Project Reference  
**Last Updated:** October 30, 2024

---

*This document serves as the single source of truth for the Lily Cafe POS System project. All technical decisions, architectural choices, and project direction should reference this document. When in doubt, refer back to the core principles and business requirements outlined here.*
