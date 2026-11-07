import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ShoppingBag,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Flame,
  ArrowRight,
  TrendingUp,
  Package,
  RefreshCw,
  Utensils,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";
import { KitchenLayout } from "../components/KitchenLayout";
import { kitchenApi, inventoryApi } from "../services/api";

export const KitchenDashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [queue, setQueue] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboardData = async () => {
    try {
      const [statsRes, queueRes, stockRes] = await Promise.all([
        kitchenApi.getDashboard(),
        kitchenApi.getQueue(),
        inventoryApi.getLowStockAlerts(),
      ]);

      if (statsRes.data?.success) setStats(statsRes.data.data);
      if (queueRes.data?.success) setQueue(queueRes.data.data.slice(0, 5));
      if (stockRes.data?.success) setLowStock(stockRes.data.data.slice(0, 4));
    } catch (err) {
      console.error("Failed to load kitchen dashboard metrics", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
  };

  if (loading) {
    return (
      <KitchenLayout>
        <div className="min-h-[50vh] flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin"></div>
        </div>
      </KitchenLayout>
    );
  }

  const statCards = [
    {
      label: "Today's Orders",
      value: stats?.total_orders_today ?? 0,
      icon: ShoppingBag,
      color: "text-stone-700 bg-stone-100",
      sub: "Cumulative volume",
    },
    {
      label: "New Incoming",
      value: stats?.placed_orders ?? 0,
      icon: AlertCircle,
      color: "text-amber-700 bg-amber-100",
      sub: "Needs confirmation",
      highlight: (stats?.placed_orders ?? 0) > 0,
    },
    {
      label: "Confirmed",
      value: stats?.confirmed_orders ?? 0,
      icon: Utensils,
      color: "text-sky-700 bg-sky-100",
      sub: "Ready for cook station",
    },
    {
      label: "Being Prepared",
      value: stats?.preparing_orders ?? 0,
      icon: Flame,
      color: "text-terracotta-600 bg-terracotta-100",
      sub: "On active burners",
    },
    {
      label: "Ready for Pickup",
      value: stats?.ready_orders ?? 0,
      icon: CheckCircle,
      color: "text-emerald-700 bg-emerald-100",
      sub: "At handoff counter",
    },
    {
      label: "Completed",
      value: stats?.completed_orders ?? 0,
      icon: TrendingUp,
      color: "text-stone-600 bg-stone-100",
      sub: "Fulfilled today",
    },
    {
      label: "Cancelled",
      value: stats?.cancelled_orders ?? 0,
      icon: XCircle,
      color: "text-rose-700 bg-rose-100",
      sub: "Refunded/Voided",
    },
  ];

  return (
    <KitchenLayout
      title="Kitchen Operations Overview"
      subtitle="Real-time order throughput, station workload, and inventory health"
      actionButton={
        <button
          onClick={handleManualRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white border border-stone-200 text-stone-700 text-xs font-semibold hover:bg-stone-50 transition shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-terracotta-600" : ""}`} />
          <span>Refresh Feed</span>
        </button>
      }
    >
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-5 rounded-3xl bg-white border transition shadow-sm ${
                card.highlight
                  ? "border-amber-400 bg-amber-50/20 ring-2 ring-amber-400/20"
                  : "border-stone-200/80"
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
                  {card.label}
                </span>
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${card.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-extrabold text-charcoal-900 tracking-tight">
                  {card.value}
                </span>
              </div>
              <p className="text-[11px] text-stone-500 mt-1">{card.sub}</p>
            </div>
          );
        })}

        {/* Kitchen Capacity Meter */}
        <div className="p-5 rounded-3xl bg-charcoal-900 text-white border border-charcoal-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-stone-400 uppercase tracking-wider">
                Kitchen Load
              </span>
              <span className="text-xs font-bold text-amber-400">
                {stats?.active_workload ?? 0} active tickets
              </span>
            </div>
            <div className="w-full bg-charcoal-800 rounded-full h-2.5 overflow-hidden my-2">
              <div
                className={`h-full transition-all duration-500 ${
                  (stats?.active_workload ?? 0) > 10
                    ? "bg-rose-500"
                    : (stats?.active_workload ?? 0) > 5
                    ? "bg-amber-400"
                    : "bg-emerald-400"
                }`}
                style={{
                  width: `${Math.min(100, Math.max(10, (stats?.active_workload ?? 0) * 10))}%`,
                }}
              ></div>
            </div>
          </div>
          <p className="text-[11px] text-stone-400">
            Optimal station throughput capacity is ~12 simultaneous tickets.
          </p>
        </div>
      </div>

      {/* Two Column Layout: Live Queue Preview & Inventory Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Live Queue Preview */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-3xl border border-stone-200/80 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-stone-100">
              <div className="flex items-center space-x-2">
                <Clock className="w-5 h-5 text-terracotta-600" />
                <h3 className="text-lg font-bold text-charcoal-900">Active Order Queue</h3>
              </div>
              <Link
                to="/kitchen/queue"
                className="text-xs font-bold text-terracotta-600 hover:text-terracotta-700 flex items-center space-x-1"
              >
                <span>Full Live Queue</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            {queue.length === 0 ? (
              <div className="py-12 text-center">
                <Utensils className="w-10 h-10 text-stone-300 mx-auto mb-2" />
                <p className="text-sm font-semibold text-stone-600">No active orders in the queue</p>
                <p className="text-xs text-stone-400">New orders placed by customers will appear here automatically.</p>
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {queue.map((item) => (
                  <div
                    key={item.order_id}
                    className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-stone-50/50 rounded-2xl px-2 transition"
                  >
                    <div className="flex items-start space-x-3">
                      <div
                        className={`w-10 h-10 rounded-2xl flex items-center justify-center text-xs font-extrabold uppercase shrink-0 ${
                          item.urgency === "CRITICAL"
                            ? "bg-rose-100 text-rose-700 ring-2 ring-rose-500/30"
                            : item.urgency === "HIGH"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-stone-100 text-stone-700"
                        }`}
                      >
                        #{item.order_id}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-bold text-charcoal-900">{item.order_number}</span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                              item.order_status === "PLACED"
                                ? "bg-amber-100 text-amber-800"
                                : item.order_status === "CONFIRMED"
                                ? "bg-sky-100 text-sky-800"
                                : item.order_status === "PREPARING"
                                ? "bg-terracotta-100 text-terracotta-700"
                                : "bg-emerald-100 text-emerald-800"
                            }`}
                          >
                            {item.order_status}
                          </span>
                        </div>
                        <p className="text-xs text-stone-500 mt-0.5">
                          {item.item_count} items • Placed {item.age_minutes}m ago
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 sm:self-center">
                      <span className="text-xs font-bold text-stone-700 mr-2">
                        ₹{parseFloat(item.total_amount).toFixed(2)}
                      </span>
                      <Link
                        to="/kitchen/orders"
                        className="px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-semibold transition"
                      >
                        Inspect Ticket
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Low Stock Alerts & Quick Navigation */}
        <div className="space-y-6">
          {/* Low Stock Warning Card */}
          <div className="bg-white rounded-3xl border border-stone-200/80 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-stone-100">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <h3 className="text-lg font-bold text-charcoal-900">Low-Stock Watchlist</h3>
              </div>
              <Link
                to="/kitchen/inventory"
                className="text-xs font-bold text-terracotta-600 hover:text-terracotta-700"
              >
                Stock Room
              </Link>
            </div>

            {lowStock.length === 0 ? (
              <div className="py-6 text-center">
                <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-1.5" />
                <p className="text-sm font-semibold text-charcoal-900">Inventory levels healthy</p>
                <p className="text-xs text-stone-400">All required ingredients exceed minimum reorder thresholds.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {lowStock.map((alert) => (
                  <div
                    key={alert.ingredient_id}
                    className="p-3.5 rounded-2xl bg-amber-50/60 border border-amber-200 flex items-center justify-between"
                  >
                    <div>
                      <h4 className="text-sm font-bold text-charcoal-900">{alert.ingredient_name}</h4>
                      <p className="text-xs text-amber-800">
                        Stock: <strong>{parseFloat(alert.current_stock).toFixed(2)}</strong> {alert.unit_of_measure} (Min: {parseFloat(alert.reorder_level).toFixed(2)})
                      </p>
                    </div>
                    <Link
                      to="/kitchen/inventory"
                      className="px-2.5 py-1 rounded-lg bg-amber-600 text-white text-xs font-bold hover:bg-amber-700 transition"
                    >
                      Stock In
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Operations Guide Card */}
          <div className="bg-stone-900 text-white rounded-3xl p-6 shadow-sm">
            <h4 className="text-base font-bold text-white mb-2">Automated Recipe Deduction</h4>
            <p className="text-xs text-stone-300 leading-relaxed mb-4">
              When an order is moved to <strong>PREPARING</strong>, our MySQL transaction engine atomically locks and deducts ingredient quantities from the kitchen stock room based on recipe specifications.
            </p>
            <div className="flex items-center space-x-3 text-xs text-amber-400 font-medium">
              <Package className="w-4 h-4 shrink-0" />
              <span>Prevents negative stock & rolls back if short</span>
            </div>
          </div>
        </div>
      </div>
    </KitchenLayout>
  );
};
