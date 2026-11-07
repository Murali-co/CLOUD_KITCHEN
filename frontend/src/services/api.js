import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: inject JWT Bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 unauthenticated
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if expired or revoked
      const currentPath = window.location.pathname;
      if (currentPath !== "/login" && currentPath !== "/register") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
      }
    }
    return Promise.reject(error);
  }
);

// Auth Endpoints
export const authApi = {
  login: (data) => api.post("/auth/login", data),
  register: (data) => api.post("/auth/register", data),
  getMe: () => api.get("/auth/me"),
  logout: () => api.post("/auth/logout"),
};

// Customer Endpoints
export const customerApi = {
  getProfile: () => api.get("/customer/profile"),
  updateProfile: (data) => api.put("/customer/profile", data),
  getAddresses: () => api.get("/customer/addresses"),
  createAddress: (data) => api.post("/customer/addresses", data),
  updateAddress: (id, data) => api.put(`/customer/addresses/${id}`, data),
  deleteAddress: (id) => api.delete(`/customer/addresses/${id}`),
};

// Catalog Endpoints
export const catalogApi = {
  getKitchens: () => api.get("/kitchens"),
  getKitchenDetail: (id) => api.get(`/kitchens/${id}`),
  getCategories: () => api.get("/categories"),
  getCuisines: (params) => api.get("/cuisines", { params }),
  getCuisineById: (id) => api.get(`/cuisines/${id}`),
  getCuisineBySlug: (slug) => api.get(`/cuisines/slug/${slug}`),
  getMenu: (params) => api.get("/menu", { params }),
  getMenuItem: (id) => api.get(`/menu/${id}`),
};

// Cart Endpoints (Phase 6)
export const cartApi = {
  getCart: () => api.get("/cart"),
  addItem: (data) => api.post("/cart/items", data),
  updateItemQuantity: (itemId, quantity) => api.put(`/cart/items/${itemId}`, { quantity }),
  removeItem: (itemId) => api.delete(`/cart/items/${itemId}`),
  clearCart: () => api.delete("/cart"),
  applyCoupon: (couponCode) => api.post("/cart/apply-coupon", { coupon_code: couponCode }),
  removeCoupon: () => api.delete("/cart/remove-coupon"),
};

// Checkout Endpoints (Phase 6/7)
export const checkoutApi = {
  getSummary: (addressId) => api.get("/checkout/summary", { params: { address_id: addressId } }),
  validate: (data) => api.post("/checkout/validate", data),
};

// Order Endpoints (Phase 7)
export const orderApi = {
  placeOrder: (data) => api.post("/orders", data),
  listOrders: (page = 1, pageSize = 10) => api.get("/orders", { params: { page, page_size: pageSize } }),
  getOrderDetail: (orderId) => api.get(`/orders/${orderId}`),
  cancelOrder: (orderId, reason) => api.post(`/orders/${orderId}/cancel`, { reason }),
  getTracking: (orderId) => api.get(`/orders/${orderId}/tracking`),
};

// Payment Endpoints (Phase 7)
export const paymentApi = {
  createPayment: (data) => api.post("/payments/create", data),
  verifyPayment: (data) => api.post("/payments/verify", data),
  getPaymentStatus: (paymentId) => api.get(`/payments/${paymentId}`),
};

// Kitchen Operations Endpoints (Phase 8)
export const kitchenApi = {
  getMyProfile: () => api.get("/kitchen/me"),
  getDashboard: () => api.get("/kitchen/dashboard"),
  getQueue: () => api.get("/kitchen/queue"),
  getOrders: (params) => api.get("/kitchen/orders", { params }),
  getOrderDetail: (orderId) => api.get(`/kitchen/orders/${orderId}`),
  updateOrderStatus: (orderId, data) => api.patch(`/kitchen/orders/${orderId}/status`, data),
  getMenu: (params) => api.get("/kitchen/menu", { params }),
  createMenuItem: (data) => api.post("/kitchen/menu", data),
  updateMenuItem: (itemId, data) => api.put(`/kitchen/menu/${itemId}`, data),
  updateMenuAvailability: (itemId, isAvailable) => api.patch(`/kitchen/menu/${itemId}/availability`, { is_available: isAvailable }),
  getAvailability: () => api.get("/kitchen/availability"),
  updateAvailability: (data) => api.patch("/kitchen/availability", data),
};

