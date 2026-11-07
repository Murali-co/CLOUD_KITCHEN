import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { 
  Bike, 
  Package, 
  MapPin, 
  Phone, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  Check, 
  Navigation, 
  KeyRound, 
  RefreshCw,
  ShoppingBag
} from "lucide-react";
import { DeliveryLayout } from "../components/DeliveryLayout";
import { deliveryApi } from "../services/api";

export const DeliveryDashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [activeDeliveries, setActiveDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [otpInputs, setOtpInputs] = useState({});
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const fetchData = async () => {
    try {
      setErrorMsg("");
      const [statsResp, activeResp] = await Promise.all([
        deliveryApi.getDashboard(),
        deliveryApi.getAssignments({ is_active: true }),
      ]);
      if (statsResp.data.success) {
        setStats(statsResp.data.data);
      }
      if (activeResp.data.success) {
        setActiveDeliveries(activeResp.data.data.items || []);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load delivery dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStatusUpdate = async (deliveryId, nextStatus) => {
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const payload = { new_status: nextStatus };
      if (nextStatus === "DELIVERED") {
        const otp = otpInputs[deliveryId];
        if (!otp || otp.length !== 4) {
          setErrorMsg("Please enter the 4-digit customer delivery OTP.");
          setActionLoading(false);
          return;
        }
        payload.delivery_otp = otp;
      }

      const resp = await deliveryApi.updateStatus(deliveryId, payload);
      if (resp.data.success) {
        setSuccessMsg(`Order updated to ${nextStatus.replace(/_/g, " ")} successfully!`);
        await fetchData();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Action failed. Check order status prerequisites.");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <DeliveryLayout>
      <div className="space-y-6">
        {/* Alerts */}
        {errorMsg && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl flex items-center space-x-3 text-red-800 animate-in fade-in">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
            <p className="text-sm font-semibold">{errorMsg}</p>
          </div>
        )}
        {successMsg && (
          <div className="bg-emerald-50 border-l-4 border-emerald-500 p-4 rounded-xl flex items-center space-x-3 text-emerald-800 animate-in fade-in">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-600" />
            <p className="text-sm font-semibold">{successMsg}</p>
          </div>
        )}

        {/* Dashboard Metric Cards */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-stone-200/80">
              <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider block">Today Completed</span>
              <div className="text-2xl font-black text-emerald-600 mt-1">
                {stats.completed_today_count}
              </div>
              <span className="text-[11px] text-stone-400 mt-0.5 block">Delivered successfully</span>
            </div>

            <div className="bg-white rounded-2xl p-4 shadow-sm border border-stone-200/80">
              <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider block">Active Tasks</span>
              <div className="text-2xl font-black text-amber-600 mt-1">
                {stats.active_deliveries_count}
              </div>
              <span className="text-[11px] text-stone-400 mt-0.5 block">In flight now</span>
            </div>

            <div className="bg-white rounded-2xl p-4 shadow-sm border border-stone-200/80">
              <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider block">Pending Pickup</span>
              <div className="text-2xl font-black text-blue-600 mt-1">
                {stats.pending_pickup_count}
              </div>
              <span className="text-[11px] text-stone-400 mt-0.5 block">At kitchen</span>
            </div>

            <div className="bg-white rounded-2xl p-4 shadow-sm border border-stone-200/80">
              <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider block">Total Lifetime</span>
              <div className="text-2xl font-black text-charcoal-900 mt-1">
                {stats.total_deliveries_count}
              </div>
              <span className="text-[11px] text-stone-400 mt-0.5 block">Completed all-time</span>
            </div>
          </div>
        )}

        {/* Active Deliveries Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-charcoal-900 flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></span>
              <span>Active Assignments ({activeDeliveries.length})</span>
            </h2>
            <button
              onClick={fetchData}
              disabled={loading}
              className="text-xs font-semibold text-stone-600 hover:text-terracotta-600 flex items-center space-x-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>

          {activeDeliveries.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 text-center border border-dashed border-stone-300">
              <div className="w-14 h-14 bg-stone-100 rounded-full flex items-center justify-center mx-auto text-stone-400 mb-3">
                <Package className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-charcoal-900">No Active Deliveries</h3>
              <p className="text-xs text-stone-500 max-w-sm mx-auto mt-1">
                You currently have no pending pickup or out-for-delivery orders. Keep your availability status set to <strong className="text-emerald-600">ONLINE</strong> to receive new assignments.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {activeDeliveries.map((del) => {
                const isAssigned = del.delivery_status === "ASSIGNED";
                const isPickedUp = del.delivery_status === "PICKED_UP";
                const isOutForDelivery = del.delivery_status === "OUT_FOR_DELIVERY";

                return (
                  <div
                    key={del.delivery_id}
                    className="bg-white rounded-2xl border-2 border-amber-300/80 shadow-md p-5 space-y-4 transition hover:shadow-lg"
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                      <div>
                        <span className="text-xs font-bold text-terracotta-600 block">
                          Order #{del.order_number}
                        </span>
                        <span className="text-xs text-stone-400">
                          {del.item_count} items • Total: ₹{Number(del.total_amount).toFixed(2)}
                        </span>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${
                          isOutForDelivery
                            ? "bg-purple-100 text-purple-800 border border-purple-200"
                            : isPickedUp
                            ? "bg-blue-100 text-blue-800 border border-blue-200"
                            : "bg-amber-100 text-amber-800 border border-amber-200"
                        }`}
                      >
                        {del.delivery_status.replace(/_/g, " ")}
                      </span>
                    </div>

                    {/* Locations */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      {/* Kitchen Pickup */}
                      <div className="bg-stone-50 rounded-xl p-3 border border-stone-200/60">
                        <span className="font-bold text-stone-700 flex items-center space-x-1.5 mb-1">
                          <span className="w-2 h-2 rounded-full bg-terracotta-500"></span>
                          <span>PICKUP: {del.kitchen_name}</span>
                        </span>
                        <p className="text-stone-600 text-[11px] leading-relaxed">
                          {del.kitchen_address}
                        </p>
                        {del.kitchen_phone && (
                          <a
                            href={`tel:${del.kitchen_phone}`}
                            className="mt-2 inline-flex items-center text-[11px] font-bold text-terracotta-600 hover:underline"
                          >
                            <Phone className="w-3 h-3 mr-1" />
                            <span>Call Kitchen</span>
                          </a>
                        )}
                      </div>

                      {/* Customer Drop-off */}
                      <div className="bg-stone-50 rounded-xl p-3 border border-stone-200/60">
                        <span className="font-bold text-stone-700 flex items-center space-x-1.5 mb-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                          <span>DELIVERY: {del.customer_name}</span>
                        </span>
                        <p className="text-stone-600 text-[11px] leading-relaxed">
                          {del.delivery_address}
                        </p>
                        {del.customer_phone && (
                          <a
                            href={`tel:${del.customer_phone}`}
                            className="mt-2 inline-flex items-center text-[11px] font-bold text-emerald-600 hover:underline"
                          >
                            <Phone className="w-3 h-3 mr-1" />
                            <span>Call Customer</span>
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Action Panel based on state */}
                    <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 space-y-3">
                      <div className="flex items-center justify-between text-xs font-semibold text-amber-900">
                        <span>Workflow Stage</span>
                        <span>
                          {isAssigned && "1/3 • Ready for pickup at kitchen"}
                          {isPickedUp && "2/3 • Picked up, depart kitchen"}
                          {isOutForDelivery && "3/3 • Arrived at customer location"}
                        </span>
                      </div>

                      {/* State Button Transitions */}
                      {isAssigned && (
                        <div>
                          <button
                            onClick={() => handleStatusUpdate(del.delivery_id, "PICKED_UP")}
                            disabled={actionLoading}
                            id={`btn-pickup-${del.delivery_id}`}
                            className="w-full py-2.5 px-4 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-bold text-sm shadow-sm transition flex items-center justify-center space-x-2"
                          >
                            <Package className="w-4 h-4" />
                            <span>Confirm Order Pickup at Kitchen</span>
                          </button>
                          <p className="text-[11px] text-stone-500 text-center mt-1.5">
                            * Kitchen order status must be marked READY FOR PICKUP.
                          </p>
                        </div>
                      )}

                      {isPickedUp && (
                        <div>
                          <button
                            onClick={() => handleStatusUpdate(del.delivery_id, "OUT_FOR_DELIVERY")}
                            disabled={actionLoading}
                            id={`btn-out-delivery-${del.delivery_id}`}
                            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-sm shadow-sm transition flex items-center justify-center space-x-2"
                          >
                            <Navigation className="w-4 h-4" />
                            <span>Start Out-For-Delivery to Customer</span>
                          </button>
                        </div>
                      )}

                      {isOutForDelivery && (
                        <div className="space-y-2">
                          <label className="text-xs font-bold text-charcoal-900 block">
                            Enter Customer Delivery OTP (4 Digits)
                          </label>
                          <div className="flex space-x-2">
                            <input
                              type="text"
                              maxLength={4}
                              placeholder="e.g. 5432"
                              value={otpInputs[del.delivery_id] || ""}
                              onChange={(e) =>
                                setOtpInputs({ ...otpInputs, [del.delivery_id]: e.target.value.trim() })
                              }
                              id={`input-otp-${del.delivery_id}`}
                              className="w-36 text-center text-lg font-black tracking-widest bg-white border-2 border-purple-300 rounded-xl px-3 py-1.5 focus:outline-none focus:border-purple-600"
                            />
                            <button
                              onClick={() => handleStatusUpdate(del.delivery_id, "DELIVERED")}
                              disabled={actionLoading}
                              id={`btn-complete-${del.delivery_id}`}
                              className="flex-1 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-sm shadow-sm transition flex items-center justify-center space-x-2"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                              <span>Verify OTP & Complete Delivery</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* View Details Link */}
                    <div className="text-right pt-1">
                      <Link
                        to={`/delivery/assignments/${del.delivery_id}`}
                        className="text-xs font-bold text-terracotta-600 hover:underline inline-flex items-center space-x-1"
                      >
                        <span>View Full Order & Instructions</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </DeliveryLayout>
  );
};
