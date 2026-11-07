import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { ProtectedRoute } from "./components/ProtectedRoute";

// Pages
import { HomePage } from "./pages/HomePage";
import { KitchensPage } from "./pages/KitchensPage";
import { KitchenDetailPage } from "./pages/KitchenDetailPage";
import { MenuPage } from "./pages/MenuPage";
import { CartPage } from "./pages/CartPage";
import { CheckoutPage } from "./pages/CheckoutPage";
import { OrderHistoryPage } from "./pages/OrderHistoryPage";
import { OrderDetailPage } from "./pages/OrderDetailPage";
import { OrderTrackingPage } from "./pages/OrderTrackingPage";
import { OrderConfirmationPage } from "./pages/OrderConfirmationPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ProfilePage } from "./pages/ProfilePage";
import { PaymentResultPage } from "./pages/PaymentResultPage";

// Kitchen Management Pages (Phases 8 & 9)
import { KitchenDashboardPage } from "./pages/KitchenDashboardPage";
import { KitchenQueuePage } from "./pages/KitchenQueuePage";
import { KitchenOrdersPage } from "./pages/KitchenOrdersPage";
import { KitchenMenuPage } from "./pages/KitchenMenuPage";
import { KitchenInventoryPage } from "./pages/KitchenInventoryPage";
import { KitchenRecipesPage } from "./pages/KitchenRecipesPage";

// Delivery Management Pages (Phase 10)
import { DeliveryDashboardPage } from "./pages/DeliveryDashboardPage";
import { DeliveryAssignmentsPage } from "./pages/DeliveryAssignmentsPage";
import { DeliveryDetailPage } from "./pages/DeliveryDetailPage";

// Administrator Dashboard Pages (Phase 11)
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AdminUsersPage } from "./pages/AdminUsersPage";
import { AdminKitchensPage } from "./pages/AdminKitchensPage";
import { AdminStaffPage } from "./pages/AdminStaffPage";
import { AdminMenuPage } from "./pages/AdminMenuPage";
import { AdminOrdersPage } from "./pages/AdminOrdersPage";
import { AdminPaymentsPage } from "./pages/AdminPaymentsPage";
import { AdminCouponsPage } from "./pages/AdminCouponsPage";
import { AdminAnalyticsPage } from "./pages/AdminAnalyticsPage";
import { AdminAuditLogsPage } from "./pages/AdminAuditLogsPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <div className="min-h-screen flex flex-col bg-cream-100 text-charcoal-900">
            <Navbar />
            <main className="flex-1">
              <Routes>
                {/* Public Browsing Routes */}
                <Route path="/" element={<HomePage />} />
                <Route path="/kitchens" element={<KitchensPage />} />
                <Route path="/kitchens/:id" element={<KitchenDetailPage />} />
                <Route path="/menu" element={<MenuPage />} />
                <Route path="/cart" element={<CartPage />} />

                {/* Authentication Routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Protected Customer Routes */}
                <Route
                  path="/checkout"
                  element={
                    <ProtectedRoute>
                      <CheckoutPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/orders"
                  element={
                    <ProtectedRoute>
                      <OrderHistoryPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/orders/:id"
                  element={
                    <ProtectedRoute>
                      <OrderDetailPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/orders/:id/track"
                  element={
                    <ProtectedRoute>
                      <OrderTrackingPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/orders/:id/confirmation"
                  element={
                    <ProtectedRoute>
                      <OrderConfirmationPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/payments/result"
                  element={
                    <ProtectedRoute>
                      <PaymentResultPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <ProfilePage />
                    </ProtectedRoute>
                  }
                />

                {/* Protected Kitchen Operations Routes (Phases 8 & 9) */}
                <Route
                  path="/kitchen/dashboard"
                  element={
                    <ProtectedRoute allowedRoles={["KITCHEN_STAFF", "ADMIN"]}>
                      <KitchenDashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/kitchen/queue"
                  element={
                    <ProtectedRoute allowedRoles={["KITCHEN_STAFF", "ADMIN"]}>
                      <KitchenQueuePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/kitchen/orders"
                  element={
                    <ProtectedRoute allowedRoles={["KITCHEN_STAFF", "ADMIN"]}>
                      <KitchenOrdersPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/kitchen/menu"
                  element={
                    <ProtectedRoute allowedRoles={["KITCHEN_STAFF", "ADMIN"]}>
                      <KitchenMenuPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/kitchen/inventory"
                  element={
                    <ProtectedRoute allowedRoles={["KITCHEN_STAFF", "ADMIN"]}>
                      <KitchenInventoryPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/kitchen/recipes"
                  element={
                    <ProtectedRoute allowedRoles={["KITCHEN_STAFF", "ADMIN"]}>
                      <KitchenRecipesPage />
                    </ProtectedRoute>
                  }
                />

                {/* Protected Delivery Operations Routes (Phase 10) */}
                <Route
                  path="/delivery/dashboard"
                  element={
                    <ProtectedRoute allowedRoles={["DELIVERY_PERSON", "ADMIN"]}>
                      <DeliveryDashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/delivery/assignments"
                  element={
                    <ProtectedRoute allowedRoles={["DELIVERY_PERSON", "ADMIN"]}>
                      <DeliveryAssignmentsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/delivery/assignments/:id"
                  element={
                    <ProtectedRoute allowedRoles={["DELIVERY_PERSON", "ADMIN"]}>
                      <DeliveryDetailPage />
                    </ProtectedRoute>
                  }
                />

                {/* Protected Administrator Control Panel Routes (Phase 11) */}
                <Route
                  path="/admin/dashboard"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminDashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/users"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminUsersPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/kitchens"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminKitchensPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/staff"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminStaffPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/menu"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminMenuPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/orders"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminOrdersPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/payments"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminPaymentsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/coupons"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminCouponsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/analytics"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminAnalyticsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/audit-logs"
                  element={
                    <ProtectedRoute allowedRoles={["ADMIN"]}>
                      <AdminAuditLogsPage />
                    </ProtectedRoute>
                  }
                />

                {/* Catch-all redirect */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
