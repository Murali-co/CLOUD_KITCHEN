import React, { useState, useEffect } from "react";
import { 
  Building2, 
  Plus, 
  MapPin, 
  Phone, 
  Mail, 
  Clock, 
  Users, 
  UtensilsCrossed, 
  Edit3, 
  Power, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw,
  Search,
  ExternalLink
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

export const AdminKitchensPage = () => {
  const [kitchens, setKitchens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editKitchen, setEditKitchen] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    street_address: "",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "",
    phone: "",
    email: "",
    max_orders_per_hour: 50,
  });

  const fetchKitchens = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const resp = await adminApi.getKitchens();
      if (resp.data.success) {
        setKitchens(resp.data.data.items || []);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load kitchen facilities");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKitchens();
  }, []);

  const handleOpenCreate = () => {
    setEditKitchen(null);
    setFormData({
      name: "",
      street_address: "",
      city: "Bengaluru",
      state: "Karnataka",
      postal_code: "",
      phone: "+91",
      email: "",
      max_orders_per_hour: 50,
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (k) => {
    setEditKitchen(k);
    setFormData({
      name: k.name,
      street_address: k.street_address,
      city: k.city,
      state: k.state,
      postal_code: k.postal_code,
      phone: k.phone,
      email: k.email,
      max_orders_per_hour: k.max_orders_per_hour,
    });
    setModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      if (editKitchen) {
        const resp = await adminApi.updateKitchen(editKitchen.kitchen_id, formData);
        if (resp.data.success) {
          setSuccessMsg(`Kitchen facility '${formData.name}' updated successfully.`);
        }
      } else {
        const resp = await adminApi.createKitchen(formData);
        if (resp.data.success) {
          setSuccessMsg(`New kitchen hub '${formData.name}' provisioned successfully.`);
        }
      }
      setModalOpen(false);
      await fetchKitchens();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to save kitchen record.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleOperatingStatus = async (k, newStatus) => {
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const resp = await adminApi.updateKitchenStatus(k.kitchen_id, {
        operating_status: newStatus,
        reason: "Administrative toggle",
      });
      if (resp.data.success) {
        setSuccessMsg(`Kitchen status set to ${newStatus}`);
        await fetchKitchens();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to update kitchen status.");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <AdminLayout
      title="Cloud Kitchen Facilities"
      subtitle="Branch provisioning, capacity controls, and operational readiness"
      actions={
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>Provision New Hub</span>
        </button>
      }
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

        {/* Kitchen Cards Grid */}
        {loading ? (
          <div className="py-20 text-center text-stone-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-purple-600" />
            <span className="text-xs">Loading kitchen network...</span>
          </div>
        ) : kitchens.length === 0 ? (
          <div className="bg-white rounded-2xl p-10 text-center border border-dashed border-stone-300">
            <Building2 className="w-8 h-8 mx-auto text-stone-400 mb-2" />
            <h3 className="text-sm font-bold text-charcoal-900">No Kitchens Provisioned</h3>
            <p className="text-xs text-stone-500 mt-1">Click "Provision New Hub" to create your first cloud kitchen.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {kitchens.map((k) => {
              const isActive = k.operating_status === "ACTIVE";
              const isMaintenance = k.operating_status === "MAINTENANCE";

              return (
                <div
                  key={k.kitchen_id}
                  className="bg-white rounded-2xl border border-stone-200/90 shadow-sm p-5 space-y-4 flex flex-col justify-between hover:shadow-md transition"
                >
                  <div className="space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-black text-charcoal-900 text-base">{k.name}</h3>
                        <span className="text-[11px] font-mono text-stone-400">
                          ID #{k.kitchen_id} • {k.city}
                        </span>
                      </div>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                          isActive
                            ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                            : isMaintenance
                            ? "bg-amber-100 text-amber-800 border border-amber-200"
                            : "bg-red-100 text-red-800 border border-red-200"
                        }`}
                      >
                        {k.operating_status}
                      </span>
                    </div>

                    {/* Address & Contact */}
                    <div className="space-y-1 text-xs text-stone-600">
                      <p className="flex items-center space-x-1.5">
                        <MapPin className="w-3.5 h-3.5 text-stone-400 shrink-0" />
                        <span className="truncate">{k.street_address}, {k.postal_code}</span>
                      </p>
                      <p className="flex items-center space-x-1.5">
                        <Phone className="w-3.5 h-3.5 text-stone-400 shrink-0" />
                        <span>{k.phone}</span>
                      </p>
                      <p className="flex items-center space-x-1.5">
                        <Mail className="w-3.5 h-3.5 text-stone-400 shrink-0" />
                        <span className="truncate">{k.email}</span>
                      </p>
                    </div>

                    {/* Statistics */}
                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-stone-100 text-center">
                      <div className="bg-stone-50 p-2 rounded-xl">
                        <span className="text-[10px] text-stone-400 uppercase font-semibold block">Staff</span>
                        <span className="text-xs font-bold text-charcoal-900">{k.active_staff_count}</span>
                      </div>
                      <div className="bg-stone-50 p-2 rounded-xl">
                        <span className="text-[10px] text-stone-400 uppercase font-semibold block">Dishes</span>
                        <span className="text-xs font-bold text-charcoal-900">{k.menu_items_count}</span>
                      </div>
                      <div className="bg-stone-50 p-2 rounded-xl">
                        <span className="text-[10px] text-stone-400 uppercase font-semibold block">Max Cap/hr</span>
                        <span className="text-xs font-bold text-charcoal-900">{k.max_orders_per_hour}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-stone-100 flex items-center justify-between">
                    <button
                      onClick={() => handleOpenEdit(k)}
                      className="inline-flex items-center space-x-1 text-xs font-bold text-stone-600 hover:text-purple-600"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Edit Details</span>
                    </button>

                    <div className="flex space-x-1">
                      {isActive ? (
                        <button
                          onClick={() => handleToggleOperatingStatus(k, "INACTIVE")}
                          disabled={actionLoading}
                          className="px-2.5 py-1 text-[11px] font-bold text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition"
                        >
                          Deactivate
                        </button>
                      ) : (
                        <button
                          onClick={() => handleToggleOperatingStatus(k, "ACTIVE")}
                          disabled={actionLoading}
                          className="px-2.5 py-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition"
                        >
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => handleToggleOperatingStatus(k, isMaintenance ? "ACTIVE" : "MAINTENANCE")}
                        disabled={actionLoading}
                        className="px-2 py-1 text-[11px] font-bold text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-lg transition"
                      >
                        {isMaintenance ? "Resume" : "Maint."}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Provision / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl animate-in zoom-in-95 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-black text-charcoal-900">
              {editKitchen ? `Edit Facility: ${editKitchen.name}` : "Provision New Cloud Kitchen"}
            </h3>

            <form onSubmit={handleFormSubmit} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-stone-700 block mb-1">Kitchen Hub Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Indiranagar Gourmet Central"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
                />
              </div>

              <div>
                <label className="font-bold text-stone-700 block mb-1">Street Address</label>
                <input
                  type="text"
                  required
                  placeholder="100 Feet Rd, HAL 2nd Stage"
                  value={formData.street_address}
                  onChange={(e) => setFormData({ ...formData, street_address: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-stone-700 block mb-1">City</label>
                  <input
                    type="text"
                    required
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
                  />
                </div>
                <div>
                  <label className="font-bold text-stone-700 block mb-1">Postal Code</label>
                  <input
                    type="text"
                    required
                    placeholder="560038"
                    value={formData.postal_code}
                    onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-stone-700 block mb-1">Contact Phone</label>
                  <input
                    type="tel"
                    required
                    placeholder="+918012345678"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
                  />
                </div>
                <div>
                  <label className="font-bold text-stone-700 block mb-1">Facility Email</label>
                  <input
                    type="email"
                    required
                    placeholder="hub@gourmetcloud.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-stone-700 block mb-1">Max Orders Processing Capacity (per hour)</label>
                <input
                  type="number"
                  min="5"
                  max="500"
                  value={formData.max_orders_per_hour}
                  onChange={(e) => setFormData({ ...formData, max_orders_per_hour: parseInt(e.target.value) || 50 })}
                  className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3 py-2 focus:outline-none focus:border-purple-600"
                />
              </div>

              <div className="flex space-x-2 pt-3 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="flex-1 py-2 text-xs font-bold text-stone-600 bg-stone-100 hover:bg-stone-200 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="flex-1 py-2 text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-xl shadow-sm"
                >
                  {actionLoading ? "Saving..." : editKitchen ? "Update Facility" : "Provision Kitchen"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};
