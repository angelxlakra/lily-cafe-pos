/**
 * Utility for testing receipt printing functionality
 * Creates a test order, processes payment, and triggers print
 */

import axios from "axios";

const API_BASE = "http://192.168.31.29:8000/api/v1";

// Test order configuration
const TEST_ORDER = {
  table_number: 49,
  customer_name: "Test Customer (Auto-Generated)",
  items: [
    { menu_item_id: 1, quantity: 2 }, // Adjust based on your seed data
    { menu_item_id: 2, quantity: 1 },
  ],
};

interface Order {
  id: number;
  order_number: string;
  total_amount: number;
  status: string;
}

interface Payment {
  id: number;
  payment_method: string;
  amount: number;
}

/**
 * Get authentication token for admin operations
 */
async function getAuthToken(): Promise<string> {
  const response = await axios.post(`${API_BASE}/auth/login`, {
    username: "admin",
    password: "changeme123", // From seed data
  });

  return response.data.access_token;
}

/**
 * Create a test order
 */
async function createTestOrder(): Promise<Order> {
  const response = await axios.post(`${API_BASE}/orders`, TEST_ORDER);
  return response.data;
}

/**
 * Add payment to order (marks it as paid)
 */
async function addPayment(
  orderId: number,
  totalAmount: number,
  token: string
): Promise<Payment[]> {
  const response = await axios.post(
    `${API_BASE}/orders/${orderId}/payments/batch`,
    {
      orderId: orderId,
      payments: [
        { payment_method: "cash", amount: totalAmount / 2 },
        { payment_method: "upi", amount: totalAmount / 2 },
      ],
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

/**
 * Open receipt PDF in new tab (works without printer)
 */
function openReceiptInNewTab(orderId: number): void {
  const receiptUrl = `${API_BASE}/orders/${orderId}/receipt`;
  window.open(receiptUrl, "_blank");
}

/**
 * Trigger print dialog for receipt PDF (requires printer)
 */
async function printReceiptPDF(orderId: number): Promise<void> {
  const receiptUrl = `${API_BASE}/orders/${orderId}/receipt`;

  try {
    // Fetch PDF as blob to avoid cross-origin issues
    const response = await axios.get(receiptUrl, {
      responseType: "blob",
    });

    // Create blob URL (same-origin)
    const blobUrl = URL.createObjectURL(response.data);

    return new Promise((resolve, reject) => {
      // Create hidden iframe for printing
      const iframe = document.createElement("iframe");
      iframe.style.display = "none";
      iframe.src = blobUrl;

      iframe.onload = () => {
        try {
          // Small delay to ensure PDF renders
          setTimeout(() => {
            const iframeWindow = iframe.contentWindow;
            if (!iframeWindow) {
              document.body.removeChild(iframe);
              URL.revokeObjectURL(blobUrl);
              reject(new Error("Failed to access iframe window"));
              return;
            }

            // Listen for afterprint event to clean up only after user closes print dialog
            iframeWindow.addEventListener("afterprint", () => {
              document.body.removeChild(iframe);
              URL.revokeObjectURL(blobUrl);
            });

            // Trigger print dialog
            iframeWindow.print();
            resolve();
          }, 500);
        } catch (error) {
          document.body.removeChild(iframe);
          URL.revokeObjectURL(blobUrl);
          reject(new Error("Failed to trigger print dialog"));
        }
      };

      iframe.onerror = () => {
        document.body.removeChild(iframe);
        URL.revokeObjectURL(blobUrl);
        reject(new Error("Failed to load receipt PDF"));
      };

      document.body.appendChild(iframe);
    });
  } catch (error) {
    throw new Error("Failed to fetch receipt PDF");
  }
}

/**
 * Main function: Complete test flow with auto-print
 * 1. Create test order
 * 2. Add payment (marks as paid)
 * 3. Generate and print receipt
 */
export async function printTestReceipt(
  onProgress?: (message: string) => void
): Promise<void> {
  try {
    // Step 1: Get auth token
    onProgress?.("Authenticating...");
    const token = await getAuthToken();

    // Step 2: Create test order
    onProgress?.("Creating test order...");
    const order = await createTestOrder();
    console.log("✅ Test order created:", order.id, order.order_number);

    // Step 3: Add payment
    onProgress?.("Processing payment...");
    await addPayment(order.id, order.total_amount, token);
    console.log("✅ Payment processed, order marked as paid");

    // Step 4: Generate and print receipt
    onProgress?.("Generating receipt...");
    await printReceiptPDF(order.id);
    console.log("✅ Receipt sent to printer");

    onProgress?.("✅ Receipt printed successfully!");
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Print failed: ${message}`);
    }
    throw error;
  }
}

/**
 * Alternative: Open receipt in new tab (no printer required)
 * 1. Create test order
 * 2. Add payment (marks as paid)
 * 3. Open receipt PDF in new browser tab
 */
export async function viewTestReceipt(
  onProgress?: (message: string) => void
): Promise<void> {
  try {
    // Step 1: Get auth token
    onProgress?.("Authenticating...");
    const token = await getAuthToken();

    // Step 2: Create test order
    onProgress?.("Creating test order...");
    const order = await createTestOrder();
    console.log("✅ Test order created:", order.id, order.order_number);

    // Step 3: Add payment
    onProgress?.("Processing payment...");
    await addPayment(order.id, order.total_amount, token);
    console.log("✅ Payment processed, order marked as paid");

    // Step 4: Open receipt in new tab
    onProgress?.("Opening receipt...");
    openReceiptInNewTab(order.id);
    console.log("✅ Receipt opened in new tab");

    onProgress?.("✅ Receipt opened successfully!");
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Failed: ${message}`);
    }
    throw error;
  }
}
