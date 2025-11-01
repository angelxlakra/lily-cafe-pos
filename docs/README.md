# Lily Cafe POS System

A self-hosted Point of Sale system for Lily Cafe by Mary's Kitchen. Built with modern web technologies for fast, reliable, and offline-capable order management.

## <� Version 0.1 - "The Order Taker"

Core order management and billing system for small-medium cafes.

### Features

- **Table-based order management** - Track orders by table number
- **Menu display with categories** - Organized menu for easy browsing
- **Order taking** - Mobile-friendly waiter interface
- **Bill generation with GST** - Automatic GST calculation (18%)
- **Receipt printing** - 80mm thermal printer support
- **Split payment support** - UPI, Cash, Card
- **Basic menu management** - Admin CRUD operations
- **Order history** - View today's orders
- **Admin authentication** - JWT-based security

## <� Tech Stack

### Backend
- **Python 3.11+** - Modern Python with type hints
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Modern ORM with async support
- **Pydantic V2** - Data validation using Python type annotations
- **SQLite** - Local database (no external dependencies)
- **UV** - Fast Python package manager

### Frontend
- **Vite** - Lightning-fast build tool
- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS V4** - CSS-first utility framework
- **React Router** - Client-side routing
- **TanStack Query** - Powerful async state management
- **Axios** - HTTP client

## =� Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **Node.js 18 or higher** - [Download](https://nodejs.org/)
- **UV** - Python package manager
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

## =� Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd lily-cafe-pos

# Copy environment variables
cp .env.example .env

# Edit .env with your details (optional for development)
nano .env
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies with UV (creates .venv automatically)
uv sync

# Initialize database and seed sample data
uv run python -m scripts.seed_data

# Start the backend server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
Interactive API docs at `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
# Open a new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 4. Using the Startup Script (Recommended)

For easier development, use the provided startup script:

```bash
# Make it executable (first time only)
chmod +x run.sh

# Run both backend and frontend
./run.sh
```

## =� Accessing from Mobile Devices

To access the POS system from mobile devices on your local network:

1. Find your computer's local IP address:
   ```bash
   # macOS/Linux
   ipconfig getifaddr en0

   # Or use
   ifconfig | grep "inet "
   ```

2. Update `.env` file with your local IP:
   ```
   CORS_ORIGINS=http://localhost:5173,http://192.168.1.100:5173
   ```

3. Access from mobile browser:
   ```
   http://192.168.1.100:5173
   ```

## =' Development Commands

### Backend

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Run backend server
uv run uvicorn app.main:app --reload

# Seed database with sample data
uv run python -m scripts.seed_data

# Run tests (when implemented)
uv run pytest

# Format code with black
uv run black backend/

# Lint with ruff
uv run ruff check backend/
```

### Frontend

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Project Structure

