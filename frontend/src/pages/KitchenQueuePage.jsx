import React, { useState, useEffect } from "react";
import {
  Clock,
  Flame,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Utensils,
  ChevronRight,
  Timer,
  ShoppingBag,
  Bell,
  ArrowRight,
} from "lucide-react";
import { KitchenLayout } from "../components/KitchenLayout";
import { kitchenApi } from "../services/api";

export const KitchenQueuePage = () => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [pollInterval, setPollInterval] = useState(15); // seconds
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Status Action Modal State
  const [transitionOrder, setTransitionOrder] = useState(null);
  const [nextStatus, setNextStatus] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchQueue = async () => {
    try {
      const resp = await kitchenApi.getQueue();
      if (resp.data?.success) {
        setQueue(resp.data.data);
        setLastUpdated(new Date());
      }
    } catch (err) {
      console.error("Queue fetch error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    const timer = setInterval(fetchQueue, pollInterval * 1000);
    return () => clearInterval(timer);
  }, [pollInterval]);

  const handleManualRefresh = () => {
    setRefreshing(true);
    fetchQueue();
  };

  const handleOpenTransition = (order, status) => {
    setTransitionOrder(order);
    setNextStatus(status);
    setNotes("");
    setErrorMsg("");
  };

  const executeTransition = async () => {
    if (!transitionOrder || !nextStatus) return;
    setSubmitting(true);
    setErrorMsg("");
    try {
      const resp = await kitchenApi.updateOrderStatus(transitionOrder.order_id, {
        status: nextStatus,
        notes: notes.trim() || undefined,
      });
      if (resp.data?.success) {
        setTransitionOrder(null);
        setNextStatus("");
        fetchQueue();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Status update failed");
    } finally {
      setSubmitting(false);
    }
  };

  const getUrgencyBadge = (urgency, ageMinutes) => {
    if (urgency === "CRITICAL" || ageMinutes >= 30) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-black bg-rose-600 text-white animate-pulse shadow-sm">
          <AlertTriangle className="w-3.5 h-3.5 mr-1" />
          DELAYED ({ageMinutes}m)
        </span>
      );
    }
    if (urgency === "HIGH" || ageMinutes >= 15) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500 text-white">
          <Clock className="w-3.5 h-3.5 mr-1" />
          RUSH ({ageMinutes}m)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-700">
        <Clock className="w-3.5 h-3.5 mr-1 text-stone-400" />
        {ageMinutes}m ago
      </span>
    );
  };

  return (
    <KitchenLayout
      title="Live Kitchen Expediter Queue"
      subtitle="Orders prioritized by wait duration, rush status, and station progression"
      actionButton={
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-stone-500 bg-white px-3 py-1.5 rounded-xl border border-stone-200">
            <Timer className="w-3.5 h-3.5 text-stone-400" />
            <span>Poll every:</span>
            <select
              value={pollInterval}
              onChange={(e) => setPollInterval(Number(e.target.value))}
              className="font-bold text-charcoal-900 focus:outline-none bg-transparent cursor-pointer"
            >
              <option value={10}>10s</option>
              <option value={15}>15s</option>
              <option value={30}>30s</option>
            </select>
          </div>

          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-white border border-stone-200 rounded-xl text-stone-700 text-xs font-semibold hover:bg-stone-50 transition shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-terracotta-600" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      }
    >
      {/* Real-time Status Notice */}
      <div className="p-3.5 rounded-2xl bg-stone-100 border border-stone-200/80 mb-6 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-stone-600 gap-2">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
          <span>
            Connected to <strong>Kitchen Queue Cache (TTL 30s)</strong>. Real timestamps calculated against MySQL master.
          </span>
        </div>
        <span className="text-stone-400 text-[11px]">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </span>
      </div>

      {/* Queue Grid: Ticket Cards */}
      {loading ? (
        <div className="py-24 text-center">
          <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm font-semibold text-stone-600">Syncing live kitchen order stream...</p>
        </div>
      ) : queue.length === 0 ? (
        <div className="py-24 text-center bg-white rounded-3xl border border-stone-200 p-8 shadow-sm">
          <Utensils className="w-12 h-12 text-stone-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-charcoal-900 mb-1">Queue is clear!</h3>
          <p className="text-xs text-stone-500 max-w-md mx-auto">
            All current tickets have been prepped or completed. As soon as a customer places an order, it will appear here instantly.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {queue.map((item) => (
            <div
              key={item.order_id}
              className={`rounded-3xl bg-white border p-6 flex flex-col justify-between shadow-sm transition-all duration-200 ${
                item.urgency === "CRITICAL"
                  ? "border-rose-400 ring-2 ring-rose-400/20 bg-rose-50/10"
                  : item.urgency === "HIGH"
                  ? "border-amber-300"
                  : "border-stone-200/80 hover:border-terracotta-300"
              }`}
            >
              <div>
                {/* Header: Ticket Number & Urgency Badge */}
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xl font-black text-charcoal-900 tracking-tight">
                    {item.order_number}
                  </span>
                  {getUrgencyBadge(item.urgency, item.age_minutes)}
                </div>

                {/* Status Indicator */}
                <div className="mb-4 flex items-center space-x-2">
                  <span className="text-xs text-stone-400">Current Phase:</span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-extrabold uppercase tracking-wider ${
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

                {/* Customer and Order Summary */}
                <div className="p-3.5 rounded-2xl bg-stone-50 border border-stone-100 mb-4 text-xs space-y-1">
                  <div className="flex justify-between text-stone-600">
                    <span>Customer:</span>
                    <strong className="text-charcoal-900">{item.customer_name}</strong>
                  </div>
                  <div className="flex justify-between text-stone-600">
                    <span>Order Size:</span>
                    <strong className="text-charcoal-900">{item.item_count} items</strong>
                  </div>
                  <div className="flex justify-between text-stone-600">
                    <span>Ticket Value:</span>
                    <strong className="text-charcoal-900">₹{parseFloat(item.total_amount).toFixed(2)}</strong>
                  </div>
                </div>
              </div>

              {/* Action Controls for Staff */}
              <div className="pt-4 border-t border-stone-100 space-y-2">
                {item.order_status === "PLACED" && (
                  <button
                    onClick={() => handleOpenTransition(item, "CONFIRMED")}
                    className="w-full py-2.5 rounded-2xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs transition shadow-sm flex items-center justify-center space-x-1.5"
                  >
                    <span>Accept & Confirm Ticket</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                )}

                {item.order_status === "CONFIRMED" && (
                  <button
                    onClick={() => handleOpenTransition(item, "PREPARING")}
                    className="w-full py-2.5 rounded-2xl bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold text-xs transition shadow-sm flex items-center justify-center space-x-1.5"
                  >
                    <Flame className="w-4 h-4" />
                    <span>Fire Ticket (Deduct Stock)</span>
                  </button>
                )}

                {item.order_status === "PREPARING" && (
                  <button
                    onClick={() => handleOpenTransition(item, "READY_FOR_PICKUP")}
                    className="w-full py-2.5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition shadow-sm flex items-center justify-center space-x-1.5"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Ready for Courier Handoff</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action Confirmation Modal */}
      {transitionOrder && nextStatus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-charcoal-900 mb-1">
              Advance Ticket: {transitionOrder.order_number}
            </h3>
            <p className="text-xs text-stone-500 mb-4">
              Moving from <strong>{transitionOrder.order_status}</strong> to <strong>{nextStatus}</strong>.
            </p>

            {nextStatus === "PREPARING" && (
              <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 mb-4 leading-relaxed">
                <strong>Cooking Station Alert:</strong> Moving to PREPARING will atomically verify and deduct recipe ingredients from kitchen storage.
              </div>
            )}

            {errorMsg && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium mb-4">
                {errorMsg}
              </div>
            )}

            <div className="mb-5">
              <label className="block text-xs font-semibold text-stone-700 mb-1">Station Note (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Grilling underway, ETA 12 mins"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                disabled={submitting}
                onClick={() => setTransitionOrder(null)}
                className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-xs transition"
              >
                Cancel
              </button>
              <button
                disabled={submitting}
                onClick={executeTransition}
                className="px-5 py-2 rounded-xl bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold text-xs transition shadow-sm flex items-center space-x-1.5"
              >
                {submitting && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                <span>Advance State</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </KitchenLayout>
  );
};
