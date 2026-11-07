import React, { useState, useEffect } from "react";
import { useLocation, useParams, useNavigate, Link } from "react-router-dom";
import {
  CheckCircle,
  Clock,
  MapPin,
  Utensils,
  CreditCard,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  ShoppingBag,
} from "lucide-react";
import { orderApi, paymentApi } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";

export const OrderConfirmationPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [order, setOrder] = useState(location.state?.order || null);
  const [loading, setLoading] = useState(!order);
  const [paying, setPaying] = useState(false);
  const [payError, setPayError] = useState(null);

  useEffect(() => {
    if (!order && id) {
      const fetchOrder = async () => {
        try {
          setLoading(true);
          const resp = await orderApi.getOrderDetail(id);
          if (resp.data.success) {
            setOrder(resp.data.data);
          }
        } catch (err) {
          console.error("Order load error:", err);
        } finally {
          setLoading(false);
        }
      };
      fetchOrder();
    }
  }, [id, order]);

  // Online Payment Simulation Workflow (Test Payment Provider)
  const handlePayNow = async () => {
    setPaying(true);
    setPayError(null);
    try {
      // 1. Create payment transaction via server API
      const createResp = await paymentApi.createPayment({
        order_id: order.order_id,
        payment_method: "UPI",
      });

      if (!createResp.data.success) {
        throw new Error(createResp.data.message || "Failed to initialize payment gateway");
      }

      const payData = createResp.data.data;

      // 2. Simulate gateway authorization & signature verification
      const verifyResp = await paymentApi.verifyPayment({
        order_id: order.order_id,
        transaction_reference: payData.transaction_reference,
        gateway_name: payData.gateway_name || "TestGateway",
        signature: payData.test_signature,
      });

      if (verifyResp.data.success) {
        // Refresh order details
        const refreshed = await orderApi.getOrderDetail(order.order_id);
        setOrder(refreshed.data.data);
      }
    } catch (err) {
      setPayError(err.response?.data?.detail || err.message || "Payment verification failed");
    } finally {
      setPaying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-charcoal-900 mb-2">Order Not Found</h2>
        <p className="text-stone-500 mb-6">We could not retrieve the details for this order.</p>
        <Link to="/orders" className="px-6 py-3 bg-stone-900 text-white font-bold rounded-2xl">
          View All Orders
        </Link>
      </div>
    );
  }

  const isConfirmed = order.order_status === "CONFIRMED";
  const isPendingPayment = order.order_status === "PENDING" && order.payments?.some((p) => p.payment_status === "PENDING");

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Success Hero Header */}
      <div className="bg-white rounded-3xl p-8 sm:p-12 shadow-sm border border-stone-200/70 text-center relative overflow-hidden mb-8">
        <div className="w-20 h-20 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-6 shadow-md">
          <CheckCircle className="w-10 h-10" />
        </div>

        <span className="text-xs font-bold uppercase tracking-wider text-terracotta-600 bg-terracotta-50 px-3 py-1 rounded-full">
          Order Successfully Received
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-charcoal-900 mt-3 mb-2 tracking-tight">
          Thank you for your order!
        </h1>
        <p className="text-stone-500 text-sm max-w-md mx-auto">
          Your order number is <strong className="text-charcoal-900 font-mono font-bold">{order.order_number}</strong>.
          We've dispatched your order details to the kitchen chef.
        </p>

        {/* Status Badges */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-stone-500 font-medium">Order Status:</span>
            <StatusBadge status={order.order_status} type="order" />
          </div>
          {order.payments?.[0] && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-stone-500 font-medium">Payment:</span>
              <StatusBadge status={order.payments[0].payment_status} type="payment" />
            </div>
          )}
        </div>
      </div>

      {/* Online Payment Notice (Test Gateway Mode) */}
      {!isConfirmed && (
        <div className="bg-amber-50 border border-amber-200 rounded-3xl p-6 sm:p-8 mb-8">
          <div className="flex items-start space-x-4">
            <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0 mt-0.5">
              <CreditCard className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-bold text-amber-900 mb-1">
                Complete Your Online Payment
              </h3>
              <p className="text-xs text-amber-800 mb-4 leading-relaxed">
                This order is in test payment mode. You can simulate instant gateway capture and cryptographic signature verification with one click.
              </p>
              {payError && (
                <p className="text-xs text-red-600 font-semibold mb-3 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {payError}
                </p>
              )}
              <button
                onClick={handlePayNow}
                disabled={paying}
                id="simulate-payment-btn"
                className="px-6 py-3 bg-terracotta-600 hover:bg-terracotta-700 disabled:opacity-50 text-white text-sm font-bold rounded-2xl shadow-md transition flex items-center space-x-2"
              >
                <span>{paying ? "Verifying Signature..." : "Simulate Payment Capture (₹" + parseFloat(order.total_amount).toFixed(2) + ")"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Order Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* Left: Items Summary */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70 space-y-4">
          <h3 className="text-base font-bold text-charcoal-900 border-b border-stone-100 pb-3 flex items-center">
            <Utensils className="w-4 h-4 mr-2 text-terracotta-600" />
            Ordered Items ({order.items?.length || 0})
          </h3>
          <div className="divide-y divide-stone-100">
            {order.items?.map((item) => (
              <div key={item.order_item_id} className="py-3 flex justify-between items-center text-sm">
                <div>
                  <p className="font-bold text-charcoal-900">{item.item_name_snapshot}</p>
                  <p className="text-xs text-stone-500">
                    {item.quantity} × ₹{parseFloat(item.unit_price_snapshot).toFixed(2)}
                  </p>
                </div>
                <span className="font-extrabold text-charcoal-900">
                  ₹{parseFloat(item.subtotal_price).toFixed(2)}
                </span>
              </div>
            ))}
          </div>

          <div className="border-t border-stone-200 pt-4 space-y-2 text-sm text-stone-600">
            <div className="flex justify-between">
              <span>Subtotal</span>
              <span className="font-semibold text-charcoal-900">₹{parseFloat(order.subtotal_amount).toFixed(2)}</span>
            </div>
            {parseFloat(order.discount_amount) > 0 && (
              <div className="flex justify-between text-emerald-600 font-semibold">
                <span>Discount</span>
                <span>-₹{parseFloat(order.discount_amount).toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span>Delivery Fee</span>
              <span className="font-semibold text-charcoal-900">₹{parseFloat(order.delivery_fee).toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>GST & Taxes</span>
              <span className="font-semibold text-charcoal-900">₹{parseFloat(order.tax_amount).toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t border-stone-200 pt-2 text-base font-black text-charcoal-900">
              <span>Total Paid / Payable</span>
              <span className="text-terracotta-700">₹{parseFloat(order.total_amount).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Right: Delivery & Kitchen details */}
        <div className="space-y-6">
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <h3 className="text-base font-bold text-charcoal-900 border-b border-stone-100 pb-3 flex items-center">
              <MapPin className="w-4 h-4 mr-2 text-terracotta-600" />
              Delivery Destination
            </h3>
            {order.delivery_address && (
              <div className="mt-4 text-sm space-y-1">
                <p className="font-bold text-charcoal-900">{order.delivery_address.recipient_name}</p>
                <p className="text-stone-600">{order.delivery_address.address_line1}</p>
                <p className="text-stone-600">
                  {order.delivery_address.city}, {order.delivery_address.state} - {order.delivery_address.postal_code}
                </p>
                <p className="text-stone-400 text-xs mt-2">{order.delivery_address.recipient_phone}</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <h3 className="text-base font-bold text-charcoal-900 border-b border-stone-100 pb-3 flex items-center">
              <Clock className="w-4 h-4 mr-2 text-terracotta-600" />
              Estimated Delivery
            </h3>
            <p className="mt-4 text-2xl font-black text-charcoal-900">30–45 Minutes</p>
            <p className="text-xs text-stone-500 mt-1">
              Freshly prepped at {order.kitchen?.name || "Cloud Kitchen Hub"}
            </p>
          </div>
        </div>
      </div>

      {/* Action Navigation Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link
          to={`/orders/${order.order_id}/track`}
          id="track-order-live-btn"
          className="w-full sm:w-auto px-8 py-4 bg-stone-900 hover:bg-stone-800 text-white font-bold rounded-2xl shadow flex items-center justify-center space-x-2 transition"
        >
          <span>Track Order Lifecycle</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
        <Link
          to="/orders"
          className="w-full sm:w-auto px-8 py-4 bg-white border border-stone-200 text-stone-700 hover:bg-stone-50 font-bold rounded-2xl shadow-xs text-center transition"
        >
          View All My Orders
        </Link>
      </div>
    </div>
  );
};
