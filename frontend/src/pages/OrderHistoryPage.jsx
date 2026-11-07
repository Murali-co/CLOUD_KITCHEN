import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  ShoppingBag,
  Clock,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Utensils,
  MapPin,
  RefreshCw,
} from "lucide-react";
import { orderApi } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";

export const OrderHistoryPage = () => {
  const [orders, setOrders] = useState([]);
  const [meta, setMeta] = useState({ page: 1, total_pages: 1, total_count: 0 });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const fetchOrders = async (pageNum = 1) => {
    try {
      setLoading(true);
      const resp = await orderApi.listOrders(pageNum, 10);
      if (resp.data.success) {
        setOrders(resp.data.data.items);
        setMeta(resp.data.data.meta);
        setPage(pageNum);
      }
    } catch (err) {
      console.error("Orders list error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders(page);
  }, [page]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-charcoal-900 tracking-tight">Your Order History</h1>
          <p className="text-sm text-stone-500 mt-1">
            Review your past artisan kitchen orders, receipt breakdowns, and real-time delivery status.
          </p>
        </div>
        <button
          onClick={() => fetchOrders(page)}
          className="inline-flex items-center px-4 py-2 bg-white border border-stone-200 text-stone-700 hover:bg-stone-50 rounded-xl text-xs font-semibold shadow-xs transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {loading && orders.length === 0 ? (
        <div className="py-24 text-center">
          <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm text-stone-500">Loading your culinary orders...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="bg-white rounded-3xl p-16 text-center shadow-sm border border-stone-200/70 max-w-xl mx-auto">
          <div className="w-20 h-20 bg-stone-100 text-stone-400 rounded-full flex items-center justify-center mx-auto mb-5">
            <ShoppingBag className="w-10 h-10 stroke-[1.5]" />
          </div>
          <h3 className="text-xl font-bold text-charcoal-900 mb-2">No orders placed yet</h3>
          <p className="text-stone-500 text-sm mb-6">
            When you place your first gourmet meal order, you can track every step of preparation right here.
          </p>
          <Link
            to="/menu"
            className="inline-flex items-center px-6 py-3 bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold rounded-2xl shadow-md transition"
          >
            Explore Menu & Order Now
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((ord) => (
            <div
              key={ord.order_id}
              className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70 hover:border-stone-300 transition"
              id={`order-card-${ord.order_id}`}
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-stone-100">
                <div>
                  <div className="flex items-center space-x-3">
                    <span className="text-base font-extrabold text-charcoal-900 font-mono">
                      {ord.order_number}
                    </span>
                    <StatusBadge status={ord.order_status} type="order" />
                    {ord.payment_status && (
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-stone-100 text-stone-600 font-semibold uppercase">
                        {ord.payment_status}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-stone-400 mt-1">
                    Placed on {new Date(ord.placed_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
                  </p>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="text-xl font-black text-charcoal-900">
                    ₹{parseFloat(ord.total_amount).toFixed(2)}
                  </span>
                  <Link
                    to={`/orders/${ord.order_id}`}
                    className="px-4 py-2 bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-bold rounded-xl transition"
                  >
                    View Details
                  </Link>
                  <Link
                    to={`/orders/${ord.order_id}/track`}
                    className="px-4 py-2 bg-terracotta-600 hover:bg-terracotta-700 text-white text-xs font-bold rounded-xl shadow-xs transition flex items-center space-x-1"
                  >
                    <span>Track</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              {/* Kitchen & Quick item count preview */}
              <div className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-stone-500 gap-2">
                <span className="flex items-center">
                  <Utensils className="w-3.5 h-3.5 mr-1.5 text-terracotta-600" />
                  Kitchen: <strong className="text-stone-700 ml-1">{ord.kitchen_name}</strong>
                </span>
                <span className="flex items-center">
                  <Clock className="w-3.5 h-3.5 mr-1.5 text-stone-400" />
                  30–45 mins ETA
                </span>
              </div>
            </div>
          ))}

          {/* Pagination Controls */}
          {meta.total_pages > 1 && (
            <div className="flex items-center justify-between pt-6">
              <span className="text-xs text-stone-500">
                Page {meta.page} of {meta.total_pages} ({meta.total_count} total orders)
              </span>
              <div className="flex space-x-2">
                <button
                  disabled={!meta.has_prev}
                  onClick={() => setPage(page - 1)}
                  className="p-2 border border-stone-200 rounded-xl bg-white hover:bg-stone-50 disabled:opacity-40 transition"
                  title="Previous Page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={!meta.has_next}
                  onClick={() => setPage(page + 1)}
                  className="p-2 border border-stone-200 rounded-xl bg-white hover:bg-stone-50 disabled:opacity-40 transition"
                  title="Next Page"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
