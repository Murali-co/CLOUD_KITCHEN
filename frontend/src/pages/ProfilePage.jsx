import React, { useState, useEffect } from "react";
import { User, Award, MapPin, Plus, Trash2, Heart, Check, Save } from "lucide-react";
import { customerApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

export const ProfilePage = () => {
  const { user, customer, setCustomer } = useAuth();
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);

  // Profile edit
  const [dietaryPref, setDietaryPref] = useState(customer?.dietary_preference || "ALL");
  const [savingPref, setSavingPref] = useState(false);
  const [prefSaved, setPrefSaved] = useState(false);

  // New Address
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAddr, setNewAddr] = useState({
    address_label: "Home",
    recipient_name: user?.first_name || "",
    recipient_phone: user?.phone_number || "",
    address_line1: "",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "",
    is_default: false,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [pResp, aResp] = await Promise.all([
        customerApi.getProfile(),
        customerApi.getAddresses(),
      ]);
      if (pResp.data?.success) {
        const custData = pResp.data.data?.customer || pResp.data.data;
        setCustomer(custData);
        if (custData?.dietary_preference) {
          setDietaryPref(custData.dietary_preference);
        }
      }
      if (aResp.data?.success) {
        setAddresses(aResp.data.data || []);
      }
    } catch (err) {
      console.error("Profile load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdatePref = async (e) => {
    e.preventDefault();
    setSavingPref(true);
    setPrefSaved(false);
    try {
      const resp = await customerApi.updateProfile({ dietary_preference: dietaryPref });
      if (resp.data?.success) {
        const custData = resp.data.data?.customer || resp.data.data;
        setCustomer(custData);
        if (custData?.dietary_preference) {
          setDietaryPref(custData.dietary_preference);
        }
        setPrefSaved(true);
        setTimeout(() => setPrefSaved(false), 3000);
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.message ||
        (Array.isArray(err.response?.data?.errors) ? err.response.data.errors.join(", ") : null) ||
        err.response?.data?.detail ||
        "Failed to update dietary preference";
      alert(typeof errorMsg === "string" ? errorMsg : "Failed to update dietary preference");
    } finally {
      setSavingPref(false);
    }
  };

  const handleCreateAddress = async (e) => {
    e.preventDefault();
    try {
      const resp = await customerApi.createAddress(newAddr);
      if (resp.data.success) {
        setAddresses([...addresses, resp.data.data]);
        setShowAddModal(false);
      }
    } catch (err) {
      alert("Failed to create address");
    }
  };

  const handleDeleteAddress = async (id) => {
    if (!confirm("Are you sure you want to remove this address?")) return;
    try {
      await customerApi.deleteAddress(id);
      setAddresses(addresses.filter((a) => a.address_id !== id));
    } catch (err) {
      alert("Could not delete address");
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-black text-charcoal-900 tracking-tight mb-8">
        Customer Profile & Settings
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Profile Card & Loyalty Points */}
        <div className="lg:col-span-5 space-y-6">
          {/* User Bio Card */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <div className="flex items-center space-x-4 mb-6">
              <div className="w-14 h-14 rounded-2xl bg-amber-100 text-terracotta-700 font-bold text-xl flex items-center justify-center">
                {user?.first_name?.[0] || "C"}
              </div>
              <div>
                <h3 className="text-xl font-bold text-charcoal-900">
                  {user?.first_name} {user?.last_name}
                </h3>
                <p className="text-xs text-stone-500">{user?.email}</p>
                <p className="text-xs text-stone-400 mt-0.5">{user?.phone_number}</p>
              </div>
            </div>

            {/* Loyalty Points Card */}
            <div className="bg-gradient-to-r from-amber-500 to-terracotta-600 text-white p-5 rounded-2xl shadow-md flex items-center justify-between">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold opacity-90 block">
                  Reward Points
                </span>
                <span className="text-3xl font-black">{customer?.loyalty_points || 0}</span>
                <span className="text-[11px] block opacity-85 mt-1">100 points = ₹100 discount</span>
              </div>
              <Award className="w-10 h-10 opacity-30" />
            </div>

            {/* Dietary Preference Form */}
            <form onSubmit={handleUpdatePref} className="mt-6 pt-6 border-t border-stone-100 space-y-3">
              <label className="block text-xs font-bold uppercase tracking-wider text-stone-500 flex items-center">
                <Heart className="w-3.5 h-3.5 mr-1 text-terracotta-600" />
                Dietary Preference
              </label>
              <select
                value={dietaryPref}
                onChange={(e) => setDietaryPref(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-sm"
              >
                <option value="ALL">All Cuisines (No Restrictions)</option>
                <option value="VEGETARIAN">Vegetarian (Pure Veg)</option>
                <option value="VEGAN">Vegan</option>
                <option value="HALAL">Halal Certified</option>
                <option value="GLUTEN_FREE">Gluten-Free</option>
              </select>
              {prefSaved && (
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-3 py-2 rounded-xl">
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Dietary preference updated successfully!</span>
                </div>
              )}
              <button
                type="submit"
                disabled={savingPref}
                className="w-full py-2.5 bg-stone-900 hover:bg-stone-800 text-white text-xs font-bold rounded-xl transition flex items-center justify-center space-x-1"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{savingPref ? "Saving..." : prefSaved ? "Saved!" : "Save Preference"}</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Saved Delivery Addresses */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-charcoal-900 flex items-center">
                <MapPin className="w-5 h-5 mr-2 text-terracotta-600" />
                Saved Delivery Addresses ({addresses.length})
              </h2>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-3.5 py-1.5 bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold rounded-xl text-xs flex items-center shadow-xs transition"
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Add New Address
              </button>
            </div>

            {addresses.length === 0 ? (
              <p className="text-sm text-stone-500 py-6 text-center border border-dashed border-stone-200 rounded-2xl">
                No addresses saved. Add your primary home or office delivery address.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {addresses.map((addr) => (
                  <div
                    key={addr.address_id}
                    className="p-4 rounded-2xl border border-stone-200 bg-stone-50/50 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400">
                          {addr.address_label}
                        </span>
                        {addr.is_default && (
                          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                            Default
                          </span>
                        )}
                      </div>
                      <h4 className="font-bold text-charcoal-900 text-sm">{addr.recipient_name}</h4>
                      <p className="text-xs text-stone-600 mt-1 line-clamp-2">
                        {addr.address_line1}, {addr.city} {addr.postal_code}
                      </p>
                      <p className="text-xs text-stone-400 mt-1">{addr.recipient_phone}</p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-stone-200/60 flex justify-end">
                      <button
                        onClick={() => handleDeleteAddress(addr.address_id)}
                        className="text-xs text-red-600 hover:text-red-700 flex items-center font-medium"
                      >
                        <Trash2 className="w-3.5 h-3.5 mr-1" />
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Address Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-stone-200">
            <h3 className="text-xl font-bold text-charcoal-900 mb-4">Add Delivery Address</h3>
            <form onSubmit={handleCreateAddress} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-600 mb-1">Address Label</label>
                <select
                  value={newAddr.address_label}
                  onChange={(e) => setNewAddr({ ...newAddr, address_label: e.target.value })}
                  className="w-full px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-sm"
                >
                  <option value="Home">Home</option>
                  <option value="Work">Work</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-stone-600 mb-1">Recipient Name</label>
                <input
                  type="text"
                  required
                  value={newAddr.recipient_name}
                  onChange={(e) => setNewAddr({ ...newAddr, recipient_name: e.target.value })}
                  className="w-full px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-stone-600 mb-1">Phone Number</label>
                <input
                  type="text"
                  required
                  value={newAddr.recipient_phone}
                  onChange={(e) => setNewAddr({ ...newAddr, recipient_phone: e.target.value })}
                  className="w-full px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-stone-600 mb-1">Street Address</label>
                <input
                  type="text"
                  required
                  value={newAddr.address_line1}
                  onChange={(e) => setNewAddr({ ...newAddr, address_line1: e.target.value })}
                  className="w-full px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-stone-600 mb-1">City</label>
                  <input
                    type="text"
                    required
                    value={newAddr.city}
                    onChange={(e) => setNewAddr({ ...newAddr, city: e.target.value })}
                    className="w-full px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-stone-600 mb-1">Postal Code</label>
                  <input
                    type="text"
                    required
                    value={newAddr.postal_code}
                    onChange={(e) => setNewAddr({ ...newAddr, postal_code: e.target.value })}
                    className="w-full px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-sm"
                  />
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-700 font-semibold rounded-xl text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-terracotta-600 hover:bg-terracotta-700 text-white font-semibold rounded-xl text-sm shadow"
                >
                  Save Address
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
