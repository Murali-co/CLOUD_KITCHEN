import React, { useState, useEffect } from "react";
import { 
  BarChart3, 
  TrendingUp, 
  Calendar, 
  ShoppingBag, 
  DollarSign, 
  Truck, 
  Users, 
  Building2, 
  UtensilsCrossed, 
  CheckCircle2, 
  Clock, 
  RefreshCw,
  AlertCircle,
  PieChart,
  ArrowUpRight
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

export const AdminAnalyticsPage = () => {
  const [days, setDays] = useState(30);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const resp = await adminApi.getAnalytics(days);
      if (resp.data.success) {
        setAnalytics(resp.data.data);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load platform analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  // Max value calculation for bar scales
  const maxRevenue = analytics?.daily_metrics?.reduce((m, d) => Math.max(m, Number(d.revenue)), 0) || 1;
  const maxOrders = analytics?.daily_metrics?.reduce((m, d) => Math.max(m, Number(d.orders_count)), 0) || 1;

  return (
    <AdminLayout
      title="Platform Analytics & Intelligence"
      subtitle="Real-time multi-dimensional business performance calculated strictly from verified database records"
      actions={
        <div className="flex items-center space-x-2">
          {/* Day Window Selector */}
          <div className="inline-flex rounded-xl bg-stone-200/80 p-0.5 text-xs font-bold">
            {[
              { val: 7, label: "Last 7 Days" },
              { val: 30, label: "Last 30 Days" },
              { val: 90, label: "Last 90 Days" },
            ].map((tab) => (
              <button
                key={tab.val}
                onClick={() => setDays(tab.val)}
                className={`px-3 py-1.5 rounded-lg transition ${
                  days === tab.val
                    ? "bg-white text-purple-700 shadow-xs"
                    : "text-stone-600 hover:text-charcoal-900"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="p-2 border border-stone-300 rounded-xl bg-white hover:bg-stone-50 text-stone-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-purple-600" : ""}`} />
          </button>
        </div>
      }
    >
      {/* Notifications */}
      {errorMsg && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {loading && !analytics ? (
        <div className="py-20 text-center text-stone-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-purple-600" />
          <p className="text-sm font-bold text-charcoal-800">Computing Platform Analytics</p>
          <p className="text-xs text-stone-500 mt-1">Aggregating historical order ledgers and payment receipts...</p>
        </div>
      ) : !analytics ? (
        <div className="py-16 text-center text-stone-400 text-xs">
          No analytics data available for the selected timeframe.
        </div>
      ) : (
        <div className="space-y-6">
          {/* 1. KEY KPI CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-stone-500">Verified Net Revenue</span>
                <div className="p-2 bg-emerald-50 text-emerald-700 rounded-xl">
                  <DollarSign className="w-5 h-5" />
                </div>
              </div>
              <p className="text-2xl font-black text-charcoal-900 mt-2">
                ₹{Number(analytics.total_revenue).toFixed(2)}
              </p>
              <span className="text-[10px] text-emerald-600 font-bold flex items-center mt-1">
                <ArrowUpRight className="w-3 h-3 mr-0.5" />
                Verified successful payments only
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-stone-500">Total Volume</span>
                <div className="p-2 bg-purple-50 text-purple-700 rounded-xl">
                  <ShoppingBag className="w-5 h-5" />
                </div>
              </div>
              <p className="text-2xl font-black text-charcoal-900 mt-2">
                {analytics.total_orders}
              </p>
              <span className="text-[10px] text-stone-400 font-medium block mt-1">
                Completed & active orders
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-stone-500">Average Order Value</span>
                <div className="p-2 bg-blue-50 text-blue-700 rounded-xl">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </div>
              <p className="text-2xl font-black text-charcoal-900 mt-2">
                ₹{Number(analytics.average_order_value).toFixed(2)}
              </p>
              <span className="text-[10px] text-stone-400 font-medium block mt-1">
                Across all kitchens
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-stone-500">Avg Delivery Speed</span>
                <div className="p-2 bg-amber-50 text-amber-700 rounded-xl">
                  <Truck className="w-5 h-5" />
                </div>
              </div>
              <p className="text-2xl font-black text-charcoal-900 mt-2">
                {analytics.delivery_speed?.average_delivery_minutes
                  ? `${Math.round(analytics.delivery_speed.average_delivery_minutes)} min`
                  : "N/A"}
              </p>
              <span className="text-[10px] text-stone-400 font-medium block mt-1">
                {analytics.delivery_speed?.total_delivered || 0} orders delivered
              </span>
            </div>
          </div>

          {/* 2. DAILY TREND CHARTS */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Revenue Trend */}
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-charcoal-900 flex items-center space-x-1.5">
                  <DollarSign className="w-4 h-4 text-emerald-600" />
                  <span>Net Revenue by Day (₹)</span>
                </h3>
                <span className="text-[10px] font-mono text-stone-400">Past {days} days</span>
              </div>

              {analytics.daily_metrics?.length === 0 ? (
                <div className="py-12 text-center text-stone-400 text-xs">No daily revenue records found.</div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {analytics.daily_metrics?.map((d) => {
                    const pct = Math.min(100, Math.round((Number(d.revenue) / maxRevenue) * 100));
                    return (
                      <div key={d.date} className="flex items-center text-xs space-x-3">
                        <span className="w-20 font-mono text-stone-500 shrink-0 text-[11px]">{d.date}</span>
                        <div className="flex-1 bg-stone-100 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                            style={{ width: `${Math.max(pct, 2)}%` }}
                          />
                        </div>
                        <span className="w-24 text-right font-bold text-charcoal-900 text-[11px]">
                          ₹{Number(d.revenue).toFixed(2)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Orders Count Trend */}
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-charcoal-900 flex items-center space-x-1.5">
                  <ShoppingBag className="w-4 h-4 text-purple-600" />
                  <span>Order Volume by Day</span>
                </h3>
                <span className="text-[10px] font-mono text-stone-400">Past {days} days</span>
              </div>

              {analytics.daily_metrics?.length === 0 ? (
                <div className="py-12 text-center text-stone-400 text-xs">No daily order records found.</div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {analytics.daily_metrics?.map((d) => {
                    const pct = Math.min(100, Math.round((Number(d.orders_count) / maxOrders) * 100));
                    return (
                      <div key={d.date} className="flex items-center text-xs space-x-3">
                        <span className="w-20 font-mono text-stone-500 shrink-0 text-[11px]">{d.date}</span>
                        <div className="flex-1 bg-stone-100 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-purple-600 h-full rounded-full transition-all duration-300"
                            style={{ width: `${Math.max(pct, 2)}%` }}
                          />
                        </div>
                        <span className="w-20 text-right font-bold text-charcoal-900 text-[11px]">
                          {d.orders_count} orders
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* 3. POPULAR MENU ITEMS & KITCHEN PERFORMANCE */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Menu Items */}
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <h3 className="text-xs font-bold text-charcoal-900 flex items-center space-x-1.5 mb-3">
                <UtensilsCrossed className="w-4 h-4 text-purple-600" />
                <span>Top Selling Menu Offerings</span>
              </h3>

              {analytics.popular_items?.length === 0 ? (
                <div className="py-10 text-center text-stone-400 text-xs">No dish sales recorded yet.</div>
              ) : (
                <div className="divide-y divide-stone-100 text-xs">
                  {analytics.popular_items?.map((item, idx) => (
                    <div key={item.menu_item_id} className="py-2.5 flex items-center justify-between">
                      <div className="flex items-center space-x-2.5">
                        <span className="w-5 h-5 rounded-md bg-stone-100 text-stone-500 flex items-center justify-center font-bold text-[10px]">
                          #{idx + 1}
                        </span>
                        <div>
                          <p className="font-bold text-charcoal-900">{item.name}</p>
                          <span className="text-[10px] text-stone-400">{item.kitchen_name}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-charcoal-900">₹{Number(item.total_revenue).toFixed(2)}</p>
                        <span className="text-[10px] text-stone-500">{item.total_ordered_quantity} orders</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Kitchen Facility Performance */}
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <h3 className="text-xs font-bold text-charcoal-900 flex items-center space-x-1.5 mb-3">
                <Building2 className="w-4 h-4 text-purple-600" />
                <span>Cloud Kitchen Facility Performance</span>
              </h3>

              {analytics.kitchen_performance?.length === 0 ? (
                <div className="py-10 text-center text-stone-400 text-xs">No facility activity recorded.</div>
              ) : (
                <div className="divide-y divide-stone-100 text-xs">
                  {analytics.kitchen_performance?.map((k) => (
                    <div key={k.kitchen_id} className="py-2.5 flex items-center justify-between">
                      <div>
                        <p className="font-bold text-charcoal-900">{k.kitchen_name}</p>
                        <span className="text-[10px] text-stone-400">
                          {k.total_orders} total orders • AOV: ₹{Number(k.average_order_value).toFixed(2)}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="font-black text-charcoal-900">₹{Number(k.total_revenue).toFixed(2)}</p>
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">
                          {Number(k.completion_rate_percent).toFixed(1)}% fulfillment
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 4. STATUS DISTRIBUTIONS */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Order Status Distribution */}
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <h3 className="text-xs font-bold text-charcoal-900 mb-3 flex items-center space-x-1.5">
                <PieChart className="w-4 h-4 text-purple-600" />
                <span>Order Status Distribution</span>
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {analytics.order_status_distribution?.map((st) => (
                  <div key={st.status} className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center justify-between">
                    <span className="font-bold text-stone-600 text-[11px]">{st.status.replace(/_/g, " ")}</span>
                    <span className="font-mono font-black text-charcoal-900">{st.count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Payment Status Distribution */}
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
              <h3 className="text-xs font-bold text-charcoal-900 mb-3 flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Payment Verification Breakdown</span>
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {analytics.payment_status_distribution?.map((pt) => (
                  <div key={pt.status} className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center justify-between">
                    <span className="font-bold text-stone-600 text-[11px]">{pt.status}</span>
                    <span className="font-mono font-black text-charcoal-900">{pt.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};
