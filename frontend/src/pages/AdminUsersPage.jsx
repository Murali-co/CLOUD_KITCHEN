import React, { useState, useEffect } from "react";
import { 
  Users, 
  Search, 
  Filter, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Edit3, 
  RefreshCw,
  Power,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

export const AdminUsersPage = () => {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Role Edit Modal
  const [selectedUser, setSelectedUser] = useState(null);
  const [newRole, setNewRole] = useState("");
  const [roleModalOpen, setRoleModalOpen] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      if (activeFilter !== "") params.is_active = activeFilter === "true";

      const resp = await adminApi.getUsers(params);
      if (resp.data.success) {
        setUsers(resp.data.data.items || []);
        setTotal(resp.data.data.meta?.total_count || 0);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load user accounts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, roleFilter, activeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleToggleStatus = async (user) => {
    if (!window.confirm(`Are you sure you want to ${user.is_active ? "deactivate" : "activate"} ${user.email}?`)) {
      return;
    }
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const resp = await adminApi.updateUserStatus(user.user_id, {
        is_active: !user.is_active,
        reason: `Admin toggle by user request`,
      });
      if (resp.data.success) {
        setSuccessMsg(`User ${user.email} is now ${!user.is_active ? "Active" : "Deactivated"}`);
        await fetchUsers();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to update user status.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRole = async () => {
    if (!selectedUser || !newRole) return;
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const resp = await adminApi.updateUserRole(selectedUser.user_id, {
        role: newRole,
      });
      if (resp.data.success) {
        setSuccessMsg(`Role updated to ${newRole} for ${selectedUser.email}`);
        setRoleModalOpen(false);
        await fetchUsers();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Role modification rejected.");
    } finally {
      setActionLoading(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  const roleColors = {
    ADMIN: "bg-purple-100 text-purple-800 border-purple-200",
    KITCHEN_MANAGER: "bg-terracotta-100 text-terracotta-800 border-terracotta-200",
    KITCHEN_STAFF: "bg-amber-100 text-amber-800 border-amber-200",
    DELIVERY_PERSON: "bg-blue-100 text-blue-800 border-blue-200",
    CUSTOMER: "bg-stone-100 text-stone-800 border-stone-200",
  };

  return (
    <AdminLayout
      title="User Management"
      subtitle="Role-based access control, security administration, and audit"
    >
      <div className="space-y-4">
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

        {/* Filter Controls */}
        <div className="bg-white rounded-2xl p-4 border border-stone-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
          <form onSubmit={handleSearchSubmit} className="flex-1 w-full md:w-auto flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-stone-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search by name, email, or phone number..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-stone-50 border border-stone-200 rounded-xl focus:outline-none focus:border-purple-500"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold transition"
            >
              Search
            </button>
          </form>

          <div className="flex items-center space-x-2 w-full md:w-auto">
            <select
              value={roleFilter}
              onChange={(e) => {
                setRoleFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs bg-stone-50 border border-stone-200 rounded-xl px-3 py-1.5 focus:outline-none"
            >
              <option value="">All Roles</option>
              <option value="CUSTOMER">Customer</option>
              <option value="DELIVERY_PERSON">Delivery Person</option>
              <option value="KITCHEN_STAFF">Kitchen Staff</option>
              <option value="KITCHEN_MANAGER">Kitchen Manager</option>
              <option value="ADMIN">Administrator</option>
            </select>

            <select
              value={activeFilter}
              onChange={(e) => {
                setActiveFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs bg-stone-50 border border-stone-200 rounded-xl px-3 py-1.5 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="true">Active Only</option>
              <option value="false">Deactivated Only</option>
            </select>

            <button
              onClick={fetchUsers}
              className="p-2 text-stone-500 hover:text-stone-800 rounded-xl hover:bg-stone-100"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-stone-600">
              <thead className="bg-stone-50 text-[11px] font-bold text-stone-500 uppercase tracking-wider border-b border-stone-200">
                <tr>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Contact</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Affiliation / Detail</th>
                  <th className="py-3 px-4">Account Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-stone-400">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-purple-600" />
                      Loading user accounts...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-10 text-center text-stone-400">
                      No user accounts found matching your query.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.user_id} className="hover:bg-stone-50/70 transition">
                      <td className="py-3 px-4 font-semibold text-charcoal-900">
                        <div className="flex items-center space-x-2">
                          <div className="w-7 h-7 rounded-full bg-stone-100 text-stone-700 flex items-center justify-center font-bold text-xs uppercase">
                            {u.first_name?.[0] || "U"}
                          </div>
                          <div>
                            <span className="block font-bold">
                              {u.first_name} {u.last_name}
                            </span>
                            <span className="text-[10px] text-stone-400">ID #{u.user_id}</span>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="block text-stone-800 font-medium">{u.email}</span>
                        <span className="text-[11px] text-stone-400">{u.phone || "No phone registered"}</span>
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider border ${
                            roleColors[u.role] || "bg-stone-100 text-stone-700"
                          }`}
                        >
                          {u.role.replace(/_/g, " ")}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-[11px]">
                        {u.kitchen_name ? (
                          <span className="text-terracotta-700 font-semibold">Kitchen: {u.kitchen_name}</span>
                        ) : u.vehicle_number ? (
                          <span className="text-blue-700 font-semibold">Vehicle: {u.vehicle_number}</span>
                        ) : (
                          <span className="text-stone-400">—</span>
                        )}
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            u.is_active
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-red-50 text-red-700"
                          }`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? "bg-emerald-500" : "bg-red-500"}`}></span>
                          <span>{u.is_active ? "Active" : "Deactivated"}</span>
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right space-x-1">
                        {/* Change Role Button */}
                        <button
                          onClick={() => {
                            setSelectedUser(u);
                            setNewRole(u.role);
                            setRoleModalOpen(true);
                          }}
                          className="px-2.5 py-1 text-[11px] font-bold text-stone-600 hover:text-purple-700 bg-stone-100 hover:bg-purple-50 rounded-lg transition"
                          title="Change Role"
                        >
                          Role
                        </button>

                        {/* Toggle Status Button */}
                        <button
                          onClick={() => handleToggleStatus(u)}
                          disabled={actionLoading}
                          className={`px-2.5 py-1 text-[11px] font-bold rounded-lg transition ${
                            u.is_active
                              ? "text-red-700 bg-red-50 hover:bg-red-100"
                              : "text-emerald-700 bg-emerald-50 hover:bg-emerald-100"
                          }`}
                        >
                          {u.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 bg-stone-50 border-t border-stone-200 flex items-center justify-between text-xs text-stone-500">
            <span>
              Showing page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total} total users)
            </span>
            <div className="flex space-x-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-stone-200 hover:bg-white disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-stone-200 hover:bg-white disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Role Change Modal */}
      {roleModalOpen && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-5 space-y-4 shadow-2xl animate-in zoom-in-95">
            <h3 className="text-base font-bold text-charcoal-900">
              Modify Account Role
            </h3>
            <p className="text-xs text-stone-500">
              Change administrative permissions for <strong>{selectedUser.email}</strong>.
            </p>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-stone-700">Assign New Role</label>
              <select
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
                className="w-full text-xs bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
              >
                <option value="CUSTOMER">CUSTOMER</option>
                <option value="DELIVERY_PERSON">DELIVERY_PERSON</option>
                <option value="KITCHEN_STAFF">KITCHEN_STAFF</option>
                <option value="KITCHEN_MANAGER">KITCHEN_MANAGER</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </div>

            <div className="p-3 rounded-xl bg-purple-50 text-[11px] text-purple-900 border border-purple-200">
              * The platform actively protects the last active administrator from demotion or accidental removal.
            </div>

            <div className="flex space-x-2 pt-2">
              <button
                onClick={() => setRoleModalOpen(false)}
                className="flex-1 py-2 text-xs font-bold text-stone-600 bg-stone-100 hover:bg-stone-200 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateRole}
                disabled={actionLoading}
                className="flex-1 py-2 text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-xl shadow-sm"
              >
                Confirm Change
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};
