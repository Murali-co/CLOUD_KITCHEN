import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  Utensils,
  MapPin,
  Clock,
  CreditCard,
  Ban,
  AlertCircle,
  CheckCircle,
  FileText,
  ArrowRight,
} from "lucide-react";
import { orderApi, paymentApi } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";

export const OrderDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchOrderDetail = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const resp = await orderApi.getOrderDetail(id);
      if (resp.data.success) {
        setOrder(resp.data.data);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Could not retrieve order details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrderDetail();
  }, [id]);

  const handleCancelOrder = async (e) => {
    e.preventDefault();
    if (!cancelReason.trim()) {
      alert("Please provide a reason for cancellation");
      return;
    }
    setCancelling(true);
    try {
      const resp = await orderApi.cancelOrder(order.order_id, cancelReason.trim());
      if (resp.data.success) {
        setShowCancelModal(false);
        await fetchOrderDetail();
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to cancel order");
    } finally {
      setCancelling(false);
    }
  };

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
        <p className="text-stone-500 mb-6">{errorMsg || "The requested order could not be located."}</p>
        <Link to="/orders" className="px-6 py-3 bg-stone-900 text-white font-bold rounded-2xl">
          Back to Order History
        </Link>
      </div>
    );
  }

  // Can cancel if order is in PENDING or CONFIRMED state
  const canCancel = order.order_status === "PENDING" || order.order_status === "CONFIRMED";

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header & Back */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <Link to="/orders" className="inline-flex items-center text-sm text-stone-500 hover:text-terracotta-600 mb-2">
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back to Orders
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-black text-charcoal-900 font-mono">
              {order.order_number}
            </h1>
            <StatusBadge status={order.order_status} type="order" />
          </div>
          <p className="text-xs text-stone-400 mt-1">
            Placed on {new Date(order.placed_at).toLocaleString("en-IN", { dateStyle: "full", timeStyle: "medium" })}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to={`/orders/${order.order_id}/track`}
            className="px-5 py-2.5 bg-stone-900 hover:bg-stone-800 text-white font-bold rounded-xl text-xs shadow-xs transition flex items-center space-x-1.5"
          >
            <span>Live Tracking</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          {canCancel && (
            <button
              onClick={() => setShowCancelModal(true)}
              id="cancel-order-button"
              className="px-4 py-2.5 bg-red-50 hover:bg-red-100 text-red-700 font-bold rounded-xl text-xs border border-red-200 transition"
            >
              Cancel Order
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Items Snapshot & Pricing Details */}
        <div className="lg:col-span-8 space-y-6">
          {/* Order Items Table */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <h3 className="text-base font-bold text-charcoal-900 border-b border-stone-100 pb-4 mb-4 flex items-center">
              <Utensils className="w-4 h-4 mr-2 text-terracotta-600" />
              Itemized Dish Receipt
            </h3>

            <div className="divide-y divide-stone-100">
              {order.items?.map((item) => (
                <div key={item.order_item_id} className="py-4 flex justify-between items-start text-sm">
                  <div>
                    <h4 className="font-bold text-charcoal-900 text-base">{item.item_name_snapshot}</h4>
                    <p className="text-xs text-stone-500 mt-0.5">
                      {item.quantity} × ₹{parseFloat(item.unit_price_snapshot).toFixed(2)}
                    </p>
                    {item.customization_notes && (
                      <p className="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded mt-1.5 inline-block">
                        Note: {item.customization_notes}
                      </p>
                    )}
                  </div>
                  <span className="font-black text-charcoal-900 text-base">
                    ₹{parseFloat(item.subtotal_price).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>

            {/* Bill Calculation */}
            <div className="border-t border-stone-200 mt-6 pt-4 space-y-2 text-sm text-stone-600">
              <div className="flex justify-between">
                <span>Items Subtotal</span>
                <span className="font-semibold text-charcoal-900">₹{parseFloat(order.subtotal_amount).toFixed(2)}</span>
              </div>
              {parseFloat(order.discount_amount) > 0 && (
                <div className="flex justify-between text-emerald-600 font-semibold">
                  <span>Promo Code Savings</span>
                  <span>-₹{parseFloat(order.discount_amount).toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span>Delivery Partner Charge</span>
                <span className="font-semibold text-charcoal-900">₹{parseFloat(order.delivery_fee).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>GST & Statutory Taxes</span>
                <span className="font-semibold text-charcoal-900">₹{parseFloat(order.tax_amount).toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-stone-200 pt-3 text-lg font-black text-charcoal-900">
                <span>Grand Total</span>
                <span className="text-terracotta-700">₹{parseFloat(order.total_amount).toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Status History Timeline */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <h3 className="text-base font-bold text-charcoal-900 border-b border-stone-100 pb-4 mb-6 flex items-center">
              <Clock className="w-4 h-4 mr-2 text-terracotta-600" />
              Official Audit Status Timeline
            </h3>

            <div className="relative pl-6 border-l-2 border-stone-200 space-y-6">
              {order.status_history?.map((hist, idx) => (
                <div key={hist.history_id || idx} className="relative">
                  <span className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-terracotta-600 ring-4 ring-terracotta-100" />
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-terracotta-700">
                      {hist.new_status}
                    </span>
                    <p className="text-xs text-stone-400">
                      {new Date(hist.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "medium" })}
                    </p>
                    {hist.notes && (
                      <p className="text-xs text-stone-600 bg-stone-50 p-2 rounded-xl mt-1 border border-stone-100">
                        {hist.notes}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Kitchen & Fulfillment Info */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Cloud Kitchen</h3>
            <p className="font-bold text-charcoal-900 text-base">{order.kitchen?.name}</p>
            <p className="text-xs text-stone-500">{order.kitchen?.address_line1}, {order.kitchen?.city}</p>
            <p className="text-xs text-stone-400">Contact: {order.kitchen?.contact_phone}</p>
          </div>

          <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Delivery Address</h3>
            <p className="font-bold text-charcoal-900 text-sm">{order.delivery_address?.recipient_name}</p>
            <p className="text-xs text-stone-600 leading-relaxed">
              {order.delivery_address?.address_line1}, {order.delivery_address?.city} - {order.delivery_address?.postal_code}
            </p>
            <p className="text-xs text-stone-400">Phone: {order.delivery_address?.recipient_phone}</p>
          </div>

          <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Payment Details</h3>
            <div className="flex justify-between items-center text-sm">
              <span className="text-stone-600">Method</span>
              <span className="font-bold text-charcoal-900">{order.payments?.[0]?.payment_method || "Online"}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-stone-600">Status</span>
              <StatusBadge status={order.payments?.[0]?.payment_status || "PENDING"} type="payment" />
            </div>
            {order.payments?.[0]?.transaction_reference && (
              <div className="pt-2 border-t border-stone-100 text-xs">
                <span className="text-stone-400 block">Ref ID</span>
                <span className="font-mono text-stone-600 break-all">{order.payments[0].transaction_reference}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Cancellation Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-stone-200">
            <div className="w-12 h-12 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center mb-4">
              <Ban className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-charcoal-900 mb-2">Cancel Order</h3>
            <p className="text-xs text-stone-500 mb-4">
              Orders can only be cancelled before the kitchen begins active cooking. Please provide a reason:
            </p>
            <form onSubmit={handleCancelOrder} className="space-y-4">
              <textarea
                required
                rows={3}
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="e.g. Ordered by mistake, wrong delivery address..."
                className="w-full px-4 py-3 bg-stone-50 border border-stone-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
              />
              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCancelModal(false)}
                  className="flex-1 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-700 font-semibold rounded-xl text-sm"
                >
                  Keep Order
                </button>
                <button
                  type="submit"
                  disabled={cancelling}
                  className="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-xl text-sm shadow"
                >
                  {cancelling ? "Cancelling..." : "Confirm Cancel"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
