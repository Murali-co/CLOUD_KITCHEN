import React, { useState, useEffect } from "react";
import { 
  ShoppingBag, 
  Search, 
  Filter, 
  Building2, 
  Calendar, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Eye, 
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Truck,
  Ban,
  User,
  Phone,
  MapPin,
  Clock,
  CreditCard,
  DollarSign
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

const ORDER_STATUSES = [
  "ORDER_RECEIVED",
  "CONFIRMED",
  "PREPARING",
  "READY_FOR_PICKUP",
  "OUT_FOR_DELIVERY",
  "DELIVERED",
  "CANCELLED",
];

export const AdminOrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [kitchens, setKitchens] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [kitchenFilter, setKitchenFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Order Details Modal
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedOrderDetail, setSelectedOrderDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Cancellation Modal
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancellingOrderId, setCancellingOrderId] = useState(null);
  const [cancelReason, setCancelReason] = useState("");

  // Assign Courier Modal
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [assignOrderId, setAssignOrderId] = useState(null);
  const [availablePersonnel, setAvailablePersonnel] = useState([]);
  const [selectedPersonnelId, setSelectedPersonnelId] = useState("");
  const [loadingPersonnel, setLoadingPersonnel] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const kitchenResp = await adminApi.getKitchens({ page_size: 100 });
      if (kitchenResp.data.success) {
        setKitchens(kitchenResp.data.data.items || []);
      }

      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (kitchenFilter) params.kitchen_id = parseInt(kitchenFilter, 10);
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const orderResp = await adminApi.getOrders(params);
      if (orderResp.data.success) {
        setOrders(orderResp.data.data.items || []);
        setTotal(orderResp.data.data.meta?.total_count || 0);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load orders.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, statusFilter, kitchenFilter, startDate, endDate]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const handleViewDetail = async (orderId) => {
    setLoadingDetail(true);
    setDetailModalOpen(true);
    try {
      const resp = await adminApi.getOrderDetail(orderId);
      if (resp.data.success) {
        setSelectedOrderDetail(resp.data.data);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load order inspection.");
      setDetailModalOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const openCancelModal = (orderId) => {
    setCancellingOrderId(orderId);
    setCancelReason("Administrative cancellation");
    setCancelModalOpen(true);
  };

  const handleCancelOrder = async (e) => {
    e.preventDefault();
    if (!cancellingOrderId) return;
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const resp = await adminApi.cancelOrder(cancellingOrderId, cancelReason);
      if (resp.data.success) {
        setSuccessMsg(`Order #${resp.data.data.order_number} was successfully cancelled.`);
        setCancelModalOpen(false);
        if (selectedOrderDetail && selectedOrderDetail.order_id === cancellingOrderId) {
          setSelectedOrderDetail(resp.data.data);
        }
        await fetchData();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to cancel order.");
    } finally {
      setActionLoading(false);
    }
  };

  const openAssignModal = async (orderId) => {
    setAssignOrderId(orderId);
    setSelectedPersonnelId("");
    setLoadingPersonnel(true);
    setAssignModalOpen(true);
    try {
      const resp = await adminApi.getAvailablePersonnel();
      if (resp.data.success) {
        setAvailablePersonnel(resp.data.data || []);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to fetch available couriers.");
    } finally {
      setLoadingPersonnel(false);
    }
  };

  const handleAssignCourier = async (e) => {
    e.preventDefault();
    if (!assignOrderId || !selectedPersonnelId) return;
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const resp = await adminApi.assignDelivery(assignOrderId, {
        delivery_person_id: parseInt(selectedPersonnelId, 10),
      });
      if (resp.data.success) {
        setSuccessMsg(`Courier assigned to order successfully.`);
        setAssignModalOpen(false);
        if (selectedOrderDetail && selectedOrderDetail.order_id === assignOrderId) {
          const updated = await adminApi.getOrderDetail(assignOrderId);
          if (updated.data.success) setSelectedOrderDetail(updated.data.data);
        }
        await fetchData();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to assign delivery courier.");
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (st) => {
    const colors = {
      ORDER_RECEIVED: "bg-blue-50 text-blue-700 border-blue-200",
      CONFIRMED: "bg-indigo-50 text-indigo-700 border-indigo-200",
      PREPARING: "bg-amber-50 text-amber-800 border-amber-200",
      READY_FOR_PICKUP: "bg-purple-50 text-purple-700 border-purple-200",
      OUT_FOR_DELIVERY: "bg-orange-50 text-orange-700 border-orange-200",
      DELIVERED: "bg-emerald-50 text-emerald-700 border-emerald-200",
      CANCELLED: "bg-red-50 text-red-700 border-red-200",
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${colors[st] || "bg-stone-100 text-stone-700 border-stone-200"}`}>
        {st.replace(/_/g, " ")}
      </span>
    );
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <AdminLayout
      title="Order Administration"
      subtitle="Complete oversight of kitchen orders, timeline tracking, delivery assignments, and cancellations"
      actions={
        <button
          onClick={fetchData}
          disabled={loading}
          className="p-2 border border-stone-300 rounded-xl bg-white hover:bg-stone-50 text-stone-700"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-purple-600" : ""}`} />
        </button>
      }
    >
      {/* Notifications */}
      {errorMsg && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-stone-200 shadow-xs flex flex-wrap items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search order number or phone..."
            className="w-full pl-9 pr-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
          />
        </form>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Order Statuses</option>
          {ORDER_STATUSES.map((st) => (
            <option key={st} value={st}>
              {st.replace(/_/g, " ")}
            </option>
          ))}
        </select>

        <select
          value={kitchenFilter}
          onChange={(e) => {
            setKitchenFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Kitchens</option>
          {kitchens.map((k) => (
            <option key={k.kitchen_id} value={k.kitchen_id}>
              {k.name} ({k.branch_code})
            </option>
          ))}
        </select>

        <div className="flex items-center space-x-1.5 text-xs">
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
            className="px-2 py-1.5 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
            title="Start Date"
          />
          <span className="text-stone-400">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
            className="px-2 py-1.5 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
            title="End Date"
          />
        </div>

        {(search || statusFilter || kitchenFilter || startDate || endDate) && (
          <button
            onClick={() => {
              setSearch("");
              setStatusFilter("");
              setKitchenFilter("");
              setStartDate("");
              setEndDate("");
              setPage(1);
            }}
            className="text-xs text-purple-600 font-bold hover:underline"
          >
            Reset
          </button>
        )}

        <div className="ml-auto text-xs text-stone-500 font-medium">
          Total Orders: <strong className="text-charcoal-900">{total}</strong>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-stone-50 border-b border-stone-200 text-stone-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Order Ref</th>
                <th className="py-3 px-4">Placed At</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Cloud Kitchen</th>
                <th className="py-3 px-4">Total Amount</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Payment</th>
                <th className="py-3 px-4">Courier</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center py-10 text-stone-400 font-medium">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-600" />
                    Loading orders...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-stone-400 font-medium">
                    <ShoppingBag className="w-8 h-8 mx-auto mb-2 text-stone-300" />
                    No orders found matching the filter criteria.
                  </td>
                </tr>
              ) : (
                orders.map((o) => (
                  <tr key={o.order_id} className="hover:bg-stone-50/60 transition">
                    <td className="py-3.5 px-4 font-mono font-bold text-charcoal-900">
                      #{o.order_number}
                    </td>
                    <td className="py-3.5 px-4 text-stone-500">
                      {new Date(o.placed_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3.5 px-4">
                      <p className="font-bold text-charcoal-900">{o.customer_name}</p>
                      <span className="text-[10px] text-stone-400">{o.customer_phone || "—"}</span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-charcoal-800">
                      {o.kitchen_name}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-charcoal-900">
                      ₹{Number(o.total_amount).toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4">
                      {getStatusBadge(o.order_status)}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        o.payment_status === "SUCCESS"
                          ? "bg-emerald-50 text-emerald-700"
                          : o.payment_status === "PENDING"
                          ? "bg-amber-50 text-amber-700"
                          : "bg-stone-100 text-stone-500"
                      }`}>
                        {o.payment_status || "PENDING"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-stone-600">
                      {o.delivery_person_name ? (
                        <div className="flex items-center space-x-1 font-medium">
                          <Truck className="w-3.5 h-3.5 text-purple-600 shrink-0" />
                          <span className="truncate max-w-[100px]">{o.delivery_person_name}</span>
                        </div>
                      ) : (
                        <span className="text-stone-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1">
                      <button
                        onClick={() => handleViewDetail(o.order_id)}
                        className="inline-flex items-center p-1.5 rounded-lg border border-stone-200 hover:bg-stone-50 text-stone-600"
                        title="Inspect Order"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>

                      {/* Dispatch courier button if not delivered or cancelled */}
                      {o.order_status !== "DELIVERED" && o.order_status !== "CANCELLED" && !o.delivery_person_name && (
                        <button
                          onClick={() => openAssignModal(o.order_id)}
                          className="inline-flex items-center p-1.5 rounded-lg border border-purple-200 bg-purple-50 hover:bg-purple-100 text-purple-700"
                          title="Assign Delivery Courier"
                        >
                          <Truck className="w-3.5 h-3.5" />
                        </button>
                      )}

                      {/* Cancel order button if not already completed/cancelled */}
                      {o.order_status !== "DELIVERED" && o.order_status !== "CANCELLED" && (
                        <button
                          onClick={() => openCancelModal(o.order_id)}
                          className="inline-flex items-center p-1.5 rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 text-red-600"
                          title="Cancel Order"
                        >
                          <Ban className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 bg-stone-50 border-t border-stone-200 flex items-center justify-between text-xs">
            <span className="text-stone-500">
              Page <strong>{page}</strong> of <strong>{totalPages}</strong>
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-stone-200 bg-white hover:bg-stone-50 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-stone-200 bg-white hover:bg-stone-50 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* INSPECT ORDER MODAL */}
      {detailModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl border border-stone-200 animate-in fade-in zoom-in-95 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <div className="flex items-center space-x-2">
                <ShoppingBag className="w-5 h-5 text-purple-600" />
                <h3 className="text-sm font-bold text-charcoal-900">
                  {selectedOrderDetail ? `Order #${selectedOrderDetail.order_number}` : "Inspecting Order..."}
                </h3>
              </div>
              <button
                onClick={() => setDetailModalOpen(false)}
                className="text-stone-400 hover:text-stone-600"
              >
                ✕
              </button>
            </div>

            {loadingDetail || !selectedOrderDetail ? (
              <div className="py-12 text-center text-stone-400">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-purple-600" />
                Retrieving order inspection details...
              </div>
            ) : (
              <div className="mt-4 space-y-5 text-xs">
                {/* Status & Kitchen Header */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-stone-50 p-3.5 rounded-xl border border-stone-200">
                  <div>
                    <span className="text-[10px] text-stone-400 font-bold block uppercase">Status</span>
                    {getStatusBadge(selectedOrderDetail.order_status)}
                  </div>
                  <div>
                    <span className="text-[10px] text-stone-400 font-bold block uppercase">Kitchen Facility</span>
                    <strong className="text-charcoal-900">{selectedOrderDetail.kitchen_name}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-stone-400 font-bold block uppercase">Total Bill</span>
                    <strong className="text-charcoal-900 text-sm">₹{Number(selectedOrderDetail.total_amount).toFixed(2)}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-stone-400 font-bold block uppercase">Placed At</span>
                    <span className="text-stone-600 font-medium">
                      {new Date(selectedOrderDetail.placed_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </div>

                {/* Customer & Address */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200">
                    <span className="text-[10px] text-stone-400 font-bold uppercase block mb-1">Customer Profile</span>
                    <p className="font-bold text-charcoal-900">{selectedOrderDetail.customer?.full_name}</p>
                    <p className="text-stone-600">{selectedOrderDetail.customer?.email}</p>
                    <p className="text-stone-600">{selectedOrderDetail.customer?.phone_number || "No phone listed"}</p>
                  </div>
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200">
                    <span className="text-[10px] text-stone-400 font-bold uppercase block mb-1">Delivery Destination</span>
                    <p className="font-bold text-charcoal-900">{selectedOrderDetail.delivery_address?.address_line1}</p>
                    <p className="text-stone-600">
                      {selectedOrderDetail.delivery_address?.city}, {selectedOrderDetail.delivery_address?.postal_code}
                    </p>
                  </div>
                </div>

                {/* Items Breakdown */}
                <div>
                  <h4 className="font-bold text-charcoal-900 mb-2">Order Items Snapshot</h4>
                  <div className="border border-stone-200 rounded-xl overflow-hidden divide-y divide-stone-100">
                    {selectedOrderDetail.items?.map((item, idx) => (
                      <div key={idx} className="p-2.5 flex items-center justify-between">
                        <div>
                          <p className="font-bold text-charcoal-900">{item.item_name}</p>
                          <span className="text-[10px] text-stone-500 font-mono">
                            Qty: {item.quantity} × ₹{Number(item.unit_price).toFixed(2)}
                          </span>
                        </div>
                        <span className="font-bold text-charcoal-900">
                          ₹{Number(item.total_price).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Delivery Courier Info */}
                <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-stone-400 font-bold uppercase block mb-0.5">Assigned Courier</span>
                    {selectedOrderDetail.delivery_person ? (
                      <div>
                        <p className="font-bold text-charcoal-900">{selectedOrderDetail.delivery_person.full_name}</p>
                        <p className="text-stone-500">Phone: {selectedOrderDetail.delivery_person.phone_number}</p>
                      </div>
                    ) : (
                      <p className="text-stone-400 italic">No courier assigned</p>
                    )}
                  </div>
                  {selectedOrderDetail.order_status !== "DELIVERED" && selectedOrderDetail.order_status !== "CANCELLED" && (
                    <button
                      onClick={() => openAssignModal(selectedOrderDetail.order_id)}
                      className="px-3 py-1.5 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 shadow-sm"
                    >
                      {selectedOrderDetail.delivery_person ? "Reassign Courier" : "Assign Courier"}
                    </button>
                  )}
                </div>

                {/* Lifecycle Timeline */}
                <div>
                  <h4 className="font-bold text-charcoal-900 mb-2">Status Timeline</h4>
                  <div className="space-y-1.5 border-l-2 border-purple-200 pl-3 ml-2">
                    {selectedOrderDetail.history?.map((h, idx) => (
                      <div key={idx} className="relative">
                        <div className="absolute -left-[19px] top-1 w-2.5 h-2.5 rounded-full bg-purple-600" />
                        <span className="font-bold text-charcoal-900 mr-2">{h.status.replace(/_/g, " ")}</span>
                        <span className="text-stone-400 text-[10px]">{new Date(h.changed_at).toLocaleString()}</span>
                        {h.notes && <p className="text-stone-500 text-[11px] mt-0.5">{h.notes}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* CANCEL ORDER MODAL */}
      {cancelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-stone-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center space-x-2 text-red-600 pb-3 border-b border-stone-100">
              <Ban className="w-5 h-5" />
              <h3 className="text-sm font-bold text-charcoal-900">Administrative Order Cancellation</h3>
            </div>

            <form onSubmit={handleCancelOrder} className="mt-4 space-y-3.5">
              <p className="text-xs text-stone-600 leading-relaxed">
                Cancelling this order will mark it cancelled across kitchen dashboards, release reserved items, and record an administrative audit entry.
              </p>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Reason for Cancellation *</label>
                <textarea
                  rows={2}
                  required
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-red-500"
                  placeholder="e.g. Customer requested cancellation, operational incident, or address unreachable"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setCancelModalOpen(false)}
                  className="px-4 py-2 border border-stone-200 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-50"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-bold hover:bg-red-700 disabled:opacity-50"
                >
                  {actionLoading ? "Cancelling..." : "Confirm Cancellation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ASSIGN COURIER MODAL */}
      {assignModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-stone-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <div className="flex items-center space-x-2">
                <Truck className="w-5 h-5 text-purple-600" />
                <h3 className="text-sm font-bold text-charcoal-900">Assign Delivery Courier</h3>
              </div>
              <button
                onClick={() => setAssignModalOpen(false)}
                className="text-stone-400 hover:text-stone-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAssignCourier} className="mt-4 space-y-3.5">
              {loadingPersonnel ? (
                <div className="py-6 text-center text-stone-400 text-xs">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-600" />
                  Finding active and available personnel...
                </div>
              ) : availablePersonnel.length === 0 ? (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs">
                  No couriers are currently marked AVAILABLE and free of active tasks. Please wait for a courier to go on-duty or complete ongoing deliveries.
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-stone-700 mb-1">Select Available Courier *</label>
                  <select
                    required
                    value={selectedPersonnelId}
                    onChange={(e) => setSelectedPersonnelId(e.target.value)}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
                  >
                    <option value="">Choose Courier</option>
                    {availablePersonnel.map((p) => (
                      <option key={p.delivery_person_id} value={p.delivery_person_id}>
                        {p.full_name} ({p.vehicle_type}) — Phone: {p.phone_number}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setAssignModalOpen(false)}
                  className="px-4 py-2 border border-stone-200 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || !selectedPersonnelId || availablePersonnel.length === 0}
                  className="px-4 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 disabled:opacity-50"
                >
                  {actionLoading ? "Assigning..." : "Assign Courier"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};