```
lily-cafe-pos/
├── backend/                      # FastAPI backend
│   ├── app/                      # Main application package
│   │   ├── api/                  # API endpoints
│   │   │   ├── v1/               # API version 1
│   │   │   │   ├── endpoints/    # Route handlers
│   │   │   │   │   ├── auth.py           # Authentication endpoints
│   │   │   │   │   ├── categories.py     # Category endpoints
│   │   │   │   │   ├── menu.py           # Menu endpoints
│   │   │   │   │   ├── orders.py         # Order & payment endpoints
│   │   │   │   │   └── admin.py          # Admin endpoints
│   │   │   │   └── router.py             # Main API router
│   │   │   └── deps.py                    # Shared dependencies
│   │   ├── core/                 # Core functionality
│   │   │   ├── config.py                  # Settings & configuration
│   │   │   └── security.py                # JWT & password hashing
│   │   ├── db/                   # Database layer
│   │   │   ├── session.py                 # Database connection & session
│   │   │   └── base.py                    # Model imports for Alembic
│   │   ├── models/               # SQLAlchemy models
│   │   │   └── models.py                  # Database models
│   │   ├── schemas/              # Pydantic schemas
│   │   │   └── schemas.py                 # Request/response schemas
│   │   ├── crud/                 # CRUD operations
│   │   │   └── crud.py                    # Database operations
│   │   ├── utils/                # Utilities
│   │   │   └── pdf_generator.py           # Receipt generation
│   │   └── main.py                        # FastAPI app entry point
│   ├── scripts/                  # Utility scripts
│   │   └── seed_data.py                   # Database seeding script
│   └── pyproject.toml            # Python dependencies (UV)
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── pages/                # Page components
│   │   ├── api/                  # API client
│   │   ├── types/                # TypeScript types
│   │   ├── hooks/                # Custom React hooks
│   │   ├── utils/                # Utility functions
│   │   ├── App.tsx               # Main app component
│   │   ├── main.tsx              # Entry point
│   │   └── index.css             # Tailwind CSS v4 styles
│   ├── package.json              # Node dependencies
│   ├── vite.config.ts            # Vite configuration
│   └── tsconfig.json             # TypeScript config
│
├── docs/                         # Documentation
│   ├── master-project-document.md
│   ├── v0.1-technical-spec.md
│   └── UV-QUICK-REFERENCE.md
│
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
└── run.sh                        # Startup script
```

## = Default Credentials

- **Admin Username**: `admin`
- **Admin Password**: `changeme123`

**� Important**: Change these credentials in production by updating the `.env` file.

## =� Database

The application uses SQLite for local data storage. The database file (`restaurant.db`) is created automatically in the backend directory.

### Database Schema

- **categories** - Menu item categories
- **menu_items** - Available items for ordering
- **orders** - Customer orders
- **order_items** - Individual items in orders (with snapshots)
- **payments** - Payment records (supports split payments)

## <� Design System

### Color Palette

- **Coffee Brown**: `#6F4E37` - Primary brand color
- **Coffee Dark**: `#4A3728` - Hover states
- **Coffee Light**: `#A0826D` - Accents
- **Cream**: `#F5E6D3` - Backgrounds
- **Lily Green**: `#8B9D83` - Secondary brand color

### Typography

- **Font Family**: Inter, system-ui, sans-serif
- **Touch Targets**: Minimum 48px (3rem) for mobile-friendly interaction

## =� API Documentation

Once the backend is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

- `POST /api/v1/auth/login` - Admin login
- `GET /api/v1/menu` - List menu items
- `POST /api/v1/orders` - Create new order
- `GET /api/v1/orders` - List orders
- `POST /api/v1/orders/{id}/payments` - Add payment

## = Security Notes

- All prices stored in paise (smallest currency unit) to avoid float precision issues
- JWT tokens expire after 24 hours (configurable)
- Admin authentication required for sensitive operations
- CORS configured for local network access only

## = Troubleshooting

### Backend won't start

- Ensure Python 3.11+ is installed: `python --version`
- Check if port 8000 is available: `lsof -i :8000`
- Verify UV is installed: `uv --version`
- Try: `uv sync --reinstall`

### Frontend won't start

- Ensure Node.js 18+ is installed: `node --version`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check if port 5173 is available: `lsof -i :5173`

### Database issues

- Delete the database file and reseed: `rm backend/restaurant.db && uv run python -m backend.seed_data`

## =� Roadmap

### v0.2 - Kitchen Display System
- Kitchen order management
- Order status tracking
- Timer functionality

### v0.3 - Reports & Analytics
- Daily/weekly/monthly reports
- Revenue analytics
- Popular items tracking

### v1.0 - Full Production Release
- Multi-location support
- Advanced inventory management
- Employee management
- Complete audit logs

## =� License

MIT License - See LICENSE file for details

## > Contributing

This is a private project for Lily Cafe. For questions or issues, contact the development team.

## =� Support

For support, please contact:
- **Email**: info@lilycafe.com
- **Phone**: +91-1234567890

---

Built with d for Lily Cafe by Mary's Kitchen
