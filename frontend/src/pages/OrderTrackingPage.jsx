import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  CheckCircle,
  Clock,
  ChefHat,
  Package,
  Bike,
  Home,
  AlertTriangle,
  RefreshCw,
  ChevronLeft,
  MapPin,
  Utensils,
} from "lucide-react";
import { orderApi } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";

const LIFECYCLE_STEPS = [
  { key: "PENDING", label: "Order Placed", icon: CheckCircle, desc: "Order registered with server" },
  { key: "CONFIRMED", label: "Kitchen Confirmed", icon: Utensils, desc: "Kitchen accepted ticket" },
  { key: "PREPARING", label: "Preparing Meal", icon: ChefHat, desc: "Chef actively cooking dishes" },
  { key: "READY_FOR_PICKUP", label: "Ready for Pickup", icon: Package, desc: "Packed in heat-retention bags" },
  { key: "OUT_FOR_DELIVERY", label: "Out for Delivery", icon: Bike, desc: "Delivery partner en route" },
  { key: "DELIVERED", label: "Delivered", icon: Home, desc: "Enjoy your culinary meal!" },
];

export const OrderTrackingPage = () => {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchOrder = async (isPoll = false) => {
    try {
      if (isPoll) setPolling(true);
      else setLoading(true);

      const resp = await orderApi.getOrderDetail(id);
      if (resp.data.success) {
        setOrder(resp.data.data);
      }
    } catch (err) {
      setErrorMsg("Failed to track order");
    } finally {
      setLoading(false);
      setPolling(false);
    }
  };

  useEffect(() => {
    fetchOrder();

    // Auto-polling interval every 8 seconds for real-time status progression
    const interval = setInterval(() => {
      fetchOrder(true);
    }, 8000);

    return () => clearInterval(interval);
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (errorMsg || !order) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-charcoal-900 mb-2">Order Not Found</h2>
        <p className="text-stone-500 mb-6">{errorMsg || "Unable to locate order tracking."}</p>
        <Link to="/orders" className="px-6 py-3 bg-stone-900 text-white font-bold rounded-2xl">
          Back to Orders
        </Link>
      </div>
    );
  }

  const isCancelled = order.order_status === "CANCELLED";

  // Calculate current active step index in lifecycle
  const currentStepIndex = LIFECYCLE_STEPS.findIndex((s) => s.key === order.order_status);

  // Map history timestamps
  const historyMap = {};
  order.status_history?.forEach((h) => {
    historyMap[h.new_status] = h.created_at;
  });

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <Link to={`/orders/${order.order_id}`} className="inline-flex items-center text-sm text-stone-500 hover:text-terracotta-600 mb-2">
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back to Order Details
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-black text-charcoal-900">
              Live Order Tracker
            </h1>
            <StatusBadge status={order.order_status} type="order" />
          </div>
          <p className="text-xs text-stone-400 mt-1 font-mono">
            Tracking Ticket: {order.order_number}
          </p>
        </div>

        <button
          onClick={() => fetchOrder(true)}
          className="inline-flex items-center px-4 py-2 bg-white border border-stone-200 text-stone-700 hover:bg-stone-50 rounded-xl text-xs font-semibold shadow-xs transition self-start sm:self-center"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${polling ? "animate-spin text-terracotta-600" : ""}`} />
          Auto-Refreshing Live
        </button>
      </div>

      {isCancelled ? (
        /* Cancelled State Banner */
        <div className="bg-red-50 border border-red-200 rounded-3xl p-8 text-center max-w-xl mx-auto shadow-sm">
          <div className="w-16 h-16 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-red-900 mb-2">Order Cancelled</h3>
          <p className="text-sm text-red-700 leading-relaxed">
            This order was cancelled and preparation has halted. Any payment made will be refunded according to the payment policy.
          </p>
          <Link
            to="/menu"
            className="mt-6 inline-flex px-6 py-2.5 bg-stone-900 text-white font-bold text-xs rounded-xl shadow"
          >
            Explore Menu & Reorder
          </Link>
        </div>
      ) : (
        /* Lifecycle Stepper Timeline */
        <div className="bg-white rounded-3xl p-6 sm:p-10 shadow-sm border border-stone-200/70 mb-8">
          <div className="space-y-8">
            {LIFECYCLE_STEPS.map((step, idx) => {
              const StepIcon = step.icon;
              const isPassed = currentStepIndex >= idx;
              const isCurrent = currentStepIndex === idx;
              const timestamp = historyMap[step.key];

              return (
                <div key={step.key} className="flex items-start space-x-4 sm:space-x-6 relative">
                  {/* Connecting Line between steps */}
                  {idx < LIFECYCLE_STEPS.length - 1 && (
                    <div
                      className={`absolute left-5 sm:left-6 top-12 w-0.5 h-10 -ml-[1px] transition-colors duration-300 ${
                        currentStepIndex > idx ? "bg-terracotta-600" : "bg-stone-200"
                      }`}
                    />
                  )}

                  {/* Icon Circle */}
                  <div
                    className={`w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all z-10 ${
                      isCurrent
                        ? "bg-terracotta-600 text-white ring-8 ring-terracotta-100 shadow-md shadow-terracotta-600/30"
                        : isPassed
                        ? "bg-emerald-600 text-white"
                        : "bg-stone-100 text-stone-400"
                    }`}
                  >
                    <StepIcon className="w-5 h-5 sm:w-6 sm:h-6" />
                  </div>

                  {/* Step Description & Timestamp */}
                  <div className="flex-1 min-w-0 pt-0.5 sm:pt-1">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between">
                      <h4
                        className={`text-base font-bold ${
                          isCurrent
                            ? "text-terracotta-700"
                            : isPassed
                            ? "text-charcoal-900"
                            : "text-stone-400"
                        }`}
                      >
                        {step.label}
                      </h4>
                      {timestamp && (
                        <span className="text-xs text-stone-400 font-mono mt-0.5 sm:mt-0">
                          {new Date(timestamp).toLocaleTimeString("en-IN", {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-stone-500 mt-1">{step.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Delivery & Kitchen Card */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70">
          <div className="flex items-center space-x-3 text-stone-700 mb-2">
            <Utensils className="w-4 h-4 text-terracotta-600" />
            <h4 className="font-bold text-sm text-charcoal-900">Preparing Kitchen</h4>
          </div>
          <p className="text-sm font-semibold text-charcoal-900">{order.kitchen?.name}</p>
          <p className="text-xs text-stone-500 mt-1">{order.kitchen?.address_line1}, {order.kitchen?.city}</p>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70">
          <div className="flex items-center space-x-3 text-stone-700 mb-2">
            <MapPin className="w-4 h-4 text-terracotta-600" />
            <h4 className="font-bold text-sm text-charcoal-900">Delivering To</h4>
          </div>
          <p className="text-sm font-semibold text-charcoal-900">{order.delivery_address?.recipient_name}</p>
          <p className="text-xs text-stone-500 mt-1 line-clamp-1">{order.delivery_address?.address_line1}</p>
        </div>
      </div>
    </div>
  );
};
