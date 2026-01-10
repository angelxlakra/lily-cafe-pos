# Analytics Dashboard Setup Guide

This guide explains how to set up the Analytics Dashboard powered by Thesys C1.

## Features

The analytics dashboard provides:

- **Revenue Analytics**: Total revenue, order count, average order value, revenue trends
- **Product Performance**: Top-selling products, revenue by category
- **Order Statistics**: Order counts by status, peak hours analysis
- **Payment Method Breakdown**: Revenue split by payment methods (Cash, UPI, Card)
- **Time Range Filters**: Real-time, historical trends, custom date ranges, comparative analysis
- **Thesys C1 Integration**: (Coming soon) Natural language queries for data exploration

## Backend Setup

### 1. Install Dependencies

Dependencies are already installed via `uv`. The OpenAI SDK is used for Thesys C1 integration.

### 2. Configure Thesys API Key

1. Get your API key from [https://thesys.dev](https://thesys.dev)
2. Create a `.env` file in the `backend` directory (or copy from `.env.example`):

```bash
cd backend
cp .env.example .env
```

3. Add your Thesys API key to the `.env` file:

```env
THESYS_API_KEY=your-thesys-api-key-here
```

### 3. Start the Backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

The analytics endpoints will be available at:
- `GET /api/v1/analytics/revenue` - Revenue analytics
- `GET /api/v1/analytics/products` - Product performance
- `GET /api/v1/analytics/orders` - Order statistics
- `POST /api/v1/analytics/query` - Thesys C1 conversational queries

## Frontend Setup

### 1. Install Dependencies

Dependencies are already installed via npm, including:
- `@thesysai/genui-sdk` - Thesys C1 React components
- `recharts` - Charting library
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

## Thesys C1 Conversational Analytics (Coming Soon)

The next update will include full Thesys C1 integration, allowing you to:

- Ask natural language questions: "Show me sales trends for last month"
- Get dynamic visualizations: "Which products perform best on weekends?"
- Compare periods: "Compare revenue from last week vs this week"
- Drill down into data: "Show me all orders over ₹1000"

## Troubleshooting

### Backend Issues

**Error: "Thesys API key not configured"**
- Solution: Add `THESYS_API_KEY` to your `.env` file

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
- **AI Integration**: OpenAI SDK → Thesys C1 API

### Frontend
- **Framework**: React 18 + TypeScript
- **State Management**: TanStack Query (React Query)
- **Charts**: Recharts library
- **UI Components**: Custom components with Tailwind CSS

## Future Enhancements

- [ ] Full Thesys C1 conversational interface
- [ ] Export analytics to PDF/Excel
- [ ] Advanced filters (by waiter, table, category)
- [ ] Predictive analytics and forecasting
- [ ] Email scheduled reports
- [ ] Dashboard customization (drag-and-drop widgets)

## Support

For issues or questions:
1. Check the main README.md
2. Review API documentation at `/docs` (FastAPI auto-generated)
3. Consult Thesys documentation at [https://docs.thesys.dev](https://docs.thesys.dev)
