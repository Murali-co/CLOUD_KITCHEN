import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { 
  ArrowLeft, 
  Package, 
  MapPin, 
  Phone, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Navigation, 
  KeyRound, 
  Calendar,
  UtensilsCrossed,
  ShieldCheck,
  RefreshCw
} from "lucide-react";
import { DeliveryLayout } from "../components/DeliveryLayout";
import { deliveryApi } from "../services/api";

export const DeliveryDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [delivery, setDelivery] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [otpInput, setOtpInput] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const fetchDetail = async () => {
    try {
      setErrorMsg("");
      const resp = await deliveryApi.getAssignmentDetail(id);
      if (resp.data.success) {
        setDelivery(resp.data.data);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load assignment details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleStatusUpdate = async (nextStatus) => {
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const payload = { new_status: nextStatus };
      if (nextStatus === "DELIVERED") {
        if (!otpInput || otpInput.trim().length !== 4) {
          setErrorMsg("Please enter the 4-digit customer delivery OTP.");
          setActionLoading(false);
          return;
        }
        payload.delivery_otp = otpInput.trim();
      }

      const resp = await deliveryApi.updateStatus(id, payload);
      if (resp.data.success) {
        setSuccessMsg(`Status updated to ${nextStatus.replace(/_/g, " ")}!`);
        await fetchDetail();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Action rejected. Please check kitchen and delivery state.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <DeliveryLayout>
        <div className="py-20 text-center text-stone-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-terracotta-500" />
          <p className="text-sm">Loading delivery details...</p>
        </div>
      </DeliveryLayout>
    );
  }

  if (!delivery) {
    return (
      <DeliveryLayout>
        <div className="bg-white rounded-2xl p-8 text-center border border-stone-200">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-2" />
          <h2 className="text-base font-bold text-charcoal-900">Assignment Not Found</h2>
          <p className="text-xs text-stone-500 mt-1">This delivery assignment does not exist or you do not have permission to access it.</p>
          <Link
            to="/delivery/dashboard"
            className="mt-4 inline-block px-4 py-2 bg-terracotta-600 text-white rounded-xl text-xs font-bold"
          >
            Back to Dashboard
          </Link>
        </div>
      </DeliveryLayout>
    );
  }

  const isAssigned = delivery.delivery_status === "ASSIGNED";
  const isPickedUp = delivery.delivery_status === "PICKED_UP";
  const isOut = delivery.delivery_status === "OUT_FOR_DELIVERY";
  const isDelivered = delivery.delivery_status === "DELIVERED";

  return (
    <DeliveryLayout>
      <div className="space-y-5">
        {/* Top Back Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center space-x-1.5 text-xs font-bold text-stone-600 hover:text-charcoal-900"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <span
            className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${
              isDelivered
                ? "bg-emerald-100 text-emerald-800"
                : isOut
                ? "bg-purple-100 text-purple-800"
                : isPickedUp
                ? "bg-blue-100 text-blue-800"
                : "bg-amber-100 text-amber-800"
            }`}
          >
            {delivery.delivery_status.replace(/_/g, " ")}
          </span>
        </div>

        {/* Alerts */}
        {errorMsg && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl flex items-center space-x-3 text-red-800">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
            <p className="text-sm font-semibold">{errorMsg}</p>
          </div>
        )}
        {successMsg && (
          <div className="bg-emerald-50 border-l-4 border-emerald-500 p-4 rounded-xl flex items-center space-x-3 text-emerald-800">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-600" />
            <p className="text-sm font-semibold">{successMsg}</p>
          </div>
        )}

        {/* Action Panel for Active Deliveries */}
        {!isDelivered && (
          <div className="bg-gradient-to-br from-amber-500 to-terracotta-600 rounded-2xl p-5 text-white shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-amber-100 uppercase tracking-wider block">Required Action</span>
                <h3 className="text-lg font-black mt-0.5">
                  {isAssigned && "Step 1: Pick Up Order from Kitchen"}
                  {isPickedUp && "Step 2: Start Out-For-Delivery"}
                  {isOut && "Step 3: Hand Over to Customer & Verify OTP"}
                </h3>
              </div>
            </div>

            {isAssigned && (
              <div>
                <button
                  onClick={() => handleStatusUpdate("PICKED_UP")}
                  disabled={actionLoading}
                  className="w-full py-3 px-4 bg-white hover:bg-stone-50 text-charcoal-900 rounded-xl font-black text-sm shadow-md transition flex items-center justify-center space-x-2"
                >
                  <Package className="w-5 h-5 text-terracotta-600" />
                  <span>Confirm Kitchen Pickup</span>
                </button>
                <p className="text-[11px] text-amber-100/90 text-center mt-2">
                  * Note: Kitchen order status must be READY FOR PICKUP before confirming.
                </p>
              </div>
            )}

            {isPickedUp && (
              <div>
                <button
                  onClick={() => handleStatusUpdate("OUT_FOR_DELIVERY")}
                  disabled={actionLoading}
                  className="w-full py-3 px-4 bg-white hover:bg-stone-50 text-charcoal-900 rounded-xl font-black text-sm shadow-md transition flex items-center justify-center space-x-2"
                >
                  <Navigation className="w-5 h-5 text-blue-600" />
                  <span>Start Transit to Customer Address</span>
                </button>
              </div>
            )}

            {isOut && (
              <div className="space-y-3">
                <p className="text-xs text-amber-100">
                  Ask the customer for the 4-digit Delivery OTP sent to their phone/order screen:
                </p>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    maxLength={4}
                    placeholder="OTP (4 digits)"
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value.trim())}
                    className="w-36 text-center text-lg font-black tracking-widest text-charcoal-900 bg-white rounded-xl px-3 py-2 focus:outline-none"
                  />
                  <button
                    onClick={() => handleStatusUpdate("DELIVERED")}
                    disabled={actionLoading}
                    className="flex-1 py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black text-sm shadow-md transition flex items-center justify-center space-x-2"
                  >
                    <CheckCircle2 className="w-5 h-5" />
                    <span>Verify OTP & Mark Delivered</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Route Details Card */}
        <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider">Pickup & Drop-off Routing</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Kitchen */}
            <div className="bg-stone-50 rounded-xl p-4 border border-stone-200/80">
              <span className="text-xs font-bold text-stone-500 uppercase tracking-wider flex items-center space-x-1.5 mb-1.5">
                <span className="w-2 h-2 rounded-full bg-terracotta-500"></span>
                <span>Kitchen Pickup Location</span>
              </span>
              <h4 className="text-sm font-black text-charcoal-900">{delivery.kitchen_name}</h4>
              <p className="text-xs text-stone-600 mt-1 leading-relaxed">{delivery.kitchen_address}</p>
              {delivery.kitchen_phone && (
                <a
                  href={`tel:${delivery.kitchen_phone}`}
                  className="mt-3 inline-flex items-center text-xs font-bold text-terracotta-600 hover:underline"
                >
                  <Phone className="w-3.5 h-3.5 mr-1" />
                  <span>Call Kitchen: {delivery.kitchen_phone}</span>
                </a>
              )}
            </div>

            {/* Customer */}
            <div className="bg-stone-50 rounded-xl p-4 border border-stone-200/80">
              <span className="text-xs font-bold text-stone-500 uppercase tracking-wider flex items-center space-x-1.5 mb-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Customer Delivery Location</span>
              </span>
              <h4 className="text-sm font-black text-charcoal-900">{delivery.customer_name}</h4>
              <p className="text-xs text-stone-600 mt-1 leading-relaxed">{delivery.delivery_address}</p>
              {delivery.customer_phone && (
                <a
                  href={`tel:${delivery.customer_phone}`}
                  className="mt-3 inline-flex items-center text-xs font-bold text-emerald-600 hover:underline"
                >
                  <Phone className="w-3.5 h-3.5 mr-1" />
                  <span>Call Customer: {delivery.customer_phone}</span>
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Order Items Snapshot */}
        <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-stone-100 pb-2">
            <h2 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider">Order Items Checklist</h2>
            <span className="text-xs text-stone-500">{delivery.order_items?.length || 0} unique items</span>
          </div>

          <div className="divide-y divide-stone-100">
            {delivery.order_items?.map((itm, idx) => (
              <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-md bg-stone-100 text-charcoal-800 font-bold flex items-center justify-center text-[11px]">
                    {itm.quantity}x
                  </span>
                  <span className="font-semibold text-charcoal-900">{itm.item_name}</span>
                </div>
                <span className="text-stone-500 font-medium">₹{Number(itm.subtotal).toFixed(2)}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-stone-100 flex items-center justify-between text-xs font-bold text-charcoal-900">
            <span>Total Value</span>
            <span>₹{Number(delivery.total_amount).toFixed(2)}</span>
          </div>
        </div>

        {/* Timeline & Status History */}
        <div className="bg-white rounded-2xl p-5 border border-stone-200 shadow-sm space-y-3">
          <h2 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider">Status History Log</h2>
          <div className="space-y-3 text-xs text-stone-600">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-stone-400"></span>
              <span>Assigned At: <strong>{new Date(delivery.assigned_at).toLocaleString()}</strong></span>
            </div>
            {delivery.picked_up_at && (
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span>Picked Up: <strong>{new Date(delivery.picked_up_at).toLocaleString()}</strong></span>
              </div>
            )}
            {delivery.delivered_at && (
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Delivered: <strong>{new Date(delivery.delivered_at).toLocaleString()}</strong></span>
              </div>
            )}
          </div>
        </div>
      </div>
    </DeliveryLayout>
  );
};
