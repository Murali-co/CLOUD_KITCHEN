import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { CheckCircle2, XCircle, AlertCircle, ArrowRight, RotateCcw, ShoppingBag } from "lucide-react";
import { api } from "../services/api";

export function PaymentResultPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const orderId = searchParams.get("order_id") || searchParams.get("orderId");
  const statusParam = searchParams.get("status") || "success";
  const transactionRef = searchParams.get("transaction_ref") || searchParams.get("tx");
  const paymentId = searchParams.get("payment_id");

  const [loading, setLoading] = useState(false);
  const [order, setOrder] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (orderId) {
      setLoading(true);
      api
        .get(`/api/v1/orders/${orderId}`)
        .then((res) => {
          setOrder(res.data);
        })
        .catch((err) => {
          console.error("Failed to load order details:", err);
          setError("Could not retrieve latest order details.");
        })
        .finally(() => setLoading(false));
    }
  }, [orderId]);

  const isSuccess =
    statusParam.toLowerCase() === "success" ||
    order?.payment_status === "PAID" ||
    order?.status === "CONFIRMED";
  const isFailed = statusParam.toLowerCase() === "failed" || order?.payment_status === "FAILED";

  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      <div className="bg-white rounded-2xl shadow-sm border border-cream-300 p-8 text-center">
        {isSuccess ? (
          <div>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-12 h-12" />
            </div>
            <h1 className="text-3xl font-serif font-bold text-charcoal-900 mb-2">
              Payment Confirmed!
            </h1>
            <p className="text-charcoal-600 mb-6">
              Thank you! Your payment has been securely processed and your cloud kitchen order is now confirmed.
            </p>
          </div>
        ) : isFailed ? (
          <div>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-50 text-red-600 flex items-center justify-center">
              <XCircle className="w-12 h-12" />
            </div>
            <h1 className="text-3xl font-serif font-bold text-charcoal-900 mb-2">
              Payment Failed
            </h1>
            <p className="text-charcoal-600 mb-6">
              We were unable to process your transaction. No funds were captured for this order attempt.
            </p>
          </div>
        ) : (
          <div>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center">
              <AlertCircle className="w-12 h-12" />
            </div>
            <h1 className="text-3xl font-serif font-bold text-charcoal-900 mb-2">
              Payment Processing
            </h1>
            <p className="text-charcoal-600 mb-6">
              Your payment is currently being verified with the payment gateway.
            </p>
          </div>
        )}

        {/* Transaction Summary Card */}
        <div className="bg-cream-100 rounded-xl p-5 mb-8 text-left border border-cream-200">
          <div className="flex justify-between items-center py-2 border-b border-cream-200 text-sm">
            <span className="text-charcoal-500 font-medium">Order Number:</span>
            <span className="font-mono font-semibold text-charcoal-900">
              {order ? order.order_number : orderId ? `#${orderId}` : "N/A"}
            </span>
          </div>

          {transactionRef && (
            <div className="flex justify-between items-center py-2 border-b border-cream-200 text-sm">
              <span className="text-charcoal-500 font-medium">Transaction Reference:</span>
              <span className="font-mono text-xs text-charcoal-700 bg-white px-2 py-0.5 rounded border border-cream-300">
                {transactionRef}
              </span>
            </div>
          )}

          {paymentId && (
            <div className="flex justify-between items-center py-2 border-b border-cream-200 text-sm">
              <span className="text-charcoal-500 font-medium">Payment ID:</span>
              <span className="font-mono text-xs text-charcoal-700">{paymentId}</span>
            </div>
          )}

          {order && (
            <>
              <div className="flex justify-between items-center py-2 border-b border-cream-200 text-sm">
                <span className="text-charcoal-500 font-medium">Kitchen:</span>
                <span className="font-medium text-charcoal-800">{order.kitchen_name}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-cream-200 text-sm">
                <span className="text-charcoal-500 font-medium">Amount:</span>
                <span className="font-bold text-terracotta-600">₹{parseFloat(order.total_amount).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center py-2 text-sm">
                <span className="text-charcoal-500 font-medium">Order Status:</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-terracotta-100 text-terracotta-800">
                  {order.status}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          {isSuccess && orderId && (
            <>
              <Link
                to={`/orders/${orderId}/track`}
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl bg-terracotta-500 text-white font-medium hover:bg-terracotta-600 transition shadow-sm"
              >
                Track Live Order
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
              <Link
                to={`/orders/${orderId}`}
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl border border-cream-300 text-charcoal-700 font-medium hover:bg-cream-100 transition"
              >
                View Order Receipt
              </Link>
            </>
          )}

          {isFailed && (
            <>
              {orderId ? (
                <Link
                  to={`/orders/${orderId}/confirmation`}
                  className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl bg-terracotta-500 text-white font-medium hover:bg-terracotta-600 transition shadow-sm"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Retry Payment
                </Link>
              ) : (
                <Link
                  to="/checkout"
                  className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl bg-terracotta-500 text-white font-medium hover:bg-terracotta-600 transition shadow-sm"
                >
                  Back to Checkout
                </Link>
              )}
              <Link
                to="/cart"
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl border border-cream-300 text-charcoal-700 font-medium hover:bg-cream-100 transition"
              >
                Review Cart
              </Link>
            </>
          )}

          {!isSuccess && !isFailed && (
            <Link
              to="/orders"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl bg-terracotta-500 text-white font-medium hover:bg-terracotta-600 transition"
            >
              Go to Order History
            </Link>
          )}

          <Link
            to="/menu"
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl text-charcoal-500 hover:text-charcoal-800 transition"
          >
            <ShoppingBag className="w-4 h-4 mr-2" />
            Explore Menu
          </Link>
        </div>
      </div>
    </div>
  );
}
