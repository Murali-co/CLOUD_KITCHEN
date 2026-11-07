import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  Calendar,
  Eye,
  CheckCircle,
  Clock,
  Flame,
  XCircle,
  AlertTriangle,
  FileText,
  User,
  MapPin,
  CreditCard,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  UtensilsCrossed,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { KitchenLayout } from "../components/KitchenLayout";
import { kitchenApi } from "../services/api";

export const KitchenOrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [loading, setLoading] = useState(true);

  // Selected Order Detail Modal State
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [orderDetail, setOrderDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Status Action Modal State
  const [statusActionOrder, setStatusActionOrder] = useState(null);
  const [targetStatus, setTargetStatus] = useState("");
  const [actionNotes, setActionNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (statusFilter) params.status = statusFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (dateFilter) params.date = dateFilter;

      const resp = await kitchenApi.getOrders(params);
      if (resp.data?.success) {
        setOrders(resp.data.data.items);
        setTotalCount(resp.data.data.meta.total_count);
      }
    } catch (err) {
      console.error("Failed to fetch kitchen orders", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [page, statusFilter, dateFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchOrders();
  };

  const handleOpenDetail = async (orderId) => {
    setSelectedOrderId(orderId);
    setDetailLoading(true);
    try {
      const resp = await kitchenApi.getOrderDetail(orderId);
      if (resp.data?.success) {
        setOrderDetail(resp.data.data);
      }
    } catch (err) {
      alert("Failed to load full order details");
      setSelectedOrderId(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const initiateStatusTransition = (order, nextStatus) => {
    setStatusActionOrder(order);
    setTargetStatus(nextStatus);
    setActionNotes("");
    setActionError("");
  };

  const executeStatusTransition = async () => {
    if (!statusActionOrder || !targetStatus) return;
    setActionLoading(true);
    setActionError("");
    try {
      const resp = await kitchenApi.updateOrderStatus(statusActionOrder.order_id, {
        status: targetStatus,
        notes: actionNotes.trim() || undefined,
      });

      if (resp.data?.success) {
        setStatusActionOrder(null);
        setTargetStatus("");
        // If detail modal is open for this order, refresh detail
        if (selectedOrderId === statusActionOrder.order_id) {
          setOrderDetail(resp.data.data);
        }
        fetchOrders();
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Order status transition failed";
      setActionError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const statusOptions = [
    { label: "All Statuses", value: "" },
    { label: "Placed", value: "PLACED" },
    { label: "Confirmed", value: "CONFIRMED" },
    { label: "Preparing", value: "PREPARING" },
    { label: "Ready for Pickup", value: "READY_FOR_PICKUP" },
    { label: "Completed", value: "COMPLETED" },
    { label: "Cancelled", value: "CANCELLED" },
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case "PLACED":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "CONFIRMED":
        return "bg-sky-100 text-sky-800 border-sky-200";
      case "PREPARING":
        return "bg-terracotta-100 text-terracotta-700 border-terracotta-200";
      case "READY_FOR_PICKUP":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "COMPLETED":
        return "bg-stone-100 text-stone-700 border-stone-200";
      case "CANCELLED":
        return "bg-rose-100 text-rose-800 border-rose-200";
      default:
        return "bg-stone-100 text-stone-700 border-stone-200";
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  return (
    <KitchenLayout
      title="Kitchen Order Management"
      subtitle="Inspect ticket specifications, advance cooking stages, and trace audit timelines"
      actionButton={
        <button
          onClick={fetchOrders}
          className="flex items-center space-x-2 px-4 py-2 bg-white border border-stone-200 rounded-xl text-stone-700 text-xs font-semibold hover:bg-stone-50 transition shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-terracotta-600" : ""}`} />
          <span>Refresh List</span>
        </button>
      }
    >
      {/* Filter & Search Bar */}
      <div className="bg-white rounded-3xl border border-stone-200/80 p-5 shadow-sm mb-6">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-stone-400" />
            <input
              type="text"
              placeholder="Search by Order # or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
            />
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3.5 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
            >
              {statusOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Date Filter */}
          <div>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => {
                setDateFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3.5 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
            />
          </div>

          {/* Submit / Reset Buttons */}
          <div className="flex items-center space-x-2">
            <button
              type="submit"
              className="flex-1 px-4 py-2.5 bg-terracotta-600 hover:bg-terracotta-700 text-white rounded-2xl text-xs font-bold transition shadow-sm"
            >
              Apply Filter
            </button>
            {(searchQuery || statusFilter || dateFilter) && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setStatusFilter("");
                  setDateFilter("");
                  setPage(1);
                }}
                className="px-3.5 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-600 rounded-2xl text-xs font-semibold transition"
              >
                Reset
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-3xl border border-stone-200/80 shadow-sm overflow-hidden mb-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-stone-50 border-b border-stone-200/80 text-xs font-bold text-stone-600 uppercase tracking-wider">
                <th className="py-4 px-6">Ticket</th>
                <th className="py-4 px-6">Customer</th>
                <th className="py-4 px-6">Items</th>
                <th className="py-4 px-6">Total & Payment</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6">Created</th>
                <th className="py-4 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-stone-400">
                    <div className="w-8 h-8 border-3 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-2"></div>
                    Loading kitchen tickets...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-stone-500">
                    No orders match the specified filter criteria.
                  </td>
                </tr>
              ) : (
                orders.map((o) => (
                  <tr key={o.order_id} className="hover:bg-stone-50/60 transition">
                    <td className="py-4 px-6">
                      <span className="font-extrabold text-charcoal-900 block">{o.order_number}</span>
                      <span className="text-[11px] text-stone-400">ID: #{o.order_id}</span>
                    </td>
                    <td className="py-4 px-6">
                      <span className="font-semibold text-charcoal-900 block">{o.customer_name}</span>
                      <span className="text-xs text-stone-500">{o.customer_phone || "—"}</span>
                    </td>
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-lg bg-stone-100 font-bold text-xs text-stone-800">
                        {o.item_count} items
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className="font-bold text-charcoal-900 block">
                        ₹{parseFloat(o.total_amount).toFixed(2)}
                      </span>
                      <span className="text-[11px] font-semibold text-stone-500 uppercase">
                        {o.payment_status} • {o.payment_method?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${getStatusBadge(
                          o.order_status
                        )}`}
                      >
                        {o.order_status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-xs text-stone-500">
                      {new Date(o.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      <span className="block text-[11px] text-stone-400">
                        {new Date(o.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right space-x-2 whitespace-nowrap">
                      {/* Quick Status Advance Button based on current status */}
                      {o.order_status === "PLACED" && (
                        <button
                          onClick={() => initiateStatusTransition(o, "CONFIRMED")}
                          className="px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition shadow-sm"
                        >
                          Confirm
                        </button>
                      )}
                      {o.order_status === "CONFIRMED" && (
                        <button
                          onClick={() => initiateStatusTransition(o, "PREPARING")}
                          className="px-3 py-1.5 rounded-xl bg-terracotta-600 hover:bg-terracotta-700 text-white text-xs font-bold transition shadow-sm"
                          title="Begins cooking and executes automatic recipe stock deduction"
                        >
                          Start Cooking
                        </button>
                      )}
                      {o.order_status === "PREPARING" && (
                        <button
                          onClick={() => initiateStatusTransition(o, "READY_FOR_PICKUP")}
                          className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-sm"
                        >
                          Mark Ready
                        </button>
                      )}

                      <button
                        onClick={() => handleOpenDetail(o.order_id)}
                        className="px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-semibold transition"
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {totalCount > pageSize && (
          <div className="p-4 border-t border-stone-100 flex items-center justify-between">
            <span className="text-xs text-stone-500">
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalCount)} of {totalCount} tickets
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-2 rounded-xl border border-stone-200 disabled:opacity-40 hover:bg-stone-50 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs font-bold text-stone-700">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="p-2 rounded-xl border border-stone-200 disabled:opacity-40 hover:bg-stone-50 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Full Order Detail Receipt Modal */}
      {selectedOrderId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in overflow-y-auto">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-2xl w-full p-6 shadow-2xl my-8 max-h-[90vh] overflow-y-auto">
            {detailLoading || !orderDetail ? (
              <div className="py-16 text-center">
                <div className="w-8 h-8 border-3 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-sm font-semibold text-stone-600">Retrieving ticket manifest...</p>
              </div>
            ) : (
              <div>
                {/* Header */}
                <div className="flex items-start justify-between pb-4 border-b border-stone-100 mb-6">
                  <div>
                    <span className="text-xs font-bold text-terracotta-600 uppercase tracking-wider block">
                      Kitchen Fulfillment Ticket
                    </span>
                    <h3 className="text-2xl font-black text-charcoal-900">{orderDetail.order_number}</h3>
                    <span className="text-xs text-stone-400">Order ID: #{orderDetail.order_id}</span>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${getStatusBadge(
                        orderDetail.order_status
                      )}`}
                    >
                      {orderDetail.order_status}
                    </span>
                    <p className="text-xs text-stone-400 mt-1">
                      {new Date(orderDetail.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Customer & Delivery Context */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-2xl bg-stone-50 border border-stone-200/80 mb-6">
                  <div>
                    <div className="flex items-center space-x-2 text-xs font-bold text-stone-500 uppercase mb-1">
                      <User className="w-3.5 h-3.5" />
                      <span>Customer</span>
                    </div>
                    <p className="text-sm font-bold text-charcoal-900">{orderDetail.customer_name}</p>
                    <p className="text-xs text-stone-600">{orderDetail.customer_phone || "Phone not provided"}</p>
                    <p className="text-xs text-stone-500">{orderDetail.customer_email}</p>
                  </div>

                  <div>
                    <div className="flex items-center space-x-2 text-xs font-bold text-stone-500 uppercase mb-1">
                      <MapPin className="w-3.5 h-3.5" />
                      <span>Delivery Destination</span>
                    </div>
                    {orderDetail.delivery_address ? (
                      <p className="text-xs text-stone-700 leading-snug">
                        {orderDetail.delivery_address.street_address}, {orderDetail.delivery_address.city} - {orderDetail.delivery_address.postal_code}
                      </p>
                    ) : (
                      <p className="text-xs text-stone-400">Pickup / Dine-in</p>
                    )}
                    <div className="mt-2 text-xs font-medium text-stone-600">
                      Payment: <strong className="text-charcoal-900">{orderDetail.payment_method}</strong> ({orderDetail.payment_status})
                    </div>
                  </div>
                </div>

                {/* Ordered Items Manifest */}
                <div className="mb-6">
                  <h4 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider mb-3">
                    Items to Prepare ({orderDetail.items?.length || 0})
                  </h4>
                  <div className="border border-stone-200 rounded-2xl divide-y divide-stone-100 overflow-hidden">
                    {orderDetail.items?.map((itm) => (
                      <div key={itm.order_item_id} className="p-3.5 flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className="w-7 h-7 rounded-lg bg-terracotta-100 text-terracotta-700 font-extrabold text-sm flex items-center justify-center shrink-0">
                            {itm.quantity}×
                          </span>
                          <div>
                            <span className="text-sm font-bold text-charcoal-900 block">{itm.item_name}</span>
                            <span className="text-xs text-stone-400">Unit: ₹{parseFloat(itm.unit_price).toFixed(2)}</span>
                          </div>
                        </div>
                        <span className="text-sm font-bold text-charcoal-900">
                          ₹{parseFloat(itm.subtotal).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>

                  {orderDetail.special_instructions && (
                    <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
                      <strong>Cooking Instructions:</strong> {orderDetail.special_instructions}
                    </div>
                  )}
                </div>

                {/* Status Timeline History */}
                <div className="mb-6">
                  <h4 className="text-sm font-bold text-charcoal-900 uppercase tracking-wider mb-3">
                    Audit Status Timeline
                  </h4>
                  <div className="border border-stone-200 rounded-2xl p-4 bg-stone-50/50 space-y-3">
                    {orderDetail.status_history?.map((hist, i) => (
                      <div key={hist.history_id || i} className="flex items-start space-x-3 text-xs">
                        <div className="w-2 h-2 rounded-full bg-terracotta-600 mt-1.5 shrink-0"></div>
                        <div className="flex-1">
                          <span className="font-bold text-charcoal-900">{hist.status}</span>
                          {hist.notes && <span className="text-stone-600"> — "{hist.notes}"</span>}
                          <p className="text-[11px] text-stone-400">
                            By User #{hist.changed_by_user_id || "System"} at {new Date(hist.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Available Status Actions */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-stone-100">
                  <div className="flex items-center space-x-2">
                    {orderDetail.order_status === "PLACED" && (
                      <button
                        onClick={() => initiateStatusTransition(orderDetail, "CONFIRMED")}
                        className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded-xl text-xs transition"
                      >
                        Confirm Order
                      </button>
                    )}
                    {orderDetail.order_status === "CONFIRMED" && (
                      <button
                        onClick={() => initiateStatusTransition(orderDetail, "PREPARING")}
                        className="px-4 py-2 bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold rounded-xl text-xs transition"
                      >
                        Start Cooking (Deduct Stock)
                      </button>
                    )}
                    {orderDetail.order_status === "PREPARING" && (
                      <button
                        onClick={() => initiateStatusTransition(orderDetail, "READY_FOR_PICKUP")}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition"
                      >
                        Mark Ready for Pickup
                      </button>
                    )}
                    {["PLACED", "CONFIRMED"].includes(orderDetail.order_status) && (
                      <button
                        onClick={() => initiateStatusTransition(orderDetail, "CANCELLED")}
                        className="px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold rounded-xl text-xs transition"
                      >
                        Cancel Ticket
                      </button>
                    )}
                  </div>

                  <button
                    onClick={() => setSelectedOrderId(null)}
                    className="px-4 py-2 bg-stone-100 hover:bg-stone-200 text-stone-700 font-semibold rounded-xl text-xs transition"
                  >
                    Close Manifest
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confirmation & Execution Modal for Status Transitions */}
      {statusActionOrder && targetStatus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-charcoal-900 mb-1">
              Advance Ticket Status: {targetStatus}
            </h3>
            <p className="text-xs text-stone-500 mb-4">
              Order {statusActionOrder.order_number} will advance from <strong>{statusActionOrder.order_status}</strong> to <strong>{targetStatus}</strong>.
            </p>

            {targetStatus === "PREPARING" && (
              <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 mb-4">
                <div className="flex items-center space-x-1.5 font-bold mb-1">
                  <Flame className="w-4 h-4 text-terracotta-600" />
                  <span>Automatic Inventory Deduction Trigger</span>
                </div>
                Moving to PREPARING calculates the exact Bill of Materials for each dish and deducts required raw ingredients atomically from MySQL inventory with row-level locks.
              </div>
            )}

            {actionError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium mb-4">
                {actionError}
              </div>
            )}

            <div className="mb-5">
              <label className="block text-xs font-semibold text-stone-700 mb-1">
                Audit Note / Reason
              </label>
              <input
                type="text"
                placeholder="e.g. Fired appetizers to station 1, stock verified"
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                disabled={actionLoading}
                onClick={() => setStatusActionOrder(null)}
                className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-xs transition"
              >
                Abort
              </button>
              <button
                disabled={actionLoading}
                onClick={executeStatusTransition}
                className="px-5 py-2 rounded-xl bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold text-xs transition shadow-sm flex items-center space-x-1.5"
              >
                {actionLoading && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                <span>Confirm Transition</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </KitchenLayout>
  );
};
