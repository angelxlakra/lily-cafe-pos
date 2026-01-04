# Thesys C1 Generative UI - Quick Integration Guide

## What is Thesys C1?

Thesys C1 is a Generative UI API that creates dynamic, interactive visualizations from natural language queries. Instead of building fixed dashboards, you can ask questions like "Show me top products this week" and get auto-generated charts and tables.

## Quick Setup (5 minutes)

### 1. Get Your API Key

Sign up at [https://thesys.dev](https://thesys.dev) and get your API key.

### 2. Add API Key to Backend

```bash
cd backend
echo "THESYS_API_KEY=your-api-key-here" >> .env
```

### 3. Install Frontend SDK

Already installed: `@thesysai/genui-sdk@^0.7.15`

### 4. Add C1Component to Analytics Page

Edit `/frontend/src/pages/AnalyticsPage.tsx`:

```typescript
// Add import at the top
import { C1Component } from '@thesysai/genui-sdk';

// Replace the "Coming Soon" section with:
{/* Thesys C1 Conversational Interface */}
<div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
  <h2 className="font-heading text-xl mb-4" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
    Ask Questions About Your Data
  </h2>

  <C1Component
    apiKey={import.meta.env.VITE_THESYS_API_KEY}
    apiEndpoint="http://localhost:8000/api/v1/analytics/query"
    placeholder="Ask a question about your analytics... (e.g., 'Show me revenue trends for last week')"
    theme={theme === 'dark' ? 'dark' : 'light'}
  />
</div>
```

### 5. Add Environment Variable to Frontend

Create `/frontend/.env`:

```bash
VITE_THESYS_API_KEY=your-api-key-here
```

### 6. Test It

```bash
# Terminal 1 - Backend
cd backend
uv run uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Navigate to Analytics page and ask:
- "Show me top selling products"
- "What's the revenue trend for this month?"
- "Which payment method is most popular?"

## Advanced: Custom Context

To give C1 more context about your data, update the backend endpoint:

```python
# backend/app/api/v1/endpoints/analytics.py

@router.post("/query")
async def conversational_query(
    request: C1QueryRequest,
    db: Session = Depends(get_db)
):
    client = get_c1_client()

    # Add context about your data schema
    context = """
    Available data:
    - Orders: id, total_amount, status, payment_method, created_at
    - OrderItems: product_name, quantity, price, category
    - Categories: Beverages, Food, Noodles, Desserts
    - Payment Methods: cash, upi, card

    Example queries:
    - "Show revenue by category"
    - "Compare cash vs UPI payments"
    - "Top 5 products by revenue"
    """

    response = client.chat.completions.create(
        model="c1",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": request.query}
        ]
    )

    return C1QueryResponse(
        query=request.query,
        result=response.choices[0].message.content
    )
```

## Styling Tips

The C1Component accepts these props:

```typescript
<C1Component
  apiKey="..."
  apiEndpoint="..."
  placeholder="Custom placeholder text"
  theme="light" | "dark"  // Matches your app theme
  className="custom-class"
  style={{ /* custom styles */ }}
/>
```

## Troubleshooting

**Error: "API key not configured"**
- Make sure `THESYS_API_KEY` is in `backend/.env`
- Restart backend server after adding key

**Error: "VITE_THESYS_API_KEY is undefined"**
- Add `VITE_THESYS_API_KEY` to `frontend/.env`
- Restart frontend dev server
- Vite only loads env vars starting with `VITE_`

**C1Component not rendering**
- Check browser console for errors
- Verify backend `/api/v1/analytics/query` endpoint is running
- Test endpoint manually: `curl -X POST http://localhost:8000/api/v1/analytics/query -H "Content-Type: application/json" -d '{"query":"test"}'`

**Rate limiting**
- Free tier: 100 requests/day
- Upgrade at [https://thesys.dev/pricing](https://thesys.dev/pricing)

## Next Steps

1. **Add more context**: Include sample data, common queries, metric definitions
2. **Enable caching**: Cache common queries to reduce API calls
3. **Add query suggestions**: Show example questions to users
4. **Track usage**: Monitor which questions users ask most
5. **Custom styling**: Match C1Component to your brand colors

## Resources

- [Thesys C1 Documentation](https://docs.thesys.dev)
- [React SDK Reference](https://docs.thesys.dev/sdk/react)
- [Example Queries](https://docs.thesys.dev/examples)