// Kitchen Inventory & Recipe Endpoints (Phase 9)
export const inventoryApi = {
  getIngredients: (params) => api.get("/kitchen/ingredients", { params }),
  createIngredient: (data) => api.post("/kitchen/ingredients", data),
  updateIngredient: (id, data) => api.put(`/kitchen/ingredients/${id}`, data),
  getInventory: (params) => api.get("/kitchen/inventory", { params }),
  getInventoryItem: (ingredientId) => api.get(`/kitchen/inventory/${ingredientId}`),
  updateReorderLevel: (ingredientId, reorderLevel) => api.patch(`/kitchen/inventory/${ingredientId}`, { reorder_level: reorderLevel }),
  getLowStockAlerts: () => api.get("/kitchen/inventory/low-stock"),
  stockIn: (data) => api.post("/kitchen/inventory/stock-in", data),
  stockAdjustment: (data) => api.post("/kitchen/inventory/stock-adjustment", data),
  getMovements: (params) => api.get("/kitchen/inventory/movements", { params }),
  getRecipe: (menuItemId) => api.get(`/kitchen/menu/${menuItemId}/recipe`),
  updateRecipe: (menuItemId, data) => api.put(`/kitchen/menu/${menuItemId}/recipe`, data),
};

// Delivery Operations Endpoints (Phase 10)
export const deliveryApi = {
  getProfile: () => api.get("/delivery/profile"),
  updateAvailability: (data) => api.patch("/delivery/availability", data),
  getDashboard: () => api.get("/delivery/dashboard"),
  getAssignments: (params) => api.get("/delivery/assignments", { params }),
  getAssignmentDetail: (deliveryId) => api.get(`/delivery/assignments/${deliveryId}`),
  updateStatus: (deliveryId, data) => api.patch(`/delivery/assignments/${deliveryId}/status`, data),
};

// Admin Operations Endpoints (Phase 11)
export const adminApi = {
  getDashboard: () => api.get("/admin/dashboard"),
  getUsers: (params) => api.get("/admin/users", { params }),
  getUser: (userId) => api.get(`/admin/users/${userId}`),
  updateUserStatus: (userId, data) => api.patch(`/admin/users/${userId}/status`, data),
  updateUserRole: (userId, data) => api.patch(`/admin/users/${userId}/role`, data),
  getKitchens: (params) => api.get("/admin/kitchens", { params }),
  getKitchen: (kitchenId) => api.get(`/admin/kitchens/${kitchenId}`),
  createKitchen: (data) => api.post("/admin/kitchens", data),
  updateKitchen: (kitchenId, data) => api.put(`/admin/kitchens/${kitchenId}`, data),
  updateKitchenStatus: (kitchenId, data) => api.patch(`/admin/kitchens/${kitchenId}/status`, data),
  getStaff: (params) => api.get("/admin/staff", { params }),
  createStaff: (data) => api.post("/admin/staff", data),
  reassignStaff: (staffId, data) => api.patch(`/admin/staff/${staffId}/reassign`, data),
  getMenu: (params) => api.get("/admin/menu", { params }),
  updateMenuItemStatus: (itemId, data) => api.patch(`/admin/menu/${itemId}/status`, data),
  getCategories: () => api.get("/admin/categories"),
  createCategory: (data) => api.post("/admin/categories", data),
  updateCategory: (categoryId, data) => api.put(`/admin/categories/${categoryId}`, data),
  getOrders: (params) => api.get("/admin/orders", { params }),
  getOrderDetail: (orderId) => api.get(`/admin/orders/${orderId}`),
  cancelOrder: (orderId, reason) => api.post(`/admin/orders/${orderId}/cancel`, null, { params: { reason } }),
  getAvailablePersonnel: () => api.get("/admin/delivery/available-personnel"),
  assignDelivery: (orderId, data) => api.post(`/admin/orders/${orderId}/assign-delivery`, data),
  getPayments: (params) => api.get("/admin/payments", { params }),
  getCoupons: (params) => api.get("/admin/coupons", { params }),
  createCoupon: (data) => api.post("/admin/coupons", data),
  updateCoupon: (couponId, data) => api.put(`/admin/coupons/${couponId}`, data),
  getAnalytics: (days) => api.get("/admin/analytics/overview", { params: { days } }),
  getAuditLogs: (params) => api.get("/admin/audit-logs", { params }),
};
