import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Clock,
  ClipboardList,
  UtensilsCrossed,
  Package,
  BookOpen,
  ChefHat,
  AlertTriangle,
  RefreshCw,
  Power,
  Pause,
  Play,
  ShieldCheck,
  Building2,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { kitchenApi, inventoryApi } from "../services/api";

export const KitchenLayout = ({ children, title, subtitle, actionButton }) => {
  const { user, staff, isStaff, isManager, loading: authLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [availability, setAvailability] = useState(null);
  const [lowStockCount, setLowStockCount] = useState(0);
  const [statusLoading, setStatusLoading] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusReason, setStatusReason] = useState("");

  const fetchStatusAndAlerts = async () => {
    if (!isStaff) return;
    try {
      const [availRes, alertRes] = await Promise.all([
        kitchenApi.getAvailability(),
        inventoryApi.getLowStockAlerts(),
      ]);
      if (availRes.data?.success) {
        setAvailability(availRes.data.data);
      }
      if (alertRes.data?.success) {
        setLowStockCount(alertRes.data.data.length);
      }
    } catch (e) {
      console.warn("Could not load kitchen availability or alerts", e);
    }
  };

  useEffect(() => {
    if (isStaff) {
      fetchStatusAndAlerts();
      const interval = setInterval(fetchStatusAndAlerts, 30000);
      return () => clearInterval(interval);
    }
  }, [isStaff]);

  const handleStatusChange = async (newStatus) => {
    setStatusLoading(true);
    try {
      const resp = await kitchenApi.updateAvailability({
        operating_status: newStatus,
        reason: statusReason || undefined,
      });
      if (resp.data?.success) {
        setAvailability(resp.data.data);
        setShowStatusModal(false);
        setStatusReason("");
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update kitchen operating status");
    } finally {
      setStatusLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isStaff) {
    return (
      <div className="max-w-xl mx-auto my-16 p-8 bg-white rounded-3xl border border-stone-200 shadow-sm text-center">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-charcoal-900 mb-2">Access Restricted</h2>
        <p className="text-stone-600 mb-6">
          The Kitchen Operations Portal is strictly accessible to verified Kitchen Managers and Line Cooks. Your account ({user?.email || "Guest"}) does not have staff privileges.
        </p>
        <button
          onClick={() => navigate("/")}
          className="px-6 py-2.5 bg-terracotta-600 text-white font-semibold rounded-xl hover:bg-terracotta-700 transition"
        >
          Return to Customer Homepage
        </button>
      </div>
    );
  }

  const tabs = [
    { name: "Overview", path: "/kitchen/dashboard", icon: LayoutDashboard },
    { name: "Live Queue", path: "/kitchen/queue", icon: Clock },
    { name: "Orders", path: "/kitchen/orders", icon: ClipboardList },
    { name: "Menu Catalog", path: "/kitchen/menu", icon: UtensilsCrossed },
    { name: "Inventory & Stock", path: "/kitchen/inventory", icon: Package, badge: lowStockCount > 0 ? lowStockCount : null },
    { name: "Recipes (BOM)", path: "/kitchen/recipes", icon: BookOpen },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case "ACTIVE":
        return "bg-emerald-500 text-white border-emerald-600";
      case "PAUSED":
        return "bg-amber-500 text-white border-amber-600";
      case "CLOSED":
        return "bg-rose-500 text-white border-rose-600";
      default:
        return "bg-stone-500 text-white border-stone-600";
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Banner: Kitchen Identity & Operating Controls */}
      <div className="bg-white rounded-3xl border border-stone-200/80 shadow-sm p-6 mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          {/* Kitchen Name & Staff Profile */}
          <div className="flex items-center space-x-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-500 to-terracotta-600 flex items-center justify-center text-white shadow-md shadow-terracotta-500/20">
              <ChefHat className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-bold text-charcoal-900 tracking-tight">
                  {staff?.kitchen_name || "Cloud Kitchen Operations"}
                </h1>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-stone-100 text-stone-700 border border-stone-200">
                  <Building2 className="w-3 h-3 mr-1 text-stone-500" />
                  ID: #{staff?.kitchen_id || 1}
                </span>
              </div>
              <div className="flex items-center space-x-3 mt-1">
                <span className="text-sm font-medium text-stone-600">
                  Logged in as <strong className="text-charcoal-900">{user?.first_name} {user?.last_name}</strong>
                </span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                    isManager ? "bg-purple-100 text-purple-700" : "bg-sky-100 text-sky-700"
                  }`}
                >
                  <ShieldCheck className="w-3 h-3 mr-1" />
                  {user?.role?.replace("_", " ")}
                </span>
              </div>
            </div>
          </div>

          {/* Operating Status & Manager Actions */}
          <div className="flex items-center space-x-3">
            {/* Low-stock warning pill */}
            {lowStockCount > 0 && (
              <Link
                to="/kitchen/inventory"
                className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 text-xs font-semibold hover:bg-amber-100 transition animate-pulse"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>{lowStockCount} Low Stock Item{lowStockCount > 1 ? "s" : ""}</span>
              </Link>
            )}

            {/* Kitchen Status Pill */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-2xl bg-stone-50 border border-stone-200">
              <span className="text-xs font-medium text-stone-500">Status:</span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${
                  getStatusColor(availability?.operating_status)
                }`}
              >
                {availability?.operating_status === "ACTIVE" && "Accepting Orders"}
                {availability?.operating_status === "PAUSED" && "Temporarily Paused"}
                {availability?.operating_status === "CLOSED" && "Kitchen Closed"}
                {!availability && "Checking..."}
              </span>
            </div>

            {/* Operating status control toggle (Managers Only) */}
            {isManager && (
              <button
                onClick={() => setShowStatusModal(true)}
                className="px-3.5 py-1.5 rounded-xl bg-charcoal-900 text-white text-xs font-semibold hover:bg-charcoal-800 transition flex items-center space-x-1.5 shadow-sm"
              >
                <Power className="w-3.5 h-3.5" />
                <span>Change Status</span>
              </button>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mt-8 border-t border-stone-100 pt-4">
          <nav className="flex space-x-2 sm:space-x-4 overflow-x-auto pb-1 scrollbar-none">
            {tabs.map((tab) => {
              const active = location.pathname === tab.path;
              const Icon = tab.icon;
              return (
                <Link
                  key={tab.path}
                  to={tab.path}
                  className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl text-sm font-semibold whitespace-nowrap transition-all duration-150 ${
                    active
                      ? "bg-terracotta-600 text-white shadow-md shadow-terracotta-600/20"
                      : "text-stone-600 hover:text-charcoal-900 hover:bg-stone-100/80"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                  {tab.badge && (
                    <span className="ml-1 px-1.5 py-0.2 bg-white text-terracotta-600 rounded-full text-xs font-bold">
                      {tab.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Page Header */}
      {(title || actionButton) && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            {title && <h2 className="text-2xl font-bold text-charcoal-900">{title}</h2>}
            {subtitle && <p className="text-sm text-stone-500 mt-0.5">{subtitle}</p>}
          </div>
          {actionButton && <div>{actionButton}</div>}
        </div>
      )}

      {/* Page Content */}
      {children}

      {/* Operating Status Modal for Kitchen Managers */}
      {showStatusModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-charcoal-900 mb-1">Set Kitchen Operating State</h3>
            <p className="text-xs text-stone-500 mb-6">
              Controlling operational availability dictates whether online customers can place new orders into this kitchen.
            </p>

            <div className="space-y-3 mb-6">
              <button
                disabled={statusLoading}
                onClick={() => handleStatusChange("ACTIVE")}
                className={`w-full flex items-center justify-between p-4 rounded-2xl border text-left transition ${
                  availability?.operating_status === "ACTIVE"
                    ? "border-emerald-500 bg-emerald-50/50"
                    : "border-stone-200 hover:border-emerald-300"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <Play className="w-5 h-5 fill-current" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-charcoal-900">Open Kitchen (Active)</h4>
                    <p className="text-xs text-stone-500">Accepting new customer orders normally</p>
                  </div>
                </div>
                {availability?.operating_status === "ACTIVE" && (
                  <span className="text-xs font-bold text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">Current</span>
                )}
              </button>

              <button
                disabled={statusLoading}
                onClick={() => handleStatusChange("PAUSED")}
                className={`w-full flex items-center justify-between p-4 rounded-2xl border text-left transition ${
                  availability?.operating_status === "PAUSED"
                    ? "border-amber-500 bg-amber-50/50"
                    : "border-stone-200 hover:border-amber-300"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
                    <Pause className="w-5 h-5 fill-current" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-charcoal-900">Pause Orders (Rush / Busy)</h4>
                    <p className="text-xs text-stone-500">Temporarily block incoming orders until queue clears</p>
                  </div>
                </div>
                {availability?.operating_status === "PAUSED" && (
                  <span className="text-xs font-bold text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">Current</span>
                )}
              </button>

              <button
                disabled={statusLoading}
                onClick={() => handleStatusChange("CLOSED")}
                className={`w-full flex items-center justify-between p-4 rounded-2xl border text-left transition ${
                  availability?.operating_status === "CLOSED"
                    ? "border-rose-500 bg-rose-50/50"
                    : "border-stone-200 hover:border-rose-300"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center">
                    <Power className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-charcoal-900">Close Kitchen</h4>
                    <p className="text-xs text-stone-500">Shut down ordering for end of shift / maintenance</p>
                  </div>
                </div>
                {availability?.operating_status === "CLOSED" && (
                  <span className="text-xs font-bold text-rose-600 bg-rose-100 px-2 py-0.5 rounded-full">Current</span>
                )}
              </button>
            </div>

            <div className="mb-6">
              <label className="block text-xs font-semibold text-stone-700 mb-1">
                Reason / Internal Log (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Extreme ticket rush, prep delay, or closing"
                value={statusReason}
                onChange={(e) => setStatusReason(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowStatusModal(false)}
                className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-sm transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
