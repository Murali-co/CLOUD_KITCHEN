import React, { useState, useEffect } from "react";
import { 
  UserCheck, 
  Search, 
  Filter, 
  Plus, 
  Building2, 
  Clock, 
  Briefcase, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Edit3, 
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Shield,
  Phone,
  Mail
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

const STAFF_ROLES = [
  { value: "KITCHEN_MANAGER", label: "Kitchen Manager" },
  { value: "HEAD_CHEF", label: "Head Chef" },
  { value: "LINE_COOK", label: "Line Cook" },
  { value: "INVENTORY_MANAGER", label: "Inventory Manager" },
  { value: "DISPATCHER", label: "Dispatcher" },
  { value: "PACKER", label: "Packer" },
];

const SHIFT_TIMINGS = [
  { value: "MORNING", label: "Morning (06:00 - 14:00)" },
  { value: "EVENING", label: "Evening (14:00 - 22:00)" },
  { value: "NIGHT", label: "Night (22:00 - 06:00)" },
  { value: "FULL_DAY", label: "Full Day" },
];

export const AdminStaffPage = () => {
  const [staffList, setStaffList] = useState([]);
  const [kitchens, setKitchens] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const [kitchenFilter, setKitchenFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Create Staff Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    password: "",
    kitchen_id: "",
    role: "LINE_COOK",
    shift_timing: "MORNING",
  });

  // Reassign Modal
  const [selectedStaff, setSelectedStaff] = useState(null);
  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [reassignData, setReassignData] = useState({
    kitchen_id: "",
    role: "",
    shift_timing: "",
    is_active: true,
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      // Fetch kitchens for dropdowns
      const kitchenResp = await adminApi.getKitchens({ page_size: 100 });
      if (kitchenResp.data.success) {
        setKitchens(kitchenResp.data.data.items || []);
      }

      // Fetch staff
      const params = { page, page_size: pageSize };
      if (kitchenFilter) params.kitchen_id = parseInt(kitchenFilter, 10);
      if (roleFilter) params.role = roleFilter;

      const staffResp = await adminApi.getStaff(params);
      if (staffResp.data.success) {
        setStaffList(staffResp.data.data.items || []);
        setTotal(staffResp.data.data.meta?.total_count || 0);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load kitchen staff roster.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, kitchenFilter, roleFilter]);

  const handleCreateStaff = async (e) => {
    e.preventDefault();
    if (!formData.first_name || !formData.email || !formData.password || !formData.kitchen_id) {
      setErrorMsg("Please fill in all mandatory fields.");
      return;
    }
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const payload = {
        first_name: formData.first_name,
        last_name: formData.last_name || undefined,
        email: formData.email,
        phone_number: formData.phone_number || undefined,
        password: formData.password,
        kitchen_id: parseInt(formData.kitchen_id, 10),
        role: formData.role,
        shift_timing: formData.shift_timing,
      };
      const resp = await adminApi.createStaff(payload);
      if (resp.data.success) {
        setSuccessMsg(`Staff account for ${resp.data.data.full_name} created successfully.`);
        setCreateModalOpen(false);
        setFormData({
          first_name: "",
          last_name: "",
          email: "",
          phone_number: "",
          password: "",
          kitchen_id: "",
          role: "LINE_COOK",
          shift_timing: "MORNING",
        });
        await fetchData();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to create staff account.");
    } finally {
      setActionLoading(false);
    }
  };

  const openReassignModal = (staff) => {
    setSelectedStaff(staff);
    setReassignData({
      kitchen_id: staff.kitchen_id || "",
      role: staff.role || "LINE_COOK",
      shift_timing: staff.shift_timing || "MORNING",
      is_active: staff.is_active,
    });
    setReassignModalOpen(true);
  };

  const handleReassignStaff = async (e) => {
    e.preventDefault();
    if (!selectedStaff) return;
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const payload = {};
      if (reassignData.kitchen_id) payload.kitchen_id = parseInt(reassignData.kitchen_id, 10);
      if (reassignData.role) payload.role = reassignData.role;
      if (reassignData.shift_timing) payload.shift_timing = reassignData.shift_timing;
      if (reassignData.is_active !== undefined) payload.is_active = reassignData.is_active;

      const resp = await adminApi.reassignStaff(selectedStaff.staff_id, payload);
      if (resp.data.success) {
        setSuccessMsg(`Updated assignment for ${selectedStaff.full_name}.`);
        setReassignModalOpen(false);
        await fetchData();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to update staff assignment.");
    } finally {
      setActionLoading(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <AdminLayout
      title="Kitchen Staff Roster"
      subtitle="Manage kitchen managers, head chefs, line cooks, and operational facility personnel"
      actions={
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              if (kitchens.length > 0 && !formData.kitchen_id) {
                setFormData((prev) => ({ ...prev, kitchen_id: kitchens[0].kitchen_id }));
              }
              setCreateModalOpen(true);
            }}
            className="flex items-center space-x-2 px-3 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add Staff Account</span>
          </button>
          <button
            onClick={fetchData}
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
      <div className="bg-white p-4 rounded-2xl border border-stone-200 shadow-xs flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-2 text-xs font-bold text-stone-600">
          <Filter className="w-4 h-4 text-purple-600" />
          <span>Filters:</span>
        </div>

        {/* Kitchen Filter */}
        <select
          value={kitchenFilter}
          onChange={(e) => {
            setKitchenFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Kitchen Facilities</option>
          {kitchens.map((k) => (
            <option key={k.kitchen_id} value={k.kitchen_id}>
              {k.name} ({k.branch_code})
            </option>
          ))}
        </select>

        {/* Role Filter */}
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Staff Roles</option>
          {STAFF_ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>

        {(kitchenFilter || roleFilter) && (
          <button
            onClick={() => {
              setKitchenFilter("");
              setRoleFilter("");
              setPage(1);
            }}
            className="text-xs text-purple-600 font-bold hover:underline"
          >
            Clear Filters
          </button>
        )}

        <div className="ml-auto text-xs text-stone-500 font-medium">
          Total Staff: <strong className="text-charcoal-900">{total}</strong>
        </div>
      </div>

      {/* Staff Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-stone-50 border-b border-stone-200 text-stone-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Staff Member</th>
                <th className="py-3 px-4">Contact</th>
                <th className="py-3 px-4">Assigned Facility</th>
                <th className="py-3 px-4">Role & Duties</th>
                <th className="py-3 px-4">Shift</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-stone-400 font-medium">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-600" />
                    Loading kitchen roster...
                  </td>
                </tr>
              ) : staffList.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-stone-400 font-medium">
                    <UserCheck className="w-8 h-8 mx-auto mb-2 text-stone-300" />
                    No staff members match the selected criteria.
                  </td>
                </tr>
              ) : (
                staffList.map((staff) => (
                  <tr key={staff.staff_id} className="hover:bg-stone-50/60 transition">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs shrink-0">
                          {staff.full_name?.[0] || "S"}
                        </div>
                        <div>
                          <p className="font-bold text-charcoal-900">{staff.full_name}</p>
                          <span className="text-[10px] text-stone-400 font-mono">ID #{staff.staff_id}</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 space-y-0.5">
                      <div className="flex items-center space-x-1.5 text-stone-600">
                        <Mail className="w-3.5 h-3.5 text-stone-400" />
                        <span>{staff.email}</span>
                      </div>
                      {staff.phone_number && (
                        <div className="flex items-center space-x-1.5 text-stone-500">
                          <Phone className="w-3.5 h-3.5 text-stone-400" />
                          <span>{staff.phone_number}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1.5 font-bold text-charcoal-800">
                        <Building2 className="w-3.5 h-3.5 text-stone-400" />
                        <span>{staff.kitchen_name}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                        {staff.role.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1 text-stone-600 font-medium">
                        <Clock className="w-3.5 h-3.5 text-stone-400" />
                        <span>{staff.shift_timing || "Standard"}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      {staff.is_active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-500 border border-stone-200">
                          <XCircle className="w-3 h-3 mr-1" />
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => openReassignModal(staff)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-stone-300 hover:bg-purple-50 hover:text-purple-700 text-stone-600 font-bold transition text-[11px]"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Reassign</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
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

      {/* CREATE STAFF MODAL */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-stone-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-stone-100">
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-purple-100 text-purple-700 rounded-xl">
                  <UserCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-charcoal-900">Provision Staff Account</h3>
                  <p className="text-xs text-stone-500">Create staff credentials with assigned cloud kitchen facility</p>
                </div>
              </div>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-stone-400 hover:text-stone-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateStaff} className="mt-4 space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-stone-700 mb-1">First Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g. Rahul"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-stone-700 mb-1">Last Name</label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g. Sharma"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-stone-700 mb-1">Email Address *</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                    placeholder="staff@kitchen.com"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-stone-700 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                    placeholder="+91 9876543210"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Temporary Initial Password *</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                  placeholder="Min 6 characters (hashed securely)"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Assign Kitchen Facility *</label>
                <select
                  required
                  value={formData.kitchen_id}
                  onChange={(e) => setFormData({ ...formData, kitchen_id: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
                >
                  <option value="">Select Cloud Kitchen Facility</option>
                  {kitchens.map((k) => (
                    <option key={k.kitchen_id} value={k.kitchen_id}>
                      {k.name} ({k.city}) — {k.branch_code}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-stone-700 mb-1">Operational Role</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
                  >
                    {STAFF_ROLES.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-stone-700 mb-1">Shift Timing</label>
                  <select
                    value={formData.shift_timing}
                    onChange={(e) => setFormData({ ...formData, shift_timing: e.target.value })}
                    className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
                  >
                    {SHIFT_TIMINGS.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-4 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-4 py-2 border border-stone-200 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 disabled:opacity-50"
                >
                  {actionLoading ? "Provisioning..." : "Provision Staff Account"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* REASSIGN STAFF MODAL */}
      {reassignModalOpen && selectedStaff && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-stone-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <h3 className="text-sm font-bold text-charcoal-900">
                Reassign: {selectedStaff.full_name}
              </h3>
              <button
                onClick={() => setReassignModalOpen(false)}
                className="text-stone-400 hover:text-stone-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReassignStaff} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Cloud Kitchen Facility</label>
                <select
                  value={reassignData.kitchen_id}
                  onChange={(e) => setReassignData({ ...reassignData, kitchen_id: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
                >
                  {kitchens.map((k) => (
                    <option key={k.kitchen_id} value={k.kitchen_id}>
                      {k.name} ({k.branch_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Staff Role</label>
                <select
                  value={reassignData.role}
                  onChange={(e) => setReassignData({ ...reassignData, role: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
                >
                  {STAFF_ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Shift Timing</label>
                <select
                  value={reassignData.shift_timing}
                  onChange={(e) => setReassignData({ ...reassignData, shift_timing: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
                >
                  {SHIFT_TIMINGS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="staffActiveToggle"
                  checked={reassignData.is_active}
                  onChange={(e) => setReassignData({ ...reassignData, is_active: e.target.checked })}
                  className="rounded text-purple-600 focus:ring-purple-500"
                />
                <label htmlFor="staffActiveToggle" className="text-xs font-bold text-stone-700">
                  Staff Account Active
                </label>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-4 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setReassignModalOpen(false)}
                  className="px-4 py-2 border border-stone-200 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 disabled:opacity-50"
                >
                  {actionLoading ? "Saving..." : "Save Assignment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};
