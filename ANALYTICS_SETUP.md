# Analytics Dashboard Setup Guide

This guide explains how to set up the Analytics Dashboard and the Ask screen.

## Features

The analytics dashboard provides:

- **Revenue Analytics**: Total revenue, order count, average order value, revenue trends
- **Product Performance**: Top-selling products, revenue by category
- **Order Statistics**: Order counts by status, peak hours analysis
- **Payment Method Breakdown**: Revenue split by payment methods (Cash, UPI, Card)
- **Time Range Filters**: Real-time, historical trends, custom date ranges, comparative analysis
- **Ask**: plain-language questions (English, Hindi, Hinglish) answered by fixed reports

## Backend Setup

### 1. Install Dependencies

Dependencies are already installed via `uv`. The OpenAI SDK is used by Ask.

### 2. Configure the Ask model key (optional)

The dashboard works without it. Ask needs an OpenAI API key:

1. Create a `.env` file in the `backend` directory (or copy from `.env.example`):

```bash
cd backend
cp .env.example .env
```

2. Add the key (and, optionally, a model — the default is `gpt-5.6-luna`):

```env
OPENAI_API_KEY=sk-...
ASK_MODEL=gpt-5.6-luna
```

Without a key, the Ask screen shows "Ask isn't set up on this server yet".

### 3. Start the Backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

The analytics endpoints will be available at:
- `GET /api/v1/analytics/revenue` - Revenue analytics
- `GET /api/v1/analytics/products` - Product performance
- `GET /api/v1/analytics/orders` - Order statistics
- `POST /api/v1/ask` - Ask: a question in, a report out (owner login only)

## Frontend Setup

### 1. Install Dependencies

Dependencies are already installed via npm, including:
- `recharts` - Charting library (with shadcn's chart wrapper in `src/components/ui/chart.tsx`)
- `date-fns` - Date manipulation

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

### 3. Access the Analytics Dashboard

1. Log in to the admin portal at `/login`
2. Navigate to **Analytics** in the sidebar
3. Use the date range picker to filter data by time period

## Using the Analytics Dashboard

### Date Range Selection

The dashboard includes a date picker with quick filters:
- **Today**: View today's metrics
- **Yesterday**: Previous day's performance
- **Last 7 Days**: Weekly trends
- **Last 30 Days**: Monthly overview
- **Custom Range**: Select specific start and end dates

### Metrics Displayed

#### Revenue Card
- Total revenue for selected period
- Percentage change vs previous period
- Color-coded trend indicator

#### Total Orders Card
- Completed orders count
- Active orders indicator

#### Average Order Value Card
- Mean revenue per order
- Calculated from completed orders only

#### Peak Hour Card
- Busiest hour of the day
- Number of orders during peak time

#### Revenue Trend Chart
- Line chart showing daily revenue
- Interactive tooltips with exact values

#### Top Products Table
- Best-selling items by quantity
- Revenue contribution per product
- Limited to top 10 products

#### Revenue by Category Chart
- Bar chart comparing category performance
- Useful for identifying profitable categories

#### Payment Method Breakdown
- Visual breakdown of payment types
- Shows revenue split between Cash, UPI, and Card

## API Query Parameters

All analytics endpoints support the following optional parameters:

- `start_date` (ISO 8601 datetime): Filter data from this date onwards
- `end_date` (ISO 8601 datetime): Filter data up to this date
- `limit` (integer): Limit number of results (products endpoint only)

Example:
```
GET /api/v1/analytics/revenue?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

## Ask

On the Analytics page, switch to **Ask Questions**. The owner types a question and gets one of a fixed set of reports back, with the period it covers shown on the card:

- "how were sales last week" · "which dish performed best since August"
- "which day was the highest revenue day since May" · "everything about July"
- "kal ka cash counter" · "august mein kaunsi dish sabse zyada biki"
- Follow-ups keep context: "how did masala tea do this month" → "and last month?"

How it stays trustworthy: the model only decides *which report, which dish, which period*. Every figure is computed by the backend from the same queries as the dashboard; the model never produces a number. If a question can't be answered by any report, it says so and suggests the nearest one.

To check routing quality against the real model on the phrasings your owners use:

```bash
cd backend && uv run python scripts/ask_eval.py
```

To load a local database with eight weeks of demo orders for trying it out:

```bash
cd backend && DATABASE_URL=sqlite:///./demo.db uv run python -m scripts.seed_demo_orders
```

## Troubleshooting

### Backend Issues

**Ask says "isn't set up on this server yet"**
- Solution: Add `OPENAI_API_KEY` to `backend/.env`

**Error: "No module named 'openai'"**
- Solution: Run `cd backend && uv add openai`

### Frontend Issues

**Charts not displaying**
- Solution: Ensure `recharts` is installed: `cd frontend && npm install recharts`

**No data showing**
- Solution: Verify you have orders in the database with PAID status

**Blank analytics page**
- Solution: Check browser console for errors, verify backend is running

## Architecture

### Backend
- **Framework**: FastAPI with SQLAlchemy ORM
- **Analytics Engine**: Custom SQL queries with aggregations
- **Ask**: OpenAI SDK (GPT-5.6 Luna, strict structured output) → report registry in `app/ask`

### Frontend
- **Framework**: React 18 + TypeScript
- **State Management**: TanStack Query (React Query)
- **Charts**: Recharts library
- **UI Components**: Custom components with Tailwind CSS

## Future Enhancements

- [ ] Export analytics to PDF/Excel
- [ ] Advanced filters (by waiter, table, category)
- [ ] Predictive analytics and forecasting
- [ ] Email scheduled reports
- [ ] Dashboard customization (drag-and-drop widgets)

## Support

For issues or questions:
1. Check the main README.md
2. Review API documentation at `/docs` (FastAPI auto-generated)
