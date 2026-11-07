import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ChevronLeft, MapPin, Phone, Mail, Clock, ArrowRight } from "lucide-react";
import { catalogApi } from "../services/api";
import { useCart } from "../context/CartContext";
import { getMenuItemImage, NEUTRAL_FOOD_PLACEHOLDER } from "../utils/menuImages";

export const KitchenDetailPage = () => {
  const { id } = useParams();
  const { addItem } = useCart();
  const [kitchen, setKitchen] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addingId, setAddingId] = useState(null);

  useEffect(() => {
    const fetchKitchenAndMenu = async () => {
      try {
        setLoading(true);
        const [kResp, mResp] = await Promise.all([
          catalogApi.getKitchenDetail(id),
          catalogApi.getMenu({ kitchen_id: id, page_size: 50 }),
        ]);
        if (kResp.data.success) setKitchen(kResp.data.data);
        if (mResp.data.success) setMenuItems(mResp.data.data.items);
      } catch (err) {
        console.error("Kitchen detail error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchKitchenAndMenu();
  }, [id]);

  const handleAdd = async (item) => {
    setAddingId(item.menu_item_id);
    try {
      await addItem(item.menu_item_id, 1);
    } catch (err) {
      alert(err.message || "Failed to add item to cart");
    } finally {
      setAddingId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!kitchen) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-charcoal-900 mb-2">Kitchen Not Found</h2>
        <Link to="/kitchens" className="px-6 py-3 bg-stone-900 text-white font-bold rounded-2xl">
          Back to Kitchens
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Link to="/kitchens" className="inline-flex items-center text-sm text-stone-500 hover:text-terracotta-600 mb-6">
        <ChevronLeft className="w-4 h-4 mr-1" />
        All Cloud Kitchens
      </Link>

      {/* Kitchen Hero Banner */}
      <div className="bg-white rounded-3xl p-8 sm:p-10 shadow-sm border border-stone-200/70 mb-10">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <span className="text-xs font-bold text-terracotta-700 bg-terracotta-50 px-3 py-1 rounded-full uppercase tracking-wider font-mono">
                {kitchen.branch_code}
              </span>
              <span className="text-xs text-emerald-700 bg-emerald-50 font-bold px-2.5 py-0.5 rounded-full">
                Active Kitchen Hub
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-charcoal-900 tracking-tight">{kitchen.name}</h1>
            <p className="text-sm text-stone-500 mt-2 flex items-center">
              <MapPin className="w-4 h-4 text-stone-400 mr-1.5 flex-shrink-0" />
              {kitchen.address_line1}, {kitchen.city}, {kitchen.state} {kitchen.postal_code}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 text-xs text-stone-600 border-t md:border-t-0 md:border-l border-stone-100 pt-4 md:pt-0 md:pl-6">
            <div>
              <span className="text-stone-400 block font-medium">Contact Phone</span>
              <span className="font-bold text-stone-800">{kitchen.contact_phone}</span>
            </div>
            <div>
              <span className="text-stone-400 block font-medium">Estimated Dispatch</span>
              <span className="font-bold text-stone-800">15–20 Minutes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Kitchen Dishes */}
      <h2 className="text-2xl font-black text-charcoal-900 tracking-tight mb-6">
        Available from this Kitchen ({menuItems.length})
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {menuItems.map((dish) => (
          <div
            key={dish.menu_item_id}
            className="bg-white rounded-3xl overflow-hidden shadow-sm border border-stone-200/70 hover:shadow-lg transition flex flex-col justify-between"
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
              </div>
              <div className="p-5">
                <h4 className="font-bold text-charcoal-900 text-base">{dish.name}</h4>
                <p className="text-xs text-stone-500 mt-1 line-clamp-2">
                  {dish.description || "Prepared with fresh organic ingredients."}
                </p>
              </div>
            </div>

            <div className="p-5 pt-0 flex items-center justify-between">
              <span className="text-lg font-black text-charcoal-900">
                ₹{parseFloat(dish.base_price).toFixed(2)}
              </span>
              <button
                onClick={() => handleAdd(dish)}
                disabled={addingId === dish.menu_item_id || !dish.is_available}
                className="px-4 py-2 bg-terracotta-600 hover:bg-terracotta-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-xs transition"
              >
                {addingId === dish.menu_item_id ? "Adding..." : "+ Add to Cart"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
