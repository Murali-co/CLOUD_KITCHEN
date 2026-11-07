import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Filter, Utensils, Clock, Check, AlertCircle, Globe } from "lucide-react";
import { catalogApi } from "../services/api";
import { useCart } from "../context/CartContext";
import { getMenuItemImage, NEUTRAL_FOOD_PLACEHOLDER } from "../utils/menuImages";

export const MenuPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { addItem, cart, clearCart } = useCart();

  const [items, setItems] = useState([]);
  const [kitchens, setKitchens] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cuisines, setCuisines] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedKitchen, setSelectedKitchen] = useState(searchParams.get("kitchen") || "");
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get("category") || "");
  const [selectedCuisine, setSelectedCuisine] = useState(searchParams.get("cuisine") || "");
  const [searchQuery, setSearchQuery] = useState(searchParams.get("search") || "");
  const [vegOnly, setVegOnly] = useState(false);

  const [addingId, setAddingId] = useState(null);
  const [mixedKitchenPrompt, setMixedKitchenPrompt] = useState(null);

  // Synchronize state when URL query parameters change (e.g. from HomePage navigation)
  useEffect(() => {
    const cuParam = searchParams.get("cuisine");
    if (cuParam !== null && cuParam !== selectedCuisine) {
      setSelectedCuisine(cuParam);
    }
    const catParam = searchParams.get("category");
    if (catParam !== null && catParam !== selectedCategory) {
      setSelectedCategory(catParam);
    }
    const kParam = searchParams.get("kitchen");
    if (kParam !== null && kParam !== selectedKitchen) {
      setSelectedKitchen(kParam);
    }
    const sParam = searchParams.get("search");
    if (sParam !== null && sParam !== searchQuery) {
      setSearchQuery(sParam);
    }
  }, [searchParams]);

  // Fetch filter options (Kitchens, Categories, Cuisines)
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [kResp, cResp, cuResp] = await Promise.all([
          catalogApi.getKitchens(),
          catalogApi.getCategories(),
          catalogApi.getCuisines(),
        ]);
        if (kResp.data.success) {
          const kItems = kResp.data.data?.items || (Array.isArray(kResp.data.data) ? kResp.data.data : []);
          setKitchens(kItems);
        }
        if (cResp.data.success) {
          const cItems = Array.isArray(cResp.data.data) ? cResp.data.data : (cResp.data.data?.items || []);
          setCategories(cItems);
        }
        if (cuResp.data.success) {
          const cuItems = Array.isArray(cuResp.data.data) ? cuResp.data.data : (cuResp.data.data?.items || []);
          setCuisines(cuItems);
        }
      } catch (err) {
        console.error("Filter options load error:", err);
      }
    };
    loadFilters();
  }, []);

  // Fetch menu items based on active filters
  useEffect(() => {
    const fetchMenuItems = async () => {
      try {
        setLoading(true);
        const params = {
          page: 1,
          page_size: 40,
        };
        if (selectedKitchen) params.kitchen_id = selectedKitchen;
        if (selectedCategory) params.category_id = selectedCategory;
        if (selectedCuisine) params.cuisine_id = selectedCuisine;
        if (searchQuery.trim()) params.search = searchQuery.trim();
        if (vegOnly) params.is_vegetarian = true;

        const resp = await catalogApi.getMenu(params);
        if (resp.data.success) {
          setItems(resp.data.data.items);
        }
      } catch (err) {
        console.error("Menu fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMenuItems();
  }, [selectedKitchen, selectedCategory, selectedCuisine, searchQuery, vegOnly]);

  const handleAddToCart = async (item) => {
    setAddingId(item.menu_item_id);
    try {
      await addItem(item.menu_item_id, 1);
    } catch (err) {
      if (err.message && err.message.toLowerCase().includes("different kitchen")) {
        setMixedKitchenPrompt(item);
      } else {
        alert(err.message || "Failed to add to cart");
      }
    } finally {
      setAddingId(null);
    }
  };

  const handleReplaceCart = async () => {
    if (!mixedKitchenPrompt) return;
    try {
      await clearCart();
      await addItem(mixedKitchenPrompt.menu_item_id, 1);
      setMixedKitchenPrompt(null);
    } catch (e) {
      alert("Failed to replace cart");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-charcoal-900 tracking-tight">Full Culinary Menu</h1>
        <p className="text-sm text-stone-500 mt-1">
          Explore artisanal dishes prepped live across our hygienic cloud kitchen facilities.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70 mb-8 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
          {/* Search Input */}
          <div className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by dish name or ingredient..."
              className="w-full pl-10 pr-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-terracotta-500"
            />
          </div>

          {/* Kitchen Selector */}
          <div>
            <select
              value={selectedKitchen}
              onChange={(e) => setSelectedKitchen(e.target.value)}
              className="w-full px-3 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-terracotta-500"
            >
              <option value="">All Cloud Kitchens</option>
              {kitchens.map((k) => (
                <option key={k.kitchen_id} value={k.kitchen_id}>
                  {k.name} ({k.branch_code})
                </option>
              ))}
            </select>
          </div>

          {/* Vegetarian Toggle */}
          <div className="flex items-center space-x-2 pl-2">
            <input
              type="checkbox"
              id="veg-only-checkbox"
              checked={vegOnly}
              onChange={(e) => setVegOnly(e.target.checked)}
              className="w-4 h-4 text-terracotta-600 rounded-sm focus:ring-terracotta-500"
            />
            <label htmlFor="veg-only-checkbox" className="text-xs font-bold text-stone-700 cursor-pointer">
              Pure Vegetarian Only
            </label>
          </div>
        </div>

        {/* Cuisine Filter Pills */}
        <div className="pt-2 border-t border-stone-100">
          <div className="flex items-center space-x-2 mb-2">
            <Globe className="w-3.5 h-3.5 text-stone-400" />
            <span className="text-xs font-bold text-stone-500 uppercase tracking-wider">Cuisine Origin:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCuisine("")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                selectedCuisine === ""
                  ? "bg-stone-900 text-white shadow-xs"
                  : "bg-stone-100 text-stone-700 hover:bg-stone-200"
              }`}
            >
              All Cuisines
            </button>
            {cuisines.map((cu) => (
              <button
                key={cu.cuisine_id}
                onClick={() => setSelectedCuisine(String(cu.cuisine_id))}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 ${
                  selectedCuisine === String(cu.cuisine_id)
                    ? "bg-stone-900 text-white shadow-xs"
                    : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                }`}
              >
                <span>{cu.cuisine_name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Category Pills */}
        <div className="pt-2 border-t border-stone-100">
          <div className="flex items-center space-x-2 mb-2">
            <Utensils className="w-3.5 h-3.5 text-stone-400" />
            <span className="text-xs font-bold text-stone-500 uppercase tracking-wider">Food Category:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory("")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                selectedCategory === ""
                  ? "bg-terracotta-600 text-white shadow-xs"
                  : "bg-stone-100 text-stone-700 hover:bg-stone-200"
              }`}
            >
              All Categories
            </button>
            {categories.map((c) => (
              <button
                key={c.category_id}
                onClick={() => setSelectedCategory(String(c.category_id))}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                  selectedCategory === String(c.category_id)
                    ? "bg-terracotta-600 text-white shadow-xs"
                    : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                }`}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Menu Items Grid */}
      {loading ? (
        <div className="py-24 text-center">
          <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm text-stone-500">Loading chef menu...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-3xl p-16 text-center shadow-sm border border-stone-200/70 max-w-md mx-auto">
          <p className="text-stone-500 font-medium">No dishes match your selected filter criteria.</p>
          <button
            onClick={() => {
              setSelectedKitchen("");
              setSelectedCategory("");
              setSelectedCuisine("");
              setSearchQuery("");
              setVegOnly(false);
              setSearchParams({});
            }}
            className="mt-4 px-4 py-2 bg-stone-900 text-white text-xs font-bold rounded-xl"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {items.map((dish) => {
            const dishCuisine = cuisines.find((c) => c.cuisine_id === dish.cuisine_id);
            return (
              <div
                key={dish.menu_item_id}
                className="bg-white rounded-3xl overflow-hidden shadow-sm border border-stone-200/70 hover:shadow-lg transition flex flex-col justify-between"
                id={`dish-card-${dish.menu_item_id}`}
              >
                <div>
                  <div className="aspect-[4/3] relative overflow-hidden bg-stone-100">
                    <img
                      src={getMenuItemImage(dish)}
                      alt={dish.name}
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src = NEUTRAL_FOOD_PLACEHOLDER;
                      }}
                      className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                    />
                    <span
                      className={`absolute top-3 left-3 w-4 h-4 rounded-sm border bg-white flex items-center justify-center shadow-xs ${
                        dish.is_vegetarian ? "border-green-600" : "border-red-600"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          dish.is_vegetarian ? "bg-green-600" : "bg-red-600"
                        }`}
                      />
                    </span>
                    {!dish.is_available && (
                      <div className="absolute inset-0 bg-stone-900/60 backdrop-blur-2xs flex items-center justify-center">
                        <span className="px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-lg uppercase tracking-wider">
                          Sold Out
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="p-5">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400">
                        {dish.kitchen_name}
                      </span>
                      {dishCuisine && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200/60 uppercase tracking-wider">
                          {dishCuisine.cuisine_name}
                        </span>
                      )}
                    </div>
                    <h4 className="font-bold text-charcoal-900 text-base">{dish.name}</h4>
                    <p className="text-xs text-stone-500 mt-1 line-clamp-2">
                      {dish.description || "Prepared fresh by dedicated chef brigade."}
                    </p>
                    <div className="flex items-center space-x-3 text-[11px] text-stone-400 mt-3">
                      <span className="flex items-center">
                        <Clock className="w-3.5 h-3.5 mr-1" />
                        {dish.preparation_time_minutes} mins prep
                      </span>
                      {dish.calories && <span>{dish.calories} kcal</span>}
                    </div>
                  </div>
                </div>

              <div className="p-5 pt-0 flex items-center justify-between">
                <span className="text-lg font-black text-charcoal-900">
                  ₹{parseFloat(dish.base_price).toFixed(2)}
                </span>
                <button
                  onClick={() => handleAddToCart(dish)}
                  disabled={addingId === dish.menu_item_id || !dish.is_available}
                  className="px-4 py-2 bg-terracotta-600 hover:bg-terracotta-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-xs transition"
                >
                  {addingId === dish.menu_item_id ? "Adding..." : "+ Add to Cart"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    )}

      {/* Mixed Kitchen Cart Alert Modal */}
      {mixedKitchenPrompt && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-stone-200">
            <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center mb-4">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-charcoal-900 mb-2">Replace Cart Items?</h3>
            <p className="text-xs text-stone-600 leading-relaxed mb-6">
              Your cart currently contains items from <strong>{cart?.kitchen_name || "another kitchen"}</strong>. To preserve hot, fresh delivery, orders must come from a single cloud kitchen.
              Would you like to clear your current cart and start an order from <strong>{mixedKitchenPrompt.kitchen_name}</strong>?
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => setMixedKitchenPrompt(null)}
                className="flex-1 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-700 font-semibold rounded-xl text-xs"
              >
                Keep Current Cart
              </button>
              <button
                onClick={handleReplaceCart}
                className="flex-1 py-2.5 bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold rounded-xl text-xs shadow"
              >
                Clear & Add Dish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
