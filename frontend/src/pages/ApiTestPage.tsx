// ========================================
// API Test Page
// For testing all API endpoints and hooks
// ========================================

import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useMenu } from '../hooks/useMenu';
import { useOrders } from '../hooks/useOrders';

export default function ApiTestPage() {
  const [testResults, setTestResults] = useState<string[]>([]);

  const auth = useAuth();
  const menu = useMenu({ available_only: true });
  const orders = useOrders();

  const addResult = (message: string, success: boolean = true) => {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = success ? '✅' : '❌';
    setTestResults(prev => [`${prefix} [${timestamp}] ${message}`, ...prev]);
  };

  // Test Authentication
  const testLogin = async () => {
    try {
      await auth.login({ username: 'admin', password: 'changeme123' });
      addResult('Login successful!');
    } catch (error) {
      addResult(`Login failed: ${error}`, false);
    }
  };

  const testLogout = () => {
    auth.logout();
    addResult('Logged out successfully');
  };

  // Test Menu API
  const testGetMenu = async () => {
    try {
      const items = menu.items.data || [];
      addResult(`Fetched ${items.length} menu items`);
    } catch (error) {
      addResult(`Failed to fetch menu: ${error}`, false);
    }
  };

  const testCreateMenuItem = async () => {
    try {
      await menu.createItemAsync({
        name: 'Test Item ' + Date.now(),
        description: 'Test description',
        price: 99,
        category: 'Test Category',
        is_available: true,
      });
      addResult('Created menu item successfully!');
    } catch (error) {
      addResult(`Failed to create menu item: ${error}`, false);
    }
  };

  // Test Orders API
  const testGetActiveOrders = async () => {
    try {
      const activeOrders = orders.active.data || [];
      addResult(`Fetched ${activeOrders.length} active orders`);
    } catch (error) {
      addResult(`Failed to fetch active orders: ${error}`, false);
    }
  };

  const testCreateOrder = async () => {
    try {
      const firstMenuItem = menu.items.data?.[0];
      if (!firstMenuItem) {
        addResult('No menu items available to create order', false);
        return;
      }

      await orders.createOrderAsync({
        table_number: Math.floor(Math.random() * 10) + 1,
        customer_name: 'Test Customer',
        items: [
          { menu_item_id: firstMenuItem.id, quantity: 2 },
        ],
      });
      addResult('Created order successfully!');
    } catch (error) {
      addResult(`Failed to create order: ${error}`, false);
    }
  };

  const testGetCategories = async () => {
    try {
      const categories = menu.categories.data || [];
      addResult(`Fetched ${categories.length} categories`);
    } catch (error) {
      addResult(`Failed to fetch categories: ${error}`, false);
    }
  };

  // Clear results
  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <div className="min-h-screen bg-neutral-background p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-coffee-brown mb-6">
          API Client Test Page
        </h1>

        {/* Authentication Status */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6 border border-neutral-border">
          <h2 className="text-xl font-semibold text-coffee-brown mb-4">
            Authentication Status
          </h2>
          <p className="mb-4">
            Status: {auth.isAuthenticated ? (
              <span className="text-success font-semibold">✅ Authenticated</span>
            ) : (
              <span className="text-error font-semibold">❌ Not Authenticated</span>
            )}
          </p>
          {auth.loginError && (
            <p className="text-error mb-4">Error: {auth.loginError}</p>
          )}
        </div>

        {/* Test Controls */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6 border border-neutral-border">
          <h2 className="text-xl font-semibold text-coffee-brown mb-4">
            API Tests
          </h2>

          <div className="grid grid-cols-2 gap-4">
            {/* Authentication Tests */}
            <div className="space-y-2">
              <h3 className="font-semibold text-coffee-brown">Authentication</h3>
              <button
                onClick={testLogin}
                disabled={auth.isLoggingIn || auth.isAuthenticated}
                className="btn w-full bg-coffee-brown text-white hover:bg-coffee-dark disabled:bg-neutral-border"
              >
                {auth.isLoggingIn ? 'Logging in...' : 'Test Login'}
              </button>
              <button
                onClick={testLogout}
                disabled={!auth.isAuthenticated}
                className="btn w-full bg-error text-white hover:bg-[#d32f2f] disabled:bg-neutral-border"
              >
                Test Logout
              </button>
            </div>

            {/* Menu Tests */}
            <div className="space-y-2">
              <h3 className="font-semibold text-coffee-brown">Menu API</h3>
              <button
                onClick={testGetMenu}
                disabled={menu.isLoading}
                className="btn w-full bg-lily-green text-white hover:bg-[#7A8C75] disabled:bg-neutral-border"
              >
                {menu.isLoading ? 'Loading...' : 'Get Menu Items'}
              </button>
              <button
                onClick={testGetCategories}
                className="btn w-full bg-lily-green text-white hover:bg-[#7A8C75] disabled:bg-neutral-border"
              >
                Get Categories
              </button>
              <button
                onClick={testCreateMenuItem}
                disabled={!auth.isAuthenticated || menu.isMutating}
                className="btn w-full bg-info text-white hover:bg-[#1976D2] disabled:bg-neutral-border"
              >
                {menu.isMutating ? 'Creating...' : 'Create Menu Item (Auth)'}
              </button>
            </div>

            {/* Orders Tests */}
            <div className="space-y-2">
              <h3 className="font-semibold text-coffee-brown">Orders API</h3>
              <button
                onClick={testGetActiveOrders}
                disabled={orders.isLoading}
                className="btn w-full bg-lily-green text-white hover:bg-[#7A8C75] disabled:bg-neutral-border"
              >
                {orders.isLoading ? 'Loading...' : 'Get Active Orders'}
              </button>
              <button
                onClick={testCreateOrder}
                disabled={orders.isMutating || !menu.items.data}
                className="btn w-full bg-info text-white hover:bg-[#1976D2] disabled:bg-neutral-border"
              >
                {orders.isMutating ? 'Creating...' : 'Create Test Order'}
              </button>
            </div>

            {/* Clear Button */}
            <div className="space-y-2">
              <h3 className="font-semibold text-coffee-brown">Controls</h3>
              <button
                onClick={clearResults}
                className="btn w-full bg-warning text-white hover:bg-[#F57C00]"
              >
                Clear Results
              </button>
            </div>
          </div>
        </div>

        {/* Current Data */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6 border border-neutral-border">
          <h2 className="text-xl font-semibold text-coffee-brown mb-4">
            Current Data
          </h2>
          <div className="space-y-2 text-sm">
            <p>Menu Items: {menu.items.data?.length || 0}</p>
            <p>Categories: {menu.categories.data?.length || 0}</p>
            <p>Active Orders: {orders.active.data?.length || 0}</p>
          </div>
        </div>

        {/* Test Results */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-neutral-border">
          <h2 className="text-xl font-semibold text-coffee-brown mb-4">
            Test Results
          </h2>
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {testResults.length === 0 ? (
              <p className="text-neutral-text-light">No tests run yet. Click buttons above to test API endpoints.</p>
            ) : (
              testResults.map((result, index) => (
                <div
                  key={index}
                  className="p-2 bg-neutral-background rounded text-sm font-mono"
                >
                  {result}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Back Button */}
        <div className="mt-6">
          <a
            href="/"
            className="btn bg-coffee-brown text-white hover:bg-coffee-dark"
          >
            ← Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
