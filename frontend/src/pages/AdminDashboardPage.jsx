import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { 
  Users, 
  Building2, 
  UtensilsCrossed, 
  ShoppingBag, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  XCircle, 
  ArrowUpRight, 
  RefreshCw,
  TrendingUp,
  Tag,
  CreditCard,
  ShieldCheck
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

export const AdminDashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const resp = await adminApi.getDashboard();
      if (resp.data.success) {
        setStats(resp.data.data);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load dashboard statistics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <AdminLayout
      title="Platform Overview"
      subtitle="Executive summary of operations, revenue, and infrastructure"
      actions={
        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl text-xs font-bold transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Metrics</span>
        </button>
      }
    >
      {errorMsg && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl text-red-800 text-sm font-semibold">
          {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center text-stone-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-purple-600" />
          <p className="text-xs font-semibold">Calculating platform metrics from MySQL database...</p>
        </div>
      ) : stats ? (
        <div className="space-y-6">
          {/* Top Row: Revenue & Core Volume */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Net Revenue */}
            <div className="bg-gradient-to-br from-emerald-600 to-teal-800 rounded-2xl p-5 text-white shadow-md relative overflow-hidden">
              <span className="text-xs font-bold text-emerald-100 uppercase tracking-wider block">
                Verified Net Revenue
              </span>
              <div className="text-3xl font-black mt-1">
                ₹{Number(stats.total_revenue || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <p className="text-[11px] text-emerald-100/80 mt-1">
                * Successful payment captures only; excludes cancelled/refunded orders.
              </p>
              <TrendingUp className="w-16 h-16 text-white/10 absolute -right-2 -bottom-2" />
            </div>

            {/* Total Orders */}
            <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-stone-500 uppercase tracking-wider">All-Time Orders</span>
                <span className="p-2 rounded-xl bg-purple-50 text-purple-600">
                  <ShoppingBag className="w-4 h-4" />
                </span>
              </div>
              <div className="text-3xl font-black text-charcoal-900 mt-2">
                {stats.total_orders}
              </div>
              <div className="flex items-center space-x-2 mt-1 text-xs">
                <span className="font-bold text-emerald-600">+{stats.today_orders} today</span>
                <span className="text-stone-400">•</span>
                <span className="text-stone-500">{stats.delivered_orders} delivered</span>
              </div>
            </div>

            {/* Cloud Kitchens */}
            <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-stone-500 uppercase tracking-wider">Kitchen Facilities</span>
                <span className="p-2 rounded-xl bg-amber-50 text-amber-600">
                  <Building2 className="w-4 h-4" />
                </span>
              </div>
              <div className="text-3xl font-black text-charcoal-900 mt-2">
                {stats.active_kitchens} <span className="text-sm font-semibold text-stone-400">/ {stats.total_kitchens}</span>
              </div>
              <p className="text-xs text-stone-500 mt-1">
                Active operating cloud kitchens
              </p>
            </div>

            {/* User Community */}
            <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-stone-500 uppercase tracking-wider">Total Accounts</span>
                <span className="p-2 rounded-xl bg-blue-50 text-blue-600">
                  <Users className="w-4 h-4" />
                </span>
              </div>
              <div className="text-3xl font-black text-charcoal-900 mt-2">
                {stats.total_users}
              </div>
              <p className="text-xs text-stone-500 mt-1">
                {stats.total_customers} registered ordering customers
              </p>
            </div>
          </div>

          {/* Second Row: Operational Status Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Orders Pipeline Breakdown */}
            <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider flex items-center justify-between">
                <span>Orders Pipeline</span>
                <Link to="/admin/orders" className="text-xs text-purple-600 hover:underline inline-flex items-center">
                  <span>Manage</span>
                  <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
                </Link>
              </h3>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-stone-50">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-amber-500" />
                    <span className="text-xs font-semibold text-stone-700">Pending / In Preparation</span>
                  </div>
                  <span className="text-sm font-bold text-charcoal-900">{stats.pending_orders}</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-stone-50">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span className="text-xs font-semibold text-stone-700">Delivered Successfully</span>
                  </div>
                  <span className="text-sm font-bold text-charcoal-900">{stats.delivered_orders}</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-stone-50">
                  <div className="flex items-center space-x-2">
                    <XCircle className="w-4 h-4 text-red-500" />
                    <span className="text-xs font-semibold text-stone-700">Cancelled Orders</span>
                  </div>
                  <span className="text-sm font-bold text-charcoal-900">{stats.cancelled_orders}</span>
                </div>
              </div>
            </div>

            {/* Inventory Alerts Across Network */}
            <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider flex items-center justify-between">
                <span>Network Stock Health</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-amber-100 text-amber-800">
                  Real-time
                </span>
              </h3>

              <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/60 flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-amber-900">
                    {stats.low_stock_alerts_count} Low Stock Warnings
                  </h4>
                  <p className="text-[11px] text-amber-800/90 mt-0.5">
                    Ingredients falling below reorder thresholds across your kitchens.
                  </p>
                </div>
              </div>

              <div className="pt-2 text-xs text-stone-500">
                Total Master Menu Catalog: <strong>{stats.total_menu_items} active dishes</strong>
              </div>
            </div>

            {/* Administrative Quick Jump */}
            <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider">
                Management Modules
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs font-bold">
                <Link
                  to="/admin/users"
                  className="p-2.5 rounded-xl border border-stone-200 hover:border-purple-300 hover:bg-purple-50 text-stone-700 hover:text-purple-700 transition flex items-center space-x-2"
                >
                  <Users className="w-4 h-4" />
                  <span>Users</span>
                </Link>
                <Link
                  to="/admin/kitchens"
                  className="p-2.5 rounded-xl border border-stone-200 hover:border-purple-300 hover:bg-purple-50 text-stone-700 hover:text-purple-700 transition flex items-center space-x-2"
                >
                  <Building2 className="w-4 h-4" />
                  <span>Kitchens</span>
                </Link>
                <Link
                  to="/admin/orders"
                  className="p-2.5 rounded-xl border border-stone-200 hover:border-purple-300 hover:bg-purple-50 text-stone-700 hover:text-purple-700 transition flex items-center space-x-2"
                >
                  <ShoppingBag className="w-4 h-4" />
                  <span>Orders</span>
                </Link>
                <Link
                  to="/admin/analytics"
                  className="p-2.5 rounded-xl border border-stone-200 hover:border-purple-300 hover:bg-purple-50 text-stone-700 hover:text-purple-700 transition flex items-center space-x-2"
                >
                  <TrendingUp className="w-4 h-4" />
                  <span>Analytics</span>
                </Link>
                <Link
                  to="/admin/payments"
                  className="p-2.5 rounded-xl border border-stone-200 hover:border-purple-300 hover:bg-purple-50 text-stone-700 hover:text-purple-700 transition flex items-center space-x-2"
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Payments</span>
                </Link>
                <Link
                  to="/admin/audit-logs"
                  className="p-2.5 rounded-xl border border-stone-200 hover:border-purple-300 hover:bg-purple-50 text-stone-700 hover:text-purple-700 transition flex items-center space-x-2"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>Audit Logs</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </AdminLayout>
  );
};
