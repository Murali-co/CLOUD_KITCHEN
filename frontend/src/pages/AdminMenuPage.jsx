import React, { useState, useEffect } from "react";
import { 
  UtensilsCrossed, 
  Search, 
  Filter, 
  Plus, 
  Building2, 
  FolderPlus, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Edit3, 
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Power,
  Tag,
  DollarSign,
  Layers,
  Image as ImageIcon
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

export const AdminMenuPage = () => {
  const [activeTab, setActiveTab] = useState("items"); // "items" or "categories"

  // Menu items state
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [kitchens, setKitchens] = useState([]);
  const [totalItems, setTotalItems] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Filters
  const [search, setSearch] = useState("");
  const [kitchenFilter, setKitchenFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [availabilityFilter, setAvailabilityFilter] = useState("");

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Category Modal
  const [catModalOpen, setCatModalOpen] = useState(false);
  const [editingCat, setEditingCat] = useState(null);
  const [catFormData, setCatFormData] = useState({
    name: "",
    description: "",
    display_order: 0,
    is_active: true,
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      // Fetch categories & kitchens for filters/management
      const [catResp, kitchenResp] = await Promise.all([
        adminApi.getCategories(),
        adminApi.getKitchens({ page_size: 100 }),
      ]);

      if (catResp.data.success) {
        setCategories(catResp.data.data || []);
      }
      if (kitchenResp.data.success) {
        setKitchens(kitchenResp.data.data.items || []);
      }

      // Fetch menu items
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (kitchenFilter) params.kitchen_id = parseInt(kitchenFilter, 10);
      if (categoryFilter) params.category_id = parseInt(categoryFilter, 10);
      if (availabilityFilter !== "") params.is_available = availabilityFilter === "true";

      const menuResp = await adminApi.getMenu(params);
      if (menuResp.data.success) {
        setMenuItems(menuResp.data.data.items || []);
        setTotalItems(menuResp.data.data.meta?.total_count || 0);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load catalog information.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, kitchenFilter, categoryFilter, availabilityFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const handleToggleAvailability = async (item) => {
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const resp = await adminApi.updateMenuItemStatus(item.item_id, {
        is_available: !item.is_available,
      });
      if (resp.data.success) {
        setSuccessMsg(`Status updated for "${item.name}"`);
        await fetchData();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to toggle item availability.");
    } finally {
      setActionLoading(false);
    }
  };

  const openCreateCategory = () => {
    setEditingCat(null);
    setCatFormData({
      name: "",
      description: "",
      display_order: categories.length + 1,
      is_active: true,
    });
    setCatModalOpen(true);
  };

  const openEditCategory = (cat) => {
    setEditingCat(cat);
    setCatFormData({
      name: cat.name,
      description: cat.description || "",
      display_order: cat.display_order || 0,
      is_active: cat.is_active,
    });
    setCatModalOpen(true);
  };

  const handleSaveCategory = async (e) => {
    e.preventDefault();
    if (!catFormData.name.trim()) return;
    setActionLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      if (editingCat) {
        const resp = await adminApi.updateCategory(editingCat.category_id, catFormData);
        if (resp.data.success) {
          setSuccessMsg(`Category "${resp.data.data.name}" updated successfully.`);
        }
      } else {
        const resp = await adminApi.createCategory(catFormData);
        if (resp.data.success) {
          setSuccessMsg(`Category "${resp.data.data.name}" created successfully.`);
        }
      }
      setCatModalOpen(false);
      await fetchData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to save category.");
    } finally {
      setActionLoading(false);
    }
  };

  const totalPages = Math.ceil(totalItems / pageSize) || 1;

  return (
    <AdminLayout
      title="Menu & Category Administration"
      subtitle="Oversee menu offerings across kitchen facilities and maintain global food categories"
      actions={
        <div className="flex items-center space-x-2">
          {activeTab === "categories" && (
            <button
              onClick={openCreateCategory}
              className="flex items-center space-x-2 px-3 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Add Category</span>
            </button>
          )}
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

      {/* Tabs */}
      <div className="flex border-b border-stone-200 gap-6 text-xs font-bold">
        <button
          onClick={() => setActiveTab("items")}
          className={`pb-3 flex items-center space-x-2 transition border-b-2 ${
            activeTab === "items"
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-stone-500 hover:text-stone-700"
          }`}
        >
          <UtensilsCrossed className="w-4 h-4" />
          <span>Menu Offerings ({totalItems})</span>
        </button>
        <button
          onClick={() => setActiveTab("categories")}
          className={`pb-3 flex items-center space-x-2 transition border-b-2 ${
            activeTab === "categories"
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-stone-500 hover:text-stone-700"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Global Categories ({categories.length})</span>
        </button>
      </div>

      {/* TAB 1: MENU ITEMS */}
      {activeTab === "items" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-white p-4 rounded-2xl border border-stone-200 shadow-xs flex flex-wrap items-center gap-3">
            <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-[200px]">
              <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search menu items..."
                className="w-full pl-9 pr-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
              />
            </form>

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

            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.category_id} value={c.category_id}>
                  {c.name}
                </option>
              ))}
            </select>

            <select
              value={availabilityFilter}
              onChange={(e) => {
                setAvailabilityFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
            >
              <option value="">Availability: All</option>
              <option value="true">Available Now</option>
              <option value="false">Unavailable</option>
            </select>

            {(search || kitchenFilter || categoryFilter || availabilityFilter !== "") && (
              <button
                onClick={() => {
                  setSearch("");
                  setKitchenFilter("");
                  setCategoryFilter("");
                  setAvailabilityFilter("");
                  setPage(1);
                }}
                className="text-xs text-purple-600 font-bold hover:underline"
              >
                Reset
              </button>
            )}
          </div>

          {/* Menu Items Table */}
          <div className="bg-white rounded-2xl border border-stone-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-stone-50 border-b border-stone-200 text-stone-500 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Item Name</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Cloud Kitchen</th>
                    <th className="py-3 px-4">Base Price</th>
                    <th className="py-3 px-4">Prep Time</th>
                    <th className="py-3 px-4">Availability</th>
                    <th className="py-3 px-4 text-right">Toggle</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="text-center py-10 text-stone-400 font-medium">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-600" />
                        Loading menu catalog...
                      </td>
                    </tr>
                  ) : menuItems.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-stone-400 font-medium">
                        <UtensilsCrossed className="w-8 h-8 mx-auto mb-2 text-stone-300" />
                        No menu items found matching the selected filters.
                      </td>
                    </tr>
                  ) : (
                    menuItems.map((item) => (
                      <tr key={item.item_id} className="hover:bg-stone-50/60 transition">
                        <td className="py-3.5 px-4">
                          <div className="flex items-center space-x-2.5">
                            <div className="w-8 h-8 rounded-lg bg-stone-100 border border-stone-200 flex items-center justify-center font-bold text-stone-500 shrink-0">
                              <UtensilsCrossed className="w-4 h-4 text-purple-600" />
                            </div>
                            <div>
                              <p className="font-bold text-charcoal-900">{item.name}</p>
                              <span className="text-[10px] text-stone-400 font-mono">ID #{item.item_id}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                            {item.category_name || "Uncategorized"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center space-x-1.5 font-bold text-charcoal-800">
                            <Building2 className="w-3.5 h-3.5 text-stone-400" />
                            <span>{item.kitchen_name}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-bold text-charcoal-900">
                          ₹{Number(item.base_price).toFixed(2)}
                        </td>
                        <td className="py-3.5 px-4 text-stone-600">
                          {item.preparation_time_minutes ? `${item.preparation_time_minutes} mins` : "—"}
                        </td>
                        <td className="py-3.5 px-4">
                          {item.is_available ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              Available
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-500 border border-stone-200">
                              <XCircle className="w-3 h-3 mr-1" />
                              Unavailable
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => handleToggleAvailability(item)}
                            disabled={actionLoading}
                            className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border font-bold transition text-[11px] ${
                              item.is_available
                                ? "border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100"
                                : "border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                            }`}
                          >
                            <Power className="w-3.5 h-3.5" />
                            <span>{item.is_available ? "Set Out of Stock" : "Make Available"}</span>
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
        </div>
      )}

      {/* TAB 2: GLOBAL CATEGORIES */}
      {activeTab === "categories" && (
        <div className="bg-white rounded-2xl border border-stone-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-stone-50 border-b border-stone-200 text-stone-500 font-bold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Order</th>
                  <th className="py-3 px-4">Category Name</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Slug</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {categories.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-stone-400 font-medium">
                      No categories configured yet.
                    </td>
                  </tr>
                ) : (
                  categories.map((cat) => (
                    <tr key={cat.category_id} className="hover:bg-stone-50/60 transition">
                      <td className="py-3.5 px-4 font-mono font-bold text-stone-500">
                        #{cat.display_order}
                      </td>
                      <td className="py-3.5 px-4 font-bold text-charcoal-900">
                        {cat.name}
                      </td>
                      <td className="py-3.5 px-4 text-stone-500 max-w-xs truncate">
                        {cat.description || "—"}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-purple-700">
                        {cat.slug}
                      </td>
                      <td className="py-3.5 px-4">
                        {cat.is_active ? (
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
                          onClick={() => openEditCategory(cat)}
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
        </div>
      )}

      {/* CATEGORY MODAL */}
      {catModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-stone-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <h3 className="text-sm font-bold text-charcoal-900">
                {editingCat ? `Edit Category: ${editingCat.name}` : "Create Food Category"}
              </h3>
              <button
                onClick={() => setCatModalOpen(false)}
                className="text-stone-400 hover:text-stone-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveCategory} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Category Name *</label>
                <input
                  type="text"
                  required
                  value={catFormData.name}
                  onChange={(e) => setCatFormData({ ...catFormData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g. Biryanis & Bowls"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={catFormData.description}
                  onChange={(e) => setCatFormData({ ...catFormData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                  placeholder="Short description for customer browsing"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Display Order</label>
                <input
                  type="number"
                  min={0}
                  value={catFormData.display_order}
                  onChange={(e) => setCatFormData({ ...catFormData, display_order: parseInt(e.target.value, 10) || 0 })}
                  className="w-full px-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="catActiveToggle"
                  checked={catFormData.is_active}
                  onChange={(e) => setCatFormData({ ...catFormData, is_active: e.target.checked })}
                  className="rounded text-purple-600 focus:ring-purple-500"
                />
                <label htmlFor="catActiveToggle" className="text-xs font-bold text-stone-700">
                  Category Active & Visible to Customers
                </label>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-4 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setCatModalOpen(false)}
                  className="px-4 py-2 border border-stone-200 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold hover:bg-purple-700 disabled:opacity-50"
                >
                  {actionLoading ? "Saving..." : editingCat ? "Update Category" : "Create Category"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};
