import React, { useState, useEffect } from "react";
import { 
  Tag, 
  Plus, 
  Calendar, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Edit3, 
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Percent,
  DollarSign,
  Clock,
  Users
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

export const AdminCouponsPage = () => {
  const [coupons, setCoupons] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const [activeOnly, setActiveOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState(null);
  const [formData, setFormData] = useState({
    code: "",
    description: "",
    discount_type: "PERCENTAGE",
    discount_value: "",
    min_order_value: 0,
    max_discount_amount: "",
    valid_from: "",
    valid_to: "",
    usage_limit_per_user: 1,
    total_usage_limit: 100,
    is_active: true,
  });

  const fetchCoupons = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const params = { page, page_size: pageSize, active_only: activeOnly };
      const resp = await adminApi.getCoupons(params);
      if (resp.data.success) {
        setCoupons(resp.data.data.items || []);
        setTotal(resp.data.data.meta?.total_count || 0);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load coupon configurations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoupons();
  }, [page, activeOnly]);

  const openCreateModal = () => {
    setEditingCoupon(null);
    const now = new Date();
    const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
    setFormData({
      code: "",
      description: "",
      discount_type: "PERCENTAGE",
      discount_value: "",
      min_order_value: 0,
      max_discount_amount: "",
      valid_from: now.toISOString().slice(0, 16),
      valid_to: nextMonth.toISOString().slice(0, 16),
      usage_limit_per_user: 1,
      total_usage_limit: 100,
      is_active: true,
    });
    setModalOpen(true);
  };

  const openEditModal = (coupon) => {
    setEditingCoupon(coupon);
    setFormData({
      code: coupon.code,
      description: coupon.description || "",
      discount_type: coupon.discount_type,
      discount_value: coupon.discount_value,
      min_order_value: coupon.min_order_value || 0,
      max_discount_amount: coupon.max_discount_amount || "",
      valid_from: coupon.valid_from ? coupon.valid_from.slice(0, 16) : "",
      valid_to: coupon.valid_to ? coupon.valid_to.slice(0, 16) : "",
      usage_limit_per_user: coupon.usage_limit_per_user || 1,
      total_usage_limit: coupon.total_usage_limit || 100,
      is_active: coupon.is_active,
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.code.trim() || !formData.discount_value) {
      setErrorMsg("Please provide a coupon code and discount value.");
      return;
    }
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const payload = {
        code: formData.code.toUpperCase().trim(),
        description: formData.description || undefined,
        discount_type: formData.discount_type,
        discount_value: parseFloat(formData.discount_value),
        min_order_value: parseFloat(formData.min_order_value) || 0,
        max_discount_amount: formData.max_discount_amount ? parseFloat(formData.max_discount_amount) : undefined,
        valid_from: formData.valid_from ? new Date(formData.valid_from).toISOString() : new Date().toISOString(),
        valid_to: formData.valid_to ? new Date(formData.valid_to).toISOString() : new Date(Date.now() + 30 * 86400000).toISOString(),
        usage_limit_per_user: parseInt(formData.usage_limit_per_user, 10) || 1,
        total_usage_limit: parseInt(formData.total_usage_limit, 10) || 1000,
        is_active: formData.is_active,
      };

      if (editingCoupon) {
        const resp = await adminApi.updateCoupon(editingCoupon.coupon_id, payload);
        if (resp.data.success) {
          setSuccessMsg(`Coupon "${resp.data.data.code}" updated successfully.`);
        }
      } else {
        const resp = await adminApi.createCoupon(payload);
        if (resp.data.success) {
          setSuccessMsg(`Coupon "${resp.data.data.code}" created successfully.`);
        }
      }
      setModalOpen(false);
      await fetchCoupons();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to save coupon.");
    } finally {
      setActionLoading(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <AdminLayout
      title="Coupons & Discounts"
      subtitle="Configure promotion vouchers, percentage/flat discounts, minimum thresholds, and redemption caps"
      actions={
        <div className="flex items-center space-x-2">
          <button
            onClick={openCreateModal}
            className="flex items-center space-x-2 px-3 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create Coupon</span>
          </button>
          <button
            onClick={fetchCoupons}
            disabled={loading}
            className="p-2 border border-stone-300 rounded-xl bg-white hover:bg-stone-50 text-stone-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-purple-600" : ""}`} />
          </button>
        </div>
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
      <div className="bg-white p-4 rounded-2xl border border-stone-200 shadow-xs flex items-center justify-between">
        <label className="flex items-center space-x-2 text-xs font-bold text-stone-700 cursor-pointer">
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(e) => {
              setActiveOnly(e.target.checked);
              setPage(1);
            }}
            className="rounded text-purple-600 focus:ring-purple-500"
          />
          <span>Show Active Promotions Only</span>
        </label>
        <span className="text-xs text-stone-500 font-medium">
          Total Coupons: <strong className="text-charcoal-900">{total}</strong>
        </span>
      </div>

      {/* Coupons Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-stone-50 border-b border-stone-200 text-stone-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Coupon Code</th>
                <th className="py-3 px-4">Discount</th>
                <th className="py-3 px-4">Min Order</th>
                <th className="py-3 px-4">Max Cap</th>
                <th className="py-3 px-4">Validity Window</th>
                <th className="py-3 px-4">Redemptions</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-stone-400 font-medium">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-600" />
                    Loading coupons...
                  </td>
                </tr>
              ) : coupons.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-stone-400 font-medium">
                    <Tag className="w-8 h-8 mx-auto mb-2 text-stone-300" />
                    No promotional coupons found.
                  </td>
                </tr>
              ) : (
                coupons.map((c) => (
                  <tr key={c.coupon_id} className="hover:bg-stone-50/60 transition">
                    <td className="py-3.5 px-4 font-mono font-black text-charcoal-900 tracking-wider">
                      <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-lg border border-purple-200">
                        {c.code}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-charcoal-900">
                      {c.discount_type === "PERCENTAGE"
                        ? `${Number(c.discount_value)}% OFF`
                        : `₹${Number(c.discount_value).toFixed(2)} FLAT`}
                    </td>
                    <td className="py-3.5 px-4 text-stone-600">
                      ₹{Number(c.min_order_value || 0).toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4 text-stone-600">
                      {c.max_discount_amount ? `₹${Number(c.max_discount_amount).toFixed(2)}` : "No limit"}
                    </td>
                    <td className="py-3.5 px-4 text-stone-500 space-y-0.5">
                      <div>From: {c.valid_from ? new Date(c.valid_from).toLocaleDateString() : "Immediate"}</div>
                      <div>Until: {c.valid_to ? new Date(c.valid_to).toLocaleDateString() : "Ongoing"}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1 font-mono font-bold text-charcoal-800">
                        <span>{c.current_usage_count || 0}</span>
                        <span className="text-stone-400">/</span>
                        <span>{c.total_usage_limit ? c.total_usage_limit : "∞"}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      {c.is_active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-500 border border-stone-200">
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => openEditModal(c)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-stone-300 hover:bg-purple-50 hover:text-purple-700 text-stone-600 font-bold transition text-[11px]"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Edit</span>
                      </button>
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

      {/* CREATE / EDIT COUPON MODAL */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-stone-200 animate-in fade-in zoom-in-95 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <h3 className="text-sm font-bold text-charcoal-900">
                {editingCoupon ? `Edit Coupon: ${editingCoupon.code}` : "Create Promotional Coupon"}
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="text-stone-400 hover:text-stone-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-4 space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Coupon Code *</label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl font-mono uppercase font-bold focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g. WELCOME50"
                  />
                </div>
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Discount Type</label>
                  <select
                    value={formData.discount_type}
                    onChange={(e) => setFormData({ ...formData, discount_type: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500 bg-white"
                  >
                    <option value="PERCENTAGE">Percentage (%)</option>
                    <option value="FIXED_AMOUNT">Fixed Amount (₹)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-bold text-stone-700 mb-1">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g. 50% discount on first 3 orders"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Discount Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={formData.discount_value}
                    onChange={(e) => setFormData({ ...formData, discount_value: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g. 20 or 150"
                  />
                </div>
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Min Order Value (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.min_order_value}
                    onChange={(e) => setFormData({ ...formData, min_order_value: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Max Cap (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.max_discount_amount}
                    onChange={(e) => setFormData({ ...formData, max_discount_amount: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                    placeholder="Optional"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Valid From</label>
                  <input
                    type="datetime-local"
                    value={formData.valid_from}
                    onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Valid To</label>
                  <input
                    type="datetime-local"
                    value={formData.valid_to}
                    onChange={(e) => setFormData({ ...formData, valid_to: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Limit Per User</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.usage_limit_per_user}
                    onChange={(e) => setFormData({ ...formData, usage_limit_per_user: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Total Limit Cap</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.total_usage_limit}
                    onChange={(e) => setFormData({ ...formData, total_usage_limit: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="couponActiveToggle"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded text-purple-600 focus:ring-purple-500"
                />
                <label htmlFor="couponActiveToggle" className="font-bold text-stone-700">
                  Coupon Active & Eligible for Redemption
                </label>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-4 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 border border-stone-200 text-stone-600 rounded-xl font-bold hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 disabled:opacity-50"
                >
                  {actionLoading ? "Saving..." : editingCoupon ? "Update Coupon" : "Create Coupon"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};
