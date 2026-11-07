import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  UtensilsCrossed,
  Plus,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Edit3,
  BookOpen,
  Leaf,
  Clock,
  Flame,
  AlertCircle,
  ToggleLeft,
  ToggleRight,
  ShieldCheck,
} from "lucide-react";
import { KitchenLayout } from "../components/KitchenLayout";
import { kitchenApi, catalogApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

export const KitchenMenuPage = () => {
  const { isManager } = useAuth();
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  // Modal State for Add / Edit
  const [showItemModal, setShowItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    category_id: "",
    description: "",
    base_price: "",
    is_vegetarian: false,
    is_available: true,
    preparation_time_minutes: 15,
    calories: "",
    image_url: "",
  });
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");

  const fetchMenuAndCategories = async () => {
    setLoading(true);
    try {
      const [menuRes, catRes] = await Promise.all([
        kitchenApi.getMenu({
          category_id: selectedCategory || undefined,
          search: searchQuery.trim() || undefined,
        }),
        catalogApi.getCategories(),
      ]);

      if (menuRes.data?.success) setMenuItems(menuRes.data.data);
      if (catRes.data?.success) setCategories(catRes.data.data);
    } catch (err) {
      console.error("Failed to load kitchen menu", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMenuAndCategories();
  }, [selectedCategory]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchMenuAndCategories();
  };

  const handleToggleAvailability = async (item) => {
    const updatedStatus = !item.is_available;
    try {
      const resp = await kitchenApi.updateMenuAvailability(item.menu_item_id, updatedStatus);
      if (resp.data?.success) {
        setMenuItems((prev) =>
          prev.map((m) => (m.menu_item_id === item.menu_item_id ? { ...m, is_available: updatedStatus } : m))
        );
      }
    } catch (err) {
      alert("Failed to update dish availability state");
    }
  };

  const openCreateModal = () => {
    setEditingItem(null);
    setFormData({
      name: "",
      category_id: categories[0]?.category_id || "",
      description: "",
      base_price: "",
      is_vegetarian: false,
      is_available: true,
      preparation_time_minutes: 15,
      calories: "",
      image_url: "",
    });
    setModalError("");
    setShowItemModal(true);
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      category_id: item.category_id,
      description: item.description || "",
      base_price: item.base_price,
      is_vegetarian: item.is_vegetarian,
      is_available: item.is_available,
      preparation_time_minutes: item.preparation_time_minutes,
      calories: item.calories || "",
      image_url: item.image_url || "",
    });
    setModalError("");
    setShowItemModal(true);
  };

  const handleModalSubmit = async (e) => {
    e.preventDefault();
    setModalLoading(true);
    setModalError("");

    try {
      const payload = {
        ...formData,
        category_id: Number(formData.category_id),
        base_price: parseFloat(formData.base_price),
        preparation_time_minutes: Number(formData.preparation_time_minutes),
        calories: formData.calories ? Number(formData.calories) : undefined,
        image_url: formData.image_url?.trim() || undefined,
        description: formData.description?.trim() || undefined,
      };

      if (editingItem) {
        const resp = await kitchenApi.updateMenuItem(editingItem.menu_item_id, payload);
        if (resp.data?.success) {
          setShowItemModal(false);
          fetchMenuAndCategories();
        }
      } else {
        const resp = await kitchenApi.createMenuItem(payload);
        if (resp.data?.success) {
          setShowItemModal(false);
          fetchMenuAndCategories();
        }
      }
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to save menu dish");
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <KitchenLayout
      title="Kitchen Menu & Catalog"
      subtitle="Manage menu availability, recipe links, prices, and preparation specifications"
      actionButton={
        isManager ? (
          <button
            onClick={openCreateModal}
            className="flex items-center space-x-2 px-4 py-2.5 bg-terracotta-600 hover:bg-terracotta-700 text-white rounded-2xl text-xs font-bold transition shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Dish</span>
          </button>
        ) : (
          <span className="text-xs text-stone-500 font-medium bg-stone-100 px-3 py-1.5 rounded-xl">
            Manager privilege required to add dishes
          </span>
        )
      }
    >
      {/* Category Filter and Search */}
      <div className="bg-white rounded-3xl border border-stone-200/80 p-5 shadow-sm mb-6">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-stone-400" />
            <input
              type="text"
              placeholder="Search dishes by name or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
            />
          </div>

          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.category_id} value={c.category_id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="submit"
              className="px-4 py-2.5 bg-terracotta-600 hover:bg-terracotta-700 text-white rounded-2xl text-xs font-bold transition shadow-sm flex-1"
            >
              Search
            </button>
            {(searchQuery || selectedCategory) && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setSelectedCategory("");
                  fetchMenuAndCategories();
                }}
                className="px-3.5 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-600 rounded-2xl text-xs font-semibold transition"
              >
                Clear
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Dishes Grid */}
      {loading ? (
        <div className="py-24 text-center">
          <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm font-semibold text-stone-600">Loading kitchen catalog...</p>
        </div>
      ) : menuItems.length === 0 ? (
        <div className="py-24 text-center bg-white rounded-3xl border border-stone-200 p-8 shadow-sm">
          <UtensilsCrossed className="w-12 h-12 text-stone-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-charcoal-900 mb-1">No menu dishes found</h3>
          <p className="text-xs text-stone-500 max-w-md mx-auto">
            Try adjusting your search criteria or add dishes to your kitchen catalog.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {menuItems.map((item) => (
            <div
              key={item.menu_item_id}
              className={`rounded-3xl bg-white border p-6 flex flex-col justify-between shadow-sm transition hover:shadow-md ${
                item.is_available ? "border-stone-200/80" : "border-stone-200 bg-stone-50/50 opacity-80"
              }`}
            >
              <div>
                {/* Header: Name, Veg Icon, Price */}
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`w-4 h-4 rounded-md border flex items-center justify-center shrink-0 ${
                        item.is_vegetarian
                          ? "border-emerald-600 text-emerald-600"
                          : "border-rose-600 text-rose-600"
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full ${item.is_vegetarian ? "bg-emerald-600" : "bg-rose-600"}`}></span>
                    </span>
                    <h3 className="text-base font-bold text-charcoal-900 leading-snug">{item.name}</h3>
                  </div>
                  <span className="text-base font-black text-charcoal-900 shrink-0">
                    ₹{parseFloat(item.base_price).toFixed(2)}
                  </span>
                </div>

                <p className="text-xs text-stone-500 line-clamp-2 mb-3">
                  {item.description || "No recipe description provided"}
                </p>

                {/* Badges: Category, Prep Time, Calories */}
                <div className="flex flex-wrap items-center gap-2 mb-4 text-[11px] text-stone-500 font-medium">
                  <span className="px-2 py-0.5 rounded-md bg-stone-100 text-stone-700">
                    {item.category_name}
                  </span>
                  <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-stone-100">
                    <Clock className="w-3 h-3 text-stone-400" />
                    <span>{item.preparation_time_minutes}m prep</span>
                  </span>
                  {item.calories && (
                    <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-stone-100">
                      <Flame className="w-3 h-3 text-stone-400" />
                      <span>{item.calories} kcal</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Bottom Actions: 86 Toggle, Recipe BOM Link, Edit */}
              <div className="pt-4 border-t border-stone-100 flex items-center justify-between gap-2">
                {/* Availability Toggle */}
                <button
                  onClick={() => handleToggleAvailability(item)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                    item.is_available
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                      : "bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100"
                  }`}
                  title="Toggle dish availability on online store (86 item)"
                >
                  <span className={`w-2 h-2 rounded-full ${item.is_available ? "bg-emerald-500" : "bg-rose-500"}`}></span>
                  <span>{item.is_available ? "In Stock (Available)" : "86'd (Sold Out)"}</span>
                </button>

                <div className="flex items-center space-x-1.5">
                  {/* Link to Recipe Bill of Materials */}
                  <Link
                    to={`/kitchen/recipes?item_id=${item.menu_item_id}`}
                    className="p-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 transition"
                    title="Configure Recipe Bill of Materials"
                  >
                    <BookOpen className="w-4 h-4 text-terracotta-600" />
                  </Link>

                  {/* Edit Item (Managers Only) */}
                  {isManager && (
                    <button
                      onClick={() => openEditModal(item)}
                      className="p-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 transition"
                      title="Edit Dish Properties"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Dish Modal (Managers Only) */}
      {showItemModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in overflow-y-auto">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-lg w-full p-6 shadow-2xl my-8">
            <h3 className="text-lg font-bold text-charcoal-900 mb-1">
              {editingItem ? `Edit Dish: ${editingItem.name}` : "Create New Kitchen Dish"}
            </h3>
            <p className="text-xs text-stone-500 mb-6">
              Specifying accurate pricing and preparation metadata ensures consistent online menu publishing.
            </p>

            {modalError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium mb-4">
                {modalError}
              </div>
            )}

            <form onSubmit={handleModalSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Dish Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Malabar Fish Curry"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Category *</label>
                  <select
                    required
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
                  >
                    {categories.map((c) => (
                      <option key={c.category_id} value={c.category_id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Base Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    required
                    placeholder="250.00"
                    value={formData.base_price}
                    onChange={(e) => setFormData({ ...formData, base_price: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Detailed culinary description and flavor profile..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                ></textarea>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Prep Time (Mins) *</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={formData.preparation_time_minutes}
                    onChange={(e) => setFormData({ ...formData, preparation_time_minutes: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Calories (Kcal)</label>
                  <input
                    type="number"
                    min="0"
                    placeholder="450"
                    value={formData.calories}
                    onChange={(e) => setFormData({ ...formData, calories: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-6 pt-2">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_vegetarian}
                    onChange={(e) => setFormData({ ...formData, is_vegetarian: e.target.checked })}
                    className="w-4 h-4 text-terracotta-600 rounded focus:ring-terracotta-500 border-stone-300"
                  />
                  <span className="text-xs font-semibold text-stone-700">Vegetarian Dish</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_available}
                    onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                    className="w-4 h-4 text-terracotta-600 rounded focus:ring-terracotta-500 border-stone-300"
                  />
                  <span className="text-xs font-semibold text-stone-700">Currently Available</span>
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-stone-100">
                <button
                  type="button"
                  disabled={modalLoading}
                  onClick={() => setShowItemModal(false)}
                  className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-5 py-2 rounded-xl bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold text-xs transition shadow-sm flex items-center space-x-1.5"
                >
                  {modalLoading && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                  <span>{editingItem ? "Update Dish" : "Create Dish"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </KitchenLayout>
  );
};
