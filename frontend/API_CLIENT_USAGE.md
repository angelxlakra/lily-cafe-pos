# API Client and Hooks Usage Guide

This document provides examples and best practices for using the API client and custom hooks in the Lily Cafe POS frontend.

## Table of Contents

1. [Setup](#setup)
2. [Authentication](#authentication)
3. [Menu Management](#menu-management)
4. [Order Management](#order-management)
5. [Payment Processing](#payment-processing)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Setup

The API client is already configured with:
- Base URL from `VITE_API_URL` environment variable
- JWT token auto-injection via request interceptor
- Error handling via response interceptor
- Retry logic with exponential backoff

### Environment Variables

Create a `.env` file in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000
```

For production or testing on local network:
```env
VITE_API_URL=http://192.168.1.X:8000
```

---

## Authentication

### Login

```tsx
import { useAuth } from '../hooks/useAuth';

function LoginPage() {
  const { login, isLoggingIn, loginError, isAuthenticated } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await login({
        username: 'admin',
        password: 'changeme123',
      });
      // Success - redirect to dashboard
      navigate('/admin/dashboard');
    } catch (error) {
      // Error is captured in loginError
      console.error('Login failed');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input type="text" name="username" />
      <input type="password" name="password" />
      <button type="submit" disabled={isLoggingIn}>
        {isLoggingIn ? 'Logging in...' : 'Login'}
      </button>
      {loginError && <p className="error">{loginError}</p>}
    </form>
  );
}
```

### Logout

```tsx
import { useAuth } from '../hooks/useAuth';

function Header() {
  const { logout, isAuthenticated } = useAuth();

  return (
    <header>
      {isAuthenticated && (
        <button onClick={logout}>Logout</button>
      )}
    </header>
  );
}
```

### Protected Routes

```tsx
import { useAuth } from '../hooks/useAuth';
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
```

---

## Menu Management

### Fetching Menu Items

```tsx
import { useMenuItems } from '../hooks/useMenu';

function MenuPage() {
  const { data, isLoading, error } = useMenuItems({ available_only: true });

  if (isLoading) return <div>Loading menu...</div>;
  if (error) return <div>Error loading menu</div>;

  const items = data?.items || [];

  return (
    <div>
      {items.map(item => (
        <div key={item.id}>
          <h3>{item.name}</h3>
          <p>{item.description}</p>
          <p>₹{item.price}</p>
        </div>
      ))}
    </div>
  );
}
```

### Creating a Menu Item

```tsx
import { useCreateMenuItem } from '../hooks/useMenu';

function AddMenuItemForm() {
  const { mutate: createItem, isPending } = useCreateMenuItem();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    createItem({
      name: 'Masala Dosa',
      description: 'Crispy dosa with potato filling',
      price: 80,
      category: 'South Indian',
      is_available: true,
    }, {
      onSuccess: () => {
        // Show success toast
        toast.success('Menu item added!');
        // Close form
        onClose();
      },
      onError: (error) => {
        toast.error('Failed to add item');
      },
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={isPending}>
        {isPending ? 'Adding...' : 'Add Item'}
      </button>
    </form>
  );
}
```

### Updating a Menu Item

```tsx
import { useUpdateMenuItem } from '../hooks/useMenu';

function EditMenuItemForm({ itemId }: { itemId: number }) {
  const { mutate: updateItem, isPending } = useUpdateMenuItem();

  const handleUpdate = () => {
    updateItem({
      id: itemId,
      data: {
        price: 90, // Update price only
      },
    }, {
      onSuccess: () => {
        toast.success('Item updated!');
      },
    });
  };

  return (
    <button onClick={handleUpdate} disabled={isPending}>
      Update Price
    </button>
  );
}
```

### Using the Composite Hook

```tsx
import { useMenu } from '../hooks/useMenu';

function MenuManagement() {
  const menu = useMenu({ available_only: false });

  // Access data
  const items = menu.items.data?.items || [];
  const categories = menu.categories.data?.categories || [];

  // Create new item
  const handleAddItem = () => {
    menu.createItem({
      name: 'New Dish',
      price: 100,
      category: 'Main Course',
    });
  };

  // Delete item
  const handleDelete = (id: number) => {
    menu.deleteItem(id);
  };

  return (
    <div>
      <h1>Menu Management</h1>
      {menu.isLoading && <p>Loading...</p>}
      {menu.isMutating && <p>Saving...</p>}

      {items.map(item => (
        <div key={item.id}>
          <span>{item.name} - ₹{item.price}</span>
          <button onClick={() => handleDelete(item.id)}>Delete</button>
        </div>
      ))}

      <button onClick={handleAddItem}>Add New Item</button>
    </div>
  );
}
```

---

## Order Management

### Viewing Active Orders

```tsx
import { useActiveOrders } from '../hooks/useOrders';

function ActiveOrdersList() {
  const { data, isLoading, error } = useActiveOrders();

  if (isLoading) return <div>Loading orders...</div>;
  if (error) return <div>Error loading orders</div>;

  const orders = data?.orders || [];

  return (
    <div>
      <h2>Active Orders ({orders.length})</h2>
      {orders.map(order => (
        <div key={order.id} className="order-card">
          <h3>Table {order.table_number}</h3>
          <p>{order.item_count} items</p>
          <p>₹{order.total_amount}</p>
          <p>{new Date(order.created_at).toLocaleTimeString()}</p>
        </div>
      ))}
    </div>
  );
}
```

### Creating an Order

```tsx
import { useCreateOrUpdateOrder } from '../hooks/useOrders';

function OrderPage({ tableNumber }: { tableNumber: number }) {
  const [cart, setCart] = useState<Array<{ menu_item_id: number; quantity: number }>>([]);
  const { mutate: createOrder, isPending } = useCreateOrUpdateOrder();

  const handleSaveOrder = () => {
    createOrder({
      table_number: tableNumber,
      customer_name: 'Rahul',
      items: cart,
    }, {
      onSuccess: () => {
        toast.success(`Order saved for Table ${tableNumber}!`);
        setCart([]);
        navigate('/tables');
      },
      onError: (error) => {
        toast.error('Failed to save order');
      },
    });
  };

  return (
    <div>
      <h2>Table {tableNumber} - New Order</h2>
      {/* Menu items and cart UI */}
      <button onClick={handleSaveOrder} disabled={isPending || cart.length === 0}>
        {isPending ? 'Saving...' : 'Save Order'}
      </button>
    </div>
  );
}
```

### Updating an Existing Order

```tsx
import { useCreateOrUpdateOrder } from '../hooks/useOrders';

function EditOrderPage({ orderId, existingItems }: { orderId: number; existingItems: any[] }) {
  const [cart, setCart] = useState(existingItems);
  const { mutate: updateOrder, isPending } = useCreateOrUpdateOrder();

  const handleUpdateOrder = () => {
    updateOrder({
      order_id: orderId,
      items: cart.map(item => ({
        menu_item_id: item.menu_item_id,
        quantity: item.quantity,
      })),
    }, {
      onSuccess: () => {
        toast.success('Order updated!');
      },
    });
  };

  return (
    <button onClick={handleUpdateOrder} disabled={isPending}>
      Update Order
    </button>
  );
}
```

### Canceling an Order

```tsx
import { useCancelOrder } from '../hooks/useOrders';

function OrderCard({ order }: { order: any }) {
  const { mutate: cancelOrder, isPending } = useCancelOrder();

  const handleCancel = () => {
    if (confirm(`Cancel order for Table ${order.table_number}?`)) {
      cancelOrder(order.id, {
        onSuccess: () => {
          toast.success('Order canceled');
        },
      });
    }
  };

  return (
    <div>
      <p>Table {order.table_number}</p>
      <button onClick={handleCancel} disabled={isPending}>
        Cancel Order
      </button>
    </div>
  );
}
```

### Using the Composite Hook

```tsx
import { useOrders } from '../hooks/useOrders';

function OrdersManagement() {
  const orders = useOrders({ date: '2024-10-30' });

  // Access data
  const activeOrders = orders.active.data?.orders || [];
  const history = orders.history.data?.orders || [];

  // Create order
  const handleCreateOrder = () => {
    orders.createOrder({
      table_number: 5,
      items: [
        { menu_item_id: 1, quantity: 2 },
      ],
    });
  };

  // Cancel order
  const handleCancelOrder = (id: number) => {
    orders.cancelOrder(id);
  };

  return (
    <div>
      <h1>Orders</h1>
      {orders.isLoading && <p>Loading...</p>}
      {orders.isMutating && <p>Processing...</p>}

      <section>
        <h2>Active Orders</h2>
        {activeOrders.map(order => (
          <div key={order.id}>
            <span>Table {order.table_number}</span>
            <button onClick={() => handleCancelOrder(order.id)}>Cancel</button>
          </div>
        ))}
      </section>

      <button onClick={handleCreateOrder}>New Order</button>
    </div>
  );
}
```

---

## Payment Processing

### Adding Payments

```tsx
import { useAddPayments } from '../hooks/useOrders';

function PaymentModal({ order }: { order: any }) {
  const [payments, setPayments] = useState<Array<{ method: PaymentMethod; amount: number }>>([]);
  const { mutate: addPayments, isPending } = useAddPayments();

  const handleComplete = () => {
    addPayments({
      orderId: order.id,
      data: { payments },
    }, {
      onSuccess: () => {
        toast.success('Payment completed!');
        // Print receipt
        printReceipt(order.id);
      },
      onError: (error) => {
        toast.error('Payment failed');
      },
    });
  };

  const remaining = order.total_amount - payments.reduce((sum, p) => sum + p.amount, 0);

  return (
    <div>
      <h3>Payment for Table {order.table_number}</h3>
      <p>Total: ₹{order.total_amount}</p>

      {/* Payment form */}

      <p>Remaining: ₹{remaining}</p>

      <button
        onClick={handleComplete}
        disabled={isPending || remaining !== 0}
      >
        {isPending ? 'Processing...' : 'Complete Payment'}
      </button>
    </div>
  );
}
```

### Printing Receipt

```tsx
import { usePrintReceipt } from '../hooks/useOrders';

function PaymentConfirmation({ orderId }: { orderId: number }) {
  const { mutate: printReceipt, isPending } = usePrintReceipt();

  const handlePrint = () => {
    printReceipt(orderId, {
      onSuccess: () => {
        // Receipt opened in new tab for printing
        toast.success('Receipt ready to print');
      },
      onError: () => {
        toast.error('Failed to generate receipt');
      },
    });
  };

  return (
    <button onClick={handlePrint} disabled={isPending}>
      {isPending ? 'Generating...' : 'Print Receipt'}
    </button>
  );
}
```

---

## Error Handling

### Global Error Handling

Errors are automatically caught by the response interceptor and can be handled in mutation callbacks:

```tsx
const { mutate: createItem } = useCreateMenuItem();

createItem(data, {
  onError: (error) => {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        toast.error('Unauthorized - please login');
      } else if (error.response?.status === 422) {
        toast.error('Invalid data - check your inputs');
      } else {
        toast.error('Server error - please try again');
      }
    } else {
      toast.error('Network error - check your connection');
    }
  },
});
```

### Retry Logic

Queries automatically retry with exponential backoff (configured in main.tsx):
- Queries retry 3 times: 1s, 2s, 4s
- Mutations retry 1 time after 1s

You can disable retry for specific queries:

```tsx
const { data } = useMenuItems({ available_only: true }, {
  retry: false, // Don't retry this query
});
```

---

## Best Practices

### 1. Use Composite Hooks When Possible

Instead of importing multiple hooks:
```tsx
// Good
const menu = useMenu();
const orders = useOrders();

// Less ideal
const { data: items } = useMenuItems();
const { mutate: createItem } = useCreateMenuItem();
const { mutate: deleteItem } = useDeleteMenuItem();
```

### 2. Handle Loading and Error States

Always show loading and error states:
```tsx
const { data, isLoading, error } = useActiveOrders();

if (isLoading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
if (!data) return null;

return <OrdersList orders={data.orders} />;
```

### 3. Use Optimistic Updates for Better UX

The `useCreateOrUpdateOrder` hook already implements optimistic updates. The UI updates immediately, then rolls back if the server request fails.

### 4. Invalidate Queries When Needed

Queries are automatically invalidated after mutations, but you can manually invalidate:

```tsx
import { useQueryClient } from '@tanstack/react-query';
import { ordersQueryKeys } from '../hooks/useOrders';

const queryClient = useQueryClient();

// Manually refetch active orders
queryClient.invalidateQueries({ queryKey: ordersQueryKeys.active });
```

### 5. Use Success/Error Callbacks

Handle success and error cases in mutation callbacks:

```tsx
mutation.mutate(data, {
  onSuccess: (data) => {
    toast.success('Success!');
    navigate('/success-page');
  },
  onError: (error) => {
    toast.error('Failed!');
    console.error(error);
  },
});
```

### 6. Check Authentication Before Admin Actions

```tsx
const { isAuthenticated } = useAuth();

if (!isAuthenticated) {
  return <Navigate to="/login" />;
}

return <AdminDashboard />;
```

### 7. Use TypeScript Types

All types are exported from `types/index.ts`. Use them for type safety:

```tsx
import type { MenuItem, Order, CreateOrderRequest } from '../types';

const handleCreateOrder = (data: CreateOrderRequest) => {
  // TypeScript ensures data matches the expected structure
};
```

---

## Testing API Calls

To test the API client:

1. Start the backend:
```bash
cd backend
uv run uvicorn main:app --reload
```

2. Start the frontend:
```bash
cd frontend
npm run dev
```

3. Check API calls in browser DevTools Network tab

4. Test authentication:
   - Login with `admin` / `changeme123`
   - Verify token stored in localStorage
   - Verify token sent in Authorization header

5. Test queries:
   - Check menu items load
   - Check active orders load
   - Verify automatic refetching

6. Test mutations:
   - Create menu item
   - Create order
   - Add payments
   - Verify cache updates

---

## Next Steps

1. Build UI components using these hooks
2. Add toast notifications for user feedback
3. Implement loading skeletons
4. Add error boundaries
5. Test on local network with multiple devices
6. Test thermal printer integration

---

**Version:** 0.1
**Last Updated:** November 1, 2024
