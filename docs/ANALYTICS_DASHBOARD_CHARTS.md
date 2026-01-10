# Analytics Dashboard Chart Recommendations

## Overview

This document outlines advanced analytics and visualization recommendations for the Lily Cafe POS system based on the available data models and current backend capabilities.

## Table of Contents

- [Data Sources Summary](#data-sources-summary)
- [Chart Type Recommendations](#chart-type-recommendations)
- [Dashboard Layouts](#dashboard-layouts)
- [Implementation Libraries](#implementation-libraries)
- [Backend Data Considerations](#backend-data-considerations)

---

## Data Sources Summary

### Available Data Models

Our backend provides rich data across multiple domains:

**Order & Payment Data:**
- Complete order history with timestamps
- Table assignments and customer names
- Order status lifecycle (Active/Paid/Canceled)
- Item-level details with quantities and served status
- Parcel/dine-in classification
- Payment method tracking (Cash/UPI/Card)
- Split payment support
- GST breakdown

**Product Data:**
- Menu items with categories
- Vegetarian/non-vegetarian classification
- Beverage vs. food classification
- Price history (via order snapshots)
- Availability status

**Inventory Data:**
- Current stock levels and minimum thresholds
- Cost per unit for valuation
- Transaction history (Purchase/Usage/Adjustment)
- Full audit trail with timestamps and staff attribution

**Cash Management:**
- Daily opening/closing balances
- Denomination counts
- Expected vs. actual variance tracking
- Staff verification records

**Time-Series Capabilities:**
- All timestamps in UTC
- Supports hourly, daily, weekly, monthly analysis
- Created/updated tracking for change history

---

## Chart Type Recommendations

### 🔥 Heatmaps

#### 1. Time-based Order Heatmap
**Visual Type:** 2D Heatmap (Hour × Day of Week)

**Data Points:**
- X-axis: Day of week (Monday-Sunday)
- Y-axis: Hour of day (0-23)
- Color intensity: Order count or revenue

**Backend Query:**
```sql
GROUP BY
  EXTRACT(DOW FROM created_at) as day_of_week,
  EXTRACT(HOUR FROM created_at) as hour
```

**Business Value:**
- Identify peak business hours at a glance
- Staff scheduling optimization
- Inventory preparation timing
- Promotional campaign timing

**Example Use Case:** "We see high activity Tuesday-Thursday 7-9 AM and 6-8 PM - this guides our coffee prep and staffing."

---

#### 2. Calendar Heatmap
**Visual Type:** Calendar Grid Heatmap

**Data Points:**
- Each cell: One day
- Color intensity: Daily revenue or order count
- Layout: Weeks × Days like GitHub contributions

**Backend Query:**
```sql
SELECT DATE(created_at) as date,
       SUM(total_amount) as revenue
FROM orders
WHERE status = 'PAID'
GROUP BY DATE(created_at)
```

**Business Value:**
- Seasonal pattern recognition
- Holiday impact analysis
- Week-over-week comparison
- Marketing campaign effectiveness

**Example Use Case:** "Calendar shows revenue dip every Sunday and spike on 1st and 15th (salary days)."

---

### 🌳 Treemaps

#### 3. Category & Product Revenue Treemap
**Visual Type:** Hierarchical Treemap

**Data Hierarchy:**
- Level 1: Categories (Coffee, Tea, Snacks, etc.)
- Level 2: Menu items within categories
- Size: Revenue contribution
- Color: Profit margin or growth rate

**Backend Query:**
```sql
SELECT c.name as category,
       m.name as item,
       SUM(oi.subtotal) as revenue,
       SUM(oi.quantity) as quantity_sold
FROM order_items oi
JOIN menu_items m ON oi.menu_item_id = m.id
JOIN categories c ON m.category_id = c.id
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'PAID'
GROUP BY c.name, m.name
```

**Business Value:**
- Visual hierarchy of revenue sources
- Identify category dominance
- Spot underperforming menu items
- Quick assessment of product portfolio

**Example Use Case:** "Coffee is 45% of revenue, but within Coffee, only 3 items make 80% of that."

---

#### 4. Inventory Cost Distribution Treemap
**Visual Type:** Hierarchical Treemap

**Data Hierarchy:**
- Level 1: Inventory categories
- Level 2: Individual inventory items
- Size: Cost valuation (current_quantity × cost_per_unit)
- Color: Stock status (green=healthy, yellow=low, red=critical)

**Backend Query:**
```sql
SELECT ic.name as category,
       ii.name as item,
       (ii.current_quantity * ii.cost_per_unit) as total_value,
       ii.is_low_stock
FROM inventory_items ii
JOIN inventory_categories ic ON ii.category_id = ic.id
WHERE ii.is_active = true
```

**Business Value:**
- Capital allocation visibility
- Identify overstocked items
- Inventory optimization opportunities
- Budget planning

**Example Use Case:** "60% of our inventory value is locked in coffee beans and milk."

---

### 📈 Area Charts (Stacked/Stream)

#### 5. Revenue Composition Over Time
**Visual Type:** Stacked Area Chart

**Data Points:**
- X-axis: Time (days/weeks)
- Y-axis: Revenue (cumulative)
- Layers: Categories or payment methods
- Colors: Distinct per layer

**Backend Query:**
```sql
SELECT DATE(o.created_at) as date,
       c.name as category,
       SUM(oi.subtotal) as revenue
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN menu_items m ON oi.menu_item_id = m.id
JOIN categories c ON m.category_id = c.id
WHERE o.status = 'PAID'
GROUP BY DATE(o.created_at), c.name
ORDER BY date
```

**Business Value:**
- Revenue mix evolution over time
- Category growth trends
- Payment method adoption rates
- Seasonal product performance

**Example Use Case:** "UPI payments grew from 20% to 60% of revenue in 3 months."

---

#### 6. Order Status Flow (Stream Graph)
**Visual Type:** Stream Graph / Stacked Area

**Data Points:**
- X-axis: Time (hourly for single day, daily for range)
- Y-axis: Order count
- Layers: Active, Paid, Canceled
- Flow: Shows status transitions visually

**Backend Query:**
```sql
SELECT DATE(created_at) as date,
       status,
       COUNT(*) as count
FROM orders
GROUP BY DATE(created_at), status
ORDER BY date
```

**Business Value:**
- Order fulfillment patterns
- Cancellation rate trends
- Operational efficiency tracking
- Bottleneck identification

**Example Use Case:** "Active orders spike at 7 PM but take 2 hours to clear - need more kitchen staff."

---

### 🎯 Funnel Charts

#### 7. Order Completion Funnel
**Visual Type:** Funnel Chart

**Stages:**
1. Orders Created (100%)
2. Orders Active (% in progress)
3. Orders Completed (% paid)
4. Drop-off: Orders Canceled (% lost)

**Backend Query:**
```sql
SELECT
  COUNT(*) as total_orders,
  SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active,
  SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) as completed,
  SUM(CASE WHEN status = 'CANCELED' THEN 1 ELSE 0 END) as canceled
FROM orders
WHERE created_at >= :start_date AND created_at <= :end_date
```

**Conversion Metrics:**
- Activation rate: Active / Total
- Completion rate: Paid / Total
- Cancellation rate: Canceled / Total
- Success rate: Paid / (Paid + Canceled)

**Business Value:**
- Identify drop-off points
- Measure operational efficiency
- Track improvement over time
- Set performance benchmarks

**Example Use Case:** "5% cancellation rate - mostly from table 12 (problematic customer?)."

---

### 🫧 Bubble Charts

#### 8. Product Performance Matrix
**Visual Type:** Bubble Chart (Scatter with Size)

**Axes:**
- X-axis: Quantity sold (volume)
- Y-axis: Total revenue (value)
- Bubble size: Profit margin or AOV
- Color: Category

**Quadrants:**
- Top-right: **Stars** (high volume + high revenue)
- Top-left: **Premium** (low volume + high revenue)
- Bottom-right: **Volume drivers** (high volume + low revenue)
- Bottom-left: **Underperformers** (low volume + low revenue)

**Backend Query:**
```sql
SELECT m.name,
       c.name as category,
       SUM(oi.quantity) as quantity_sold,
       SUM(oi.subtotal) as total_revenue,
       AVG(oi.unit_price) as avg_price
FROM order_items oi
JOIN menu_items m ON oi.menu_item_id = m.id
JOIN categories c ON m.category_id = c.id
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'PAID'
GROUP BY m.id, m.name, c.name
```

**Business Value:**
- Portfolio analysis
- Pricing strategy validation
- Menu optimization decisions
- Marketing focus areas

**Example Use Case:** "Masala Chai is a star (high volume + high revenue), but Iced Matcha is premium (low volume but high margin)."

---

#### 9. Payment Method Analysis Bubble
**Visual Type:** Bubble Chart

**Axes:**
- X-axis: Average transaction value
- Y-axis: Transaction count
- Bubble size: Total revenue
- Color: Payment method (Cash/UPI/Card)

**Backend Query:**
```sql
SELECT p.payment_method,
       COUNT(*) as transaction_count,
       AVG(p.amount) as avg_amount,
       SUM(p.amount) as total_revenue
FROM payments p
JOIN orders o ON p.order_id = o.id
WHERE o.status = 'PAID'
GROUP BY p.payment_method
```

**Business Value:**
- Payment preference by ticket size
- Optimal payment infrastructure
- Fee optimization (UPI/Card charges)
- Customer behavior insights

**Example Use Case:** "Cash dominates low-value orders (<₹200), but UPI dominates high-value (>₹500)."

---

### 🕸️ Radar/Spider Charts

#### 10. Category Performance Score
**Visual Type:** Radar Chart (Multi-axis)

**Metrics (Normalized 0-100):**
- Revenue contribution
- Order frequency
- Average order value
- Item variety (count)
- Vegetarian ratio
- Availability rate

**Backend Query (requires normalization):**
```sql
WITH category_metrics AS (
  SELECT c.name,
         SUM(oi.subtotal) as revenue,
         COUNT(DISTINCT o.id) as order_count,
         AVG(oi.subtotal) as avg_order_value,
         COUNT(DISTINCT m.id) as item_count,
         AVG(CASE WHEN m.is_vegetarian THEN 1 ELSE 0 END) as veg_ratio,
         AVG(CASE WHEN m.is_available THEN 1 ELSE 0 END) as availability
  FROM categories c
  JOIN menu_items m ON c.id = m.category_id
  LEFT JOIN order_items oi ON m.id = oi.menu_item_id
  LEFT JOIN orders o ON oi.order_id = o.id AND o.status = 'PAID'
  GROUP BY c.name
)
SELECT * FROM category_metrics
```

**Business Value:**
- Holistic category assessment
- Identify strengths and weaknesses
- Balanced portfolio development
- Strategic decision making

**Example Use Case:** "Coffee scores high on revenue and frequency but low on variety - opportunity to expand."

---

#### 11. Day-of-Week Performance Radar
**Visual Type:** Radar Chart

**Metrics per Day:**
- Revenue (normalized)
- Order count (normalized)
- Average order value (normalized)
- Payment diversity score
- Parcel order ratio

**Backend Query:**
```sql
SELECT
  EXTRACT(DOW FROM o.created_at) as day_of_week,
  SUM(o.total_amount) as revenue,
  COUNT(*) as order_count,
  AVG(o.total_amount) as avg_order_value,
  COUNT(DISTINCT p.payment_method) as payment_diversity,
  AVG(CASE WHEN oi.is_parcel THEN 1 ELSE 0 END) as parcel_ratio
FROM orders o
LEFT JOIN payments p ON o.id = p.order_id
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.status = 'PAID'
GROUP BY EXTRACT(DOW FROM o.created_at)
```

**Business Value:**
- Multi-dimensional day comparison
- Identify truly "best" days
- Optimize operations per day
- Marketing calendar planning

**Example Use Case:** "Friday has highest revenue but lowest AOV - it's high volume, low margin."

---

### 💧 Sankey Diagrams

#### 12. Order Flow Diagram
**Visual Type:** Sankey (Flow Diagram)

**Flow Path:**
Category → Menu Item → Payment Method → Revenue

**Nodes:**
- Source: Categories (Coffee, Tea, etc.)
- Intermediate 1: Top menu items
- Intermediate 2: Payment methods
- Destination: Revenue buckets

**Backend Query:**
```sql
SELECT c.name as category,
       m.name as menu_item,
       p.payment_method,
       SUM(oi.subtotal) as revenue
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN menu_items m ON oi.menu_item_id = m.id
JOIN categories c ON m.category_id = c.id
JOIN payments p ON o.id = p.order_id
WHERE o.status = 'PAID'
GROUP BY c.name, m.name, p.payment_method
```

**Business Value:**
- Revenue path visualization
- Payment preference by product
- Cross-sell opportunities
- Product-payment correlations

**Example Use Case:** "Coffee → Cappuccino → UPI accounts for ₹50K (20% of total revenue flow)."

---

#### 13. Inventory Usage Flow
**Visual Type:** Sankey Diagram

**Flow Path:**
Inventory Category → Items → Transaction Type → Quantity Change

**Nodes:**
- Source: Inventory categories
- Intermediate: Inventory items
- Destination: Purchase/Usage/Adjustment

**Backend Query:**
```sql
SELECT ic.name as category,
       ii.name as item,
       it.transaction_type,
       SUM(ABS(it.quantity)) as total_quantity
FROM inventory_transactions it
JOIN inventory_items ii ON it.item_id = ii.id
JOIN inventory_categories ic ON ii.category_id = ic.id
WHERE it.created_at >= :start_date AND it.created_at <= :end_date
GROUP BY ic.name, ii.name, it.transaction_type
```

**Business Value:**
- Inventory movement patterns
- High-usage item identification
- Purchase optimization
- Waste detection (adjustments)

**Example Use Case:** "Milk shows high purchase but also high adjustment (waste) - need better storage."

---

### 📦 Box & Whisker Plots

#### 14. Order Value Distribution
**Visual Type:** Box Plot (Multiple Distributions)

**Grouping:**
- By day of week
- By payment method
- By table number
- By time period

**Statistical Metrics:**
- Minimum
- Q1 (25th percentile)
- Median (Q2)
- Q3 (75th percentile)
- Maximum
- Outliers

**Backend Query:**
```sql
SELECT
  EXTRACT(DOW FROM created_at) as group_key,
  total_amount
FROM orders
WHERE status = 'PAID'
ORDER BY group_key, total_amount
```

**Business Value:**
- Understand spending patterns
- Identify customer segments
- Detect anomalies/fraud
- Pricing strategy insights
- Variance analysis

**Example Use Case:** "Monday orders are consistently low (₹100-200), but weekends have huge variance (₹50-1500) - different customer types."

---

#### 15. Item Quantity Distribution
**Visual Type:** Box Plot

**Grouping:** By menu item

**Data:** Quantity per order (from order_items)

**Backend Query:**
```sql
SELECT m.name,
       oi.quantity
FROM order_items oi
JOIN menu_items m ON oi.menu_item_id = m.id
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'PAID'
ORDER BY m.name
```

**Business Value:**
- Bulk order identification
- Single-serve vs. sharing items
- Inventory planning
- Portion size validation

**Example Use Case:** "Samosas typically ordered in 3-6 qty, but chai is always 1-2 - guides inventory prep."

---

### 📊 Waterfall Charts

#### 16. Daily Revenue Breakdown
**Visual Type:** Waterfall Chart (Sequential Changes)

**Flow:**
1. Start: ₹0
2. +Coffee revenue
3. +Tea revenue
4. +Snacks revenue
5. +Meals revenue
6. -GST amount
7. End: Net revenue

**Backend Query:**
```sql
SELECT c.name as category,
       SUM(oi.subtotal) as revenue
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN menu_items m ON oi.menu_item_id = m.id
JOIN categories c ON m.category_id = c.id
WHERE o.status = 'PAID'
  AND DATE(o.created_at) = :target_date
GROUP BY c.name

UNION ALL

SELECT 'GST' as category,
       -SUM(gst_amount) as revenue
FROM orders
WHERE status = 'PAID'
  AND DATE(created_at) = :target_date
```

**Business Value:**
- Revenue composition clarity
- Category contribution visualization
- Tax impact understanding
- Sequential story-telling

**Example Use Case:** "Started at ₹0, Coffee added ₹12K, Tea ₹8K, Snacks ₹5K, minus ₹1.25K GST = ₹23.75K net."

---

#### 17. Inventory Valuation Changes
**Visual Type:** Waterfall Chart

**Flow:**
1. Start: Opening stock value
2. +Purchases
3. -Usage
4. ±Adjustments
5. End: Closing stock value

**Backend Query:**
```sql
WITH daily_transactions AS (
  SELECT
    transaction_type,
    SUM(quantity * ii.cost_per_unit) as value_change
  FROM inventory_transactions it
  JOIN inventory_items ii ON it.item_id = ii.id
  WHERE DATE(it.created_at) = :target_date
  GROUP BY transaction_type
)
SELECT * FROM daily_transactions
```

**Business Value:**
- Inventory value tracking
- Waste/loss identification
- Purchase impact visualization
- Stock valuation audit

**Example Use Case:** "Started with ₹25K stock, bought ₹10K, used ₹8K, lost ₹500 to waste = ₹26.5K closing."

---

### 🎨 Polar/Radial Charts

#### 18. Hourly Order Distribution (Polar Area)
**Visual Type:** Polar Area Chart (24-hour clock)

**Data Points:**
- 24 segments (0-23 hours)
- Radius: Order count or revenue
- Color: Intensity gradient

**Backend Query:**
```sql
SELECT EXTRACT(HOUR FROM created_at) as hour,
       COUNT(*) as order_count,
       SUM(total_amount) as revenue
FROM orders
WHERE status = 'PAID'
  AND DATE(created_at) = :target_date
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour
```

**Business Value:**
- Intuitive 24-hour rhythm visualization
- Peak hour identification
- Staffing schedule optimization
- Marketing timing

**Example Use Case:** "Visual 'clock' shows clear spikes at 8 AM, 1 PM, and 7 PM - our three rush periods."

---

#### 19. Payment Method Mix (Radial Bar)
**Visual Type:** Radial Bar Chart

**Data Points:**
- Segments: Cash, UPI, Card
- Radius/Height: Transaction amount
- Arc length: Transaction count

**Backend Query:**
```sql
SELECT payment_method,
       COUNT(*) as transaction_count,
       SUM(amount) as total_amount
FROM payments p
JOIN orders o ON p.order_id = o.id
WHERE o.status = 'PAID'
  AND DATE(o.created_at) >= :start_date
GROUP BY payment_method
```

**Business Value:**
- Payment preference visualization
- Infrastructure planning
- Fee impact assessment
- Customer behavior insights

**Example Use Case:** "Radial chart shows UPI dominates both count and value - can negotiate better UPI rates."

---

### 🎰 Gauge Charts

#### 20. Real-time Performance Gauges
**Visual Type:** Gauge/Speedometer

**Gauge Types:**

**A. Daily Revenue Gauge**
- Min: ₹0
- Target: Daily average or goal
- Max: Best day revenue
- Current: Today's revenue
- Zones: Red (<50%), Yellow (50-80%), Green (>80%)

**B. Order Count Gauge**
- Similar structure for order volume

**C. Average Order Value Gauge**
- Track AOV against target

**D. Inventory Fill Rate Gauge**
- 0-100% stock level
- Red zone: <30%
- Yellow: 30-70%
- Green: >70%

**Backend Queries:**
```sql
-- Today's revenue vs. average
SELECT
  SUM(total_amount) as today_revenue,
  (SELECT AVG(daily_rev) FROM (
    SELECT DATE(created_at), SUM(total_amount) as daily_rev
    FROM orders WHERE status = 'PAID'
    GROUP BY DATE(created_at)
  ) subq) as avg_revenue,
  (SELECT MAX(daily_rev) FROM (
    SELECT DATE(created_at), SUM(total_amount) as daily_rev
    FROM orders WHERE status = 'PAID'
    GROUP BY DATE(created_at)
  ) subq) as max_revenue
FROM orders
WHERE status = 'PAID' AND DATE(created_at) = CURRENT_DATE
```

**Business Value:**
- Real-time performance monitoring
- Goal tracking
- Motivational visualization
- Quick status assessment

**Example Use Case:** "Revenue gauge shows 65% of target at 3 PM - need to push evening sales."

---

### 📅 Gantt-style Timeline

#### 21. Order Timeline View
**Visual Type:** Horizontal Timeline/Gantt

**Data Points:**
- Y-axis: Order numbers
- X-axis: Time
- Bars: Order lifecycle
  - Start: created_at
  - Milestone: items served
  - End: payment received
- Color: Table number or status

**Backend Query:**
```sql
SELECT o.order_number,
       o.table_number,
       o.created_at,
       MIN(CASE WHEN oi.is_served THEN oi.updated_at END) as first_served,
       MAX(CASE WHEN oi.is_served THEN oi.updated_at END) as last_served,
       p.created_at as paid_at
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN payments p ON o.id = p.order_id
WHERE DATE(o.created_at) = :target_date
GROUP BY o.id, o.order_number, o.table_number, o.created_at, p.created_at
ORDER BY o.created_at
```

**Business Value:**
- Kitchen efficiency analysis
- Service time tracking
- Bottleneck identification
- Staff performance monitoring

**Example Use Case:** "Orders from Table 5 consistently take 45 mins from order to payment - investigate waiter or kitchen issue."

---

### 🌊 Violin Plots

#### 22. Price Distribution by Category
**Visual Type:** Violin Plot (Distribution + Box Plot)

**Data Points:**
- X-axis: Categories
- Y-axis: Menu item prices
- Width: Density at each price point
- Inner box: Median, quartiles

**Backend Query:**
```sql
SELECT c.name as category,
       m.price
FROM menu_items m
JOIN categories c ON m.category_id = c.id
WHERE m.is_available = true
ORDER BY c.name
```

**Business Value:**
- Price range visualization
- Pricing strategy assessment
- Menu balance evaluation
- Gap analysis

**Example Use Case:** "Coffee category has narrow price range (₹60-120), but Meals has wide distribution (₹80-400) - diverse portfolio."

---

### 🔄 Chord Diagrams

#### 23. Category Co-occurrence
**Visual Type:** Chord Diagram (Circular Flow)

**Data Points:**
- Nodes: Categories (around circle)
- Chords: Co-occurrence strength
- Width: Frequency of pairing
- Color: Source category

**Backend Query:**
```sql
SELECT
  c1.name as category1,
  c2.name as category2,
  COUNT(*) as co_occurrence
FROM order_items oi1
JOIN order_items oi2 ON oi1.order_id = oi2.order_id
  AND oi1.id < oi2.id
JOIN menu_items m1 ON oi1.menu_item_id = m1.id
JOIN menu_items m2 ON oi2.menu_item_id = m2.id
JOIN categories c1 ON m1.category_id = c1.id
JOIN categories c2 ON m2.category_id = c2.id
JOIN orders o ON oi1.order_id = o.id
WHERE o.status = 'PAID'
  AND c1.id != c2.id
GROUP BY c1.name, c2.name
```

**Business Value:**
- Cross-sell opportunities
- Combo meal design
- Upsell strategy
- Customer behavior patterns

**Example Use Case:** "Strong chord between Coffee and Snacks (70% co-occurrence) - create combo deals."

---

## Dashboard Layouts

### Dashboard 1: Operations Command Center

**Purpose:** Real-time operational monitoring

**Widgets:**
1. **Gauges Row** (Top)
   - Today's Revenue vs. Target
   - Order Count vs. Average
   - Active Orders (real-time)

2. **Heatmap** (Center-left)
   - Hour × Day order heatmap
   - Current hour highlighted

3. **Funnel** (Center-right)
   - Order status progression
   - Conversion rates

4. **Polar Chart** (Bottom-left)
   - 24-hour order distribution

5. **Timeline** (Bottom-right)
   - Active orders lifecycle
   - Bottleneck alerts

**Refresh:** Every 30 seconds (real-time monitoring)

---

### Dashboard 2: Product Analytics Deep Dive

**Purpose:** Menu performance and optimization

**Widgets:**
1. **Treemap** (Top-left, large)
   - Category/Product revenue hierarchy

2. **Bubble Chart** (Top-right)
   - Product performance matrix
   - Quadrant analysis overlay

3. **Radar Chart** (Bottom-left)
   - Category performance scores

4. **Chord Diagram** (Bottom-center)
   - Category co-occurrence patterns

5. **Violin Plot** (Bottom-right)
   - Price distribution by category

**Refresh:** Daily or on-demand

---

### Dashboard 3: Financial Intelligence

**Purpose:** Revenue analysis and financial health

**Widgets:**
1. **KPI Cards** (Top row)
   - Total Revenue
   - Average Order Value
   - Transaction Count
   - Revenue Growth %

2. **Waterfall Chart** (Center-left)
   - Daily revenue breakdown by category

3. **Sankey Diagram** (Center-right)
   - Revenue flow (Category → Product → Payment)

4. **Stacked Area Chart** (Bottom, full-width)
   - Revenue composition over time (30 days)
   - Category layers

5. **Box Plot** (Sidebar)
   - Order value distribution by payment method

**Refresh:** Hourly or daily

---

### Dashboard 4: Inventory & Supply Chain

**Purpose:** Inventory management and cost control

**Widgets:**
1. **Gauges Row** (Top)
   - Stock fill rate
   - Low stock items count
   - Inventory value

2. **Treemap** (Center-left, large)
   - Inventory cost distribution

3. **Waterfall Chart** (Center-right)
   - Daily inventory valuation changes

4. **Sankey Diagram** (Bottom-left)
   - Inventory usage flow

5. **Box Plot** (Bottom-right)
   - Usage pattern distribution by item

**Refresh:** Real-time or hourly

---

### Dashboard 5: Customer Insights

**Purpose:** Customer behavior and preferences

**Widgets:**
1. **Calendar Heatmap** (Top, full-width)
   - Daily revenue over months
   - Seasonal patterns

2. **Bubble Chart** (Center-left)
   - Payment method analysis

3. **Radar Chart** (Center-right)
   - Day-of-week performance

4. **Box Plot** (Bottom-left)
   - Order value distribution by day

5. **Chord Diagram** (Bottom-right)
   - Product pairing patterns

**Refresh:** Daily

---

## Implementation Libraries

### Recommended Libraries for React/TypeScript

#### 1. **Apache ECharts** (Highly Recommended)
**Pros:**
- Most comprehensive chart library
- Beautiful, professional visualizations
- Excellent performance with large datasets
- Built-in support for heatmaps, sankey, treemap, radar, etc.
- Great documentation
- Active development

**Cons:**
- Larger bundle size
- Configuration can be verbose

**Best For:** Complex charts (Sankey, Treemap, Chord, Heatmap)

**Installation:**
```bash
npm install echarts echarts-for-react
```

**Example:**
```typescript
import ReactECharts from 'echarts-for-react';

const option = {
  tooltip: {},
  series: [{
    type: 'treemap',
    data: treeData
  }]
};

<ReactECharts option={option} />
```

---

#### 2. **Recharts** (Good for Standard Charts)
**Pros:**
- React-native API (JSX components)
- Great for bar, line, pie, area charts
- Easy to learn
- Good documentation
- Smaller bundle size

**Cons:**
- Limited advanced chart types
- Less performant with very large datasets

**Best For:** Standard charts (Bar, Line, Pie, Area)

**Installation:**
```bash
npm install recharts
```

**Example:**
```typescript
import { BarChart, Bar, XAxis, YAxis } from 'recharts';

<BarChart data={data}>
  <Bar dataKey="revenue" fill="#8884d8" />
  <XAxis dataKey="category" />
  <YAxis />
</BarChart>
```

---

#### 3. **Nivo** (Beautiful & Modern)
**Pros:**
- Modern, beautiful design
- Great animations
- Good variety of charts
- Responsive by default
- TypeScript support

**Cons:**
- Smaller community than Recharts/ECharts
- Some charts require tweaking for customization

**Best For:** Heatmaps, Sankey, Treemap, Radial charts

**Installation:**
```bash
npm install @nivo/core @nivo/heatmap @nivo/sankey @nivo/treemap
```

**Example:**
```typescript
import { ResponsiveHeatMap } from '@nivo/heatmap';

<ResponsiveHeatMap
  data={heatmapData}
  margin={{ top: 60, right: 90, bottom: 60, left: 90 }}
  valueFormat=">-.2s"
/>
```

---

#### 4. **D3.js** (Maximum Flexibility)
**Pros:**
- Most powerful and flexible
- Can create any visualization
- Full control over every aspect
- Great for custom, unique charts

**Cons:**
- Steep learning curve
- More code required
- Imperative (not React-friendly without wrappers)

**Best For:** Custom visualizations, Chord diagrams, complex interactions

**Installation:**
```bash
npm install d3
```

**Usage:** Typically used with useEffect and refs in React

---

#### 5. **Visx** (Airbnb's D3 + React)
**Pros:**
- Combines D3 power with React patterns
- Component-based D3
- Great for custom charts
- TypeScript support

**Cons:**
- Still requires D3 knowledge
- More boilerplate than Recharts

**Best For:** Custom charts with D3 flexibility but React patterns

**Installation:**
```bash
npm install @visx/visx
```

---

### Recommended Combination

**For this project, we recommend:**

1. **Recharts** - For standard charts (bar, line, pie, area)
2. **Apache ECharts** - For advanced charts (heatmap, sankey, treemap, radar, waterfall, chord)
3. **Nivo** - Alternative for heatmaps and sankey if you prefer the aesthetic

**Rationale:**
- Recharts handles 60% of charts with minimal code
- ECharts fills the gap for complex visualizations
- Both have excellent React integrations
- Combined bundle size is acceptable
- Covers all chart types in this document

---

## Backend Data Considerations

### Required Backend Endpoints

To support these visualizations, you'll need these analytics endpoints:

#### 1. Time-Series Data
```python
GET /api/v1/analytics/timeseries
Query params:
  - start_date, end_date
  - group_by: hour|day|week|month
  - metric: revenue|orders|aov
  - dimension: category|payment_method|status
```

#### 2. Category Performance
```python
GET /api/v1/analytics/categories
Query params:
  - start_date, end_date
  - include_items: boolean
Returns: Hierarchical data for treemaps
```

#### 3. Product Matrix
```python
GET /api/v1/analytics/product-matrix
Query params:
  - start_date, end_date
Returns: quantity_sold, revenue, margin per product
```

#### 4. Co-occurrence Analysis
```python
GET /api/v1/analytics/co-occurrence
Query params:
  - level: category|item
  - start_date, end_date
Returns: Pairing frequency matrix
```

#### 5. Distribution Stats
```python
GET /api/v1/analytics/distributions
Query params:
  - metric: order_value|quantity|revenue
  - group_by: day_of_week|payment_method|category
Returns: Min, Q1, median, Q3, max, outliers
```

#### 6. Inventory Insights
```python
GET /api/v1/analytics/inventory
Query params:
  - type: valuation|usage|transactions
  - start_date, end_date
Returns: Appropriate data for inventory charts
```

#### 7. Real-time Metrics
```python
GET /api/v1/analytics/realtime
Returns: Current values for gauges
  - today_revenue, today_target, avg_revenue
  - active_orders, order_count
  - inventory_fill_rate
```

---

### Data Optimization Tips

1. **Database Indexing**
   ```sql
   CREATE INDEX idx_orders_created_at ON orders(created_at);
   CREATE INDEX idx_orders_status ON orders(status);
   CREATE INDEX idx_order_items_order_id ON order_items(order_id);
   CREATE INDEX idx_payments_payment_method ON payments(payment_method);
   ```

2. **Materialized Views** (for heavy queries)
   ```sql
   CREATE MATERIALIZED VIEW daily_revenue_summary AS
   SELECT DATE(created_at) as date,
          SUM(total_amount) as revenue,
          COUNT(*) as order_count
   FROM orders
   WHERE status = 'PAID'
   GROUP BY DATE(created_at);
   ```

3. **Caching Strategy**
   - Real-time metrics: No cache (fresh data)
   - Hourly aggregates: 5-minute cache
   - Daily aggregates: 1-hour cache
   - Historical data: 24-hour cache

4. **Pagination**
   - For large datasets (e.g., all orders), implement cursor-based pagination
   - Return max 1000 records per request

5. **Aggregation in Database**
   - Always aggregate in SQL, not in Python
   - Use database's date/time functions
   - Leverage window functions for rankings

---

## Implementation Priority

### Phase 1: Quick Wins (Week 1)
1. **Heatmap**: Time-based order heatmap
2. **Funnel**: Order completion funnel
3. **Gauges**: Real-time performance gauges
4. **Stacked Area**: Revenue composition over time

**Rationale:** High impact, medium complexity, use Recharts + ECharts

---

### Phase 2: Product Insights (Week 2)
1. **Treemap**: Category/Product revenue hierarchy
2. **Bubble Chart**: Product performance matrix
3. **Radar Chart**: Category performance scores
4. **Box Plot**: Order value distribution

**Rationale:** Critical for menu optimization, moderate complexity

---

### Phase 3: Advanced Analytics (Week 3)
1. **Sankey**: Revenue flow diagram
2. **Waterfall**: Daily revenue breakdown
3. **Chord Diagram**: Category co-occurrence
4. **Polar Chart**: Hourly order distribution

**Rationale:** High visual impact, complex implementation

---

### Phase 4: Operational Tools (Week 4)
1. **Calendar Heatmap**: Daily revenue calendar
2. **Timeline**: Order lifecycle view
3. **Violin Plot**: Price distribution
4. **Inventory Treemap**: Cost distribution

**Rationale:** Nice-to-have, specialized use cases

---

## Data Quality Considerations

### Required Data Validations

1. **Timezone Consistency**
   - All timestamps in UTC
   - Convert to local timezone in frontend only

2. **Currency Precision**
   - Always use paise (integers) in database
   - Convert to rupees only for display
   - Avoid floating-point arithmetic

3. **Status Integrity**
   - Ensure orders can't skip statuses
   - Validate status transitions

4. **Date Range Limits**
   - Cap queries to max 1 year
   - Warn on queries >90 days
   - Suggest aggregated views for long ranges

5. **Null Handling**
   - Handle optional fields (customer_name, table_number)
   - Default values for missing data

---

## Performance Benchmarks

### Expected Query Performance

| Chart Type | Data Points | Query Time | Acceptable Limit |
|------------|-------------|------------|------------------|
| Heatmap (7×24) | 168 cells | <100ms | <500ms |
| Treemap | <100 nodes | <200ms | <1s |
| Sankey | <50 flows | <300ms | <1s |
| Time-series (30 days) | 30 points | <50ms | <200ms |
| Distribution stats | 1000 orders | <500ms | <2s |

### Optimization Strategies if Slow

1. **Database**
   - Add indexes
   - Use materialized views
   - Partition large tables by date

2. **Application**
   - Implement caching (Redis)
   - Pre-compute aggregates
   - Background jobs for heavy computations

3. **Frontend**
   - Lazy load charts
   - Virtualize long lists
   - Debounce filter changes
   - Show loading states

---

## Accessibility Considerations

1. **Color Blindness**
   - Use colorblind-friendly palettes
   - Don't rely solely on color to convey information
   - Add patterns/textures where possible

2. **Screen Readers**
   - Provide alt text for charts
   - Include data tables as alternative
   - ARIA labels for interactive elements

3. **Keyboard Navigation**
   - All filters keyboard accessible
   - Tab order logical
   - Keyboard shortcuts for common actions

4. **Contrast**
   - Ensure WCAG AA compliance (4.5:1 ratio)
   - Test in different lighting conditions

---

## Next Steps

1. **Review & Prioritize**
   - Discuss which charts are most valuable for your business
   - Align with user needs and business goals

2. **Backend Development**
   - Create analytics endpoints
   - Optimize database queries
   - Implement caching

3. **Frontend Development**
   - Set up chart libraries
   - Create reusable chart components
   - Build dashboard layouts

4. **Testing**
   - Test with real data at scale
   - Performance testing
   - User acceptance testing

5. **Iteration**
   - Gather user feedback
   - Refine visualizations
   - Add new charts based on needs

---

## References

- **ECharts Documentation:** https://echarts.apache.org/
- **Recharts Documentation:** https://recharts.org/
- **Nivo Documentation:** https://nivo.rocks/
- **D3.js Documentation:** https://d3js.org/
- **Visx Documentation:** https://airbnb.io/visx/

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
**Maintainer:** Development Team
