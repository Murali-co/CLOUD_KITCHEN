import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ShoppingBag,
  Plus,
  Minus,
  Trash2,
  Tag,
  ArrowRight,
  Utensils,
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  X,
} from "lucide-react";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { getMenuItemImage, NEUTRAL_FOOD_PLACEHOLDER } from "../utils/menuImages";

export const CartPage = () => {
  const {
    cart,
    loading,
    error: cartError,
    updateQuantity,
    removeItem,
    clearCart,
    applyCoupon,
    removeCoupon,
  } = useCart();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [couponCode, setCouponCode] = useState("");
  const [couponLoading, setCouponLoading] = useState(false);
  const [couponMessage, setCouponMessage] = useState(null);
  const [couponError, setCouponError] = useState(null);

  const handleApplyCoupon = async (e) => {
    e.preventDefault();
    if (!couponCode.trim()) return;
    setCouponLoading(true);
    setCouponError(null);
    setCouponMessage(null);
    try {
      await applyCoupon(couponCode.trim());
      setCouponMessage(`Coupon '${couponCode.toUpperCase()}' applied successfully!`);
      setCouponCode("");
    } catch (err) {
      setCouponError(err.message || "Failed to apply coupon");
    } finally {
      setCouponLoading(false);
    }
  };

  const handleRemoveCoupon = async () => {
    setCouponLoading(true);
    try {
      await removeCoupon();
      setCouponMessage("Coupon removed");
      setCouponError(null);
    } catch (err) {
      setCouponError("Could not remove coupon");
    } finally {
      setCouponLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="w-20 h-20 bg-amber-100 text-terracotta-600 rounded-3xl mx-auto flex items-center justify-center mb-6 shadow-sm">
          <ShoppingBag className="w-10 h-10" />
        </div>
        <h2 className="text-3xl font-bold text-charcoal-900 mb-3">Sign in to view your cart</h2>
        <p className="text-stone-600 mb-8 max-w-md mx-auto">
          Your cloud kitchen cart is synchronized with your profile. Sign in to view saved items and checkout.
        </p>
        <Link
          to="/login"
          state={{ from: { pathname: "/cart" } }}
          className="inline-flex items-center px-6 py-3.5 bg-terracotta-600 hover:bg-terracotta-700 text-white font-semibold rounded-2xl shadow-md transition"
        >
          Sign In Now
        </Link>
      </div>
    );
  }

  const items = cart?.items || [];
  const hasItems = items.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb / Back button */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-2 text-sm text-stone-500">
          <Link to="/menu" className="hover:text-terracotta-600 flex items-center transition">
            <ChevronLeft className="w-4 h-4 mr-1" />
            Continue Shopping
          </Link>
          <span>/</span>
          <span className="text-charcoal-900 font-semibold">Shopping Cart</span>
        </div>
        {hasItems && (
          <button
            onClick={clearCart}
            id="clear-cart-button"
            className="text-xs text-stone-500 hover:text-red-600 flex items-center transition"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1" />
            Clear Entire Cart
          </button>
        )}
      </div>

      <h1 className="text-3xl font-extrabold text-charcoal-900 mb-8 tracking-tight">
        Your Gourmet Cart
      </h1>

      {/* Global Error Banner */}
      {cartError && (
        <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Notice regarding your cart:</p>
            <p>{cartError}</p>
          </div>
        </div>
      )}

      {!hasItems ? (
        /* Empty State */
        <div className="bg-white rounded-3xl p-16 text-center shadow-sm border border-stone-200/70 max-w-2xl mx-auto">
          <div className="w-24 h-24 bg-stone-100 text-stone-400 rounded-full mx-auto flex items-center justify-center mb-6">
            <ShoppingBag className="w-12 h-12 stroke-[1.5]" />
          </div>
          <h3 className="text-2xl font-bold text-charcoal-900 mb-2">Your cart is currently empty</h3>
          <p className="text-stone-500 mb-8">
            Explore our curated chef selections and artisan meals from top local cloud kitchens.
          </p>
          <Link
            to="/menu"
            id="explore-menu-empty-cart-btn"
            className="inline-flex items-center px-8 py-3.5 bg-terracotta-600 hover:bg-terracotta-700 text-white font-semibold rounded-2xl shadow-md shadow-terracotta-600/30 transition transform hover:-translate-y-0.5"
          >
            Explore Menu
            <ArrowRight className="w-4 h-4 ml-2" />
          </Link>
        </div>
      ) : (
        /* Cart Grid */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Items Column */}
          <div className="lg:col-span-8 space-y-4">
            {/* Kitchen Info Card */}
            {cart.kitchen_name && (
              <div className="bg-amber-50/80 border border-amber-200/80 rounded-2xl px-5 py-3.5 flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2 text-stone-800 font-medium">
                  <Utensils className="w-4 h-4 text-terracotta-600" />
                  <span>
                    Fulfilling from: <strong>{cart.kitchen_name}</strong>
                  </span>
                </div>
                <span className="text-xs bg-amber-200/70 text-amber-900 font-semibold px-2 py-0.5 rounded-full">
                  Single-Kitchen Order
                </span>
              </div>
            )}

            {/* Cart Items List */}
            <div className="bg-white rounded-3xl shadow-sm border border-stone-200/70 divide-y divide-stone-100 overflow-hidden">
              {items.map((item) => (
                <div
                  key={item.menu_item_id}
                  className="p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition hover:bg-stone-50/50"
                  id={`cart-item-${item.menu_item_id}`}
                >
                  {/* Left: Dish info & image */}
                  <div className="flex items-center space-x-4">
                    <img
                      src={getMenuItemImage(item)}
                      alt={item.name}
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src = NEUTRAL_FOOD_PLACEHOLDER;
                      }}
                      className="w-20 h-20 rounded-2xl object-cover border border-stone-100 shadow-xs flex-shrink-0"
                    />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`w-3.5 h-3.5 rounded-sm border flex items-center justify-center ${
                            item.is_vegetarian
                              ? "border-green-600"
                              : "border-red-600"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              item.is_vegetarian ? "bg-green-600" : "bg-red-600"
                            }`}
                          />
                        </span>
                        <h4 className="text-base font-bold text-charcoal-900">
                          {item.name}
                        </h4>
                      </div>
                      <p className="text-sm font-semibold text-terracotta-700 mt-1">
                        ₹{parseFloat(item.current_price).toFixed(2)}
                      </p>
                      {!item.is_available && (
                        <span className="inline-block mt-1 text-xs text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded-md font-medium">
                          Currently Out of Stock
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right: Quantity Controls & Subtotal */}
                  <div className="flex items-center justify-between sm:justify-end w-full sm:w-auto space-x-6">
                    {/* Quantity Selector */}
                    <div className="flex items-center border border-stone-200 rounded-xl bg-stone-50/80 p-1">
                      <button
                        onClick={() => updateQuantity(item.menu_item_id, item.quantity - 1)}
                        className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-white text-stone-700 transition"
                        title="Decrease quantity"
                      >
                        <Minus className="w-3.5 h-3.5" />
                      </button>
                      <span className="w-8 text-center text-sm font-bold text-charcoal-900">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => updateQuantity(item.menu_item_id, item.quantity + 1)}
                        className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-white text-stone-700 transition"
                        title="Increase quantity"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Line item total */}
                    <div className="text-right min-w-[80px]">
                      <span className="text-base font-extrabold text-charcoal-900">
                        ₹{parseFloat(item.subtotal_price).toFixed(2)}
                      </span>
                    </div>

                    {/* Remove button */}
                    <button
                      onClick={() => removeItem(item.menu_item_id)}
                      className="p-2 text-stone-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition"
                      title="Remove item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bill Summary Column */}
          <div className="lg:col-span-4 space-y-6">
            {/* Coupon Card */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70">
              <h3 className="text-sm font-bold uppercase tracking-wider text-stone-500 mb-3 flex items-center">
                <Tag className="w-4 h-4 mr-2 text-terracotta-600" />
                Apply Promo Code
              </h3>

              {cart.applied_coupon_code ? (
                <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <div>
                      <p className="text-sm font-bold text-emerald-900 tracking-wide">
                        {cart.applied_coupon_code}
                      </p>
                      <p className="text-xs text-emerald-700">
                        Saved ₹{parseFloat(cart.discount_amount).toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleRemoveCoupon}
                    disabled={couponLoading}
                    className="p-1.5 text-stone-400 hover:text-red-600 rounded-lg hover:bg-emerald-100/50 transition"
                    title="Remove coupon"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <form onSubmit={handleApplyCoupon} className="space-y-2">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                      placeholder="e.g. TEST50 or WELCOME10"
                      className="flex-1 px-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-sm font-medium uppercase focus:outline-none focus:ring-2 focus:ring-terracotta-500"
                    />
                    <button
                      type="submit"
                      disabled={couponLoading || !couponCode.trim()}
                      className="px-4 py-2.5 bg-stone-900 hover:bg-stone-800 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition"
                    >
                      {couponLoading ? "Applying..." : "Apply"}
                    </button>
                  </div>
                  {couponError && (
                    <p className="text-xs text-red-600 font-medium">{couponError}</p>
                  )}
                  {couponMessage && (
                    <p className="text-xs text-emerald-600 font-medium">{couponMessage}</p>
                  )}
                  <p className="text-[11px] text-stone-400">
                    Try demo coupon <strong>TEST50</strong> for 50% discount up to ₹150.
                  </p>
                </form>
              )}
            </div>

            {/* Server-Calculated Bill Details */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70 space-y-4">
              <h3 className="text-base font-bold text-charcoal-900 border-b border-stone-100 pb-3">
                Order Summary
              </h3>

              <div className="space-y-2.5 text-sm">
                <div className="flex justify-between text-stone-600">
                  <span>Item Subtotal</span>
                  <span className="font-semibold text-charcoal-900">
                    ₹{parseFloat(cart.subtotal_amount).toFixed(2)}
                  </span>
                </div>

                {parseFloat(cart.discount_amount) > 0 && (
                  <div className="flex justify-between text-emerald-600 font-medium">
                    <span>Discount Applied</span>
                    <span>-₹{parseFloat(cart.discount_amount).toFixed(2)}</span>
                  </div>
                )}

                <div className="flex justify-between text-stone-600">
                  <span>Delivery Partner Fee</span>
                  <span className="font-semibold text-charcoal-900">
                    ₹{parseFloat(cart.delivery_fee).toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between text-stone-600">
                  <span>GST & Restaurant Taxes (5%)</span>
                  <span className="font-semibold text-charcoal-900">
                    ₹{parseFloat(cart.tax_amount).toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="border-t border-stone-200 pt-4 flex justify-between items-baseline">
                <div>
                  <span className="text-base font-bold text-charcoal-900 block">
                    Grand Total
                  </span>
                  <span className="text-xs text-stone-400">Inclusive of all taxes</span>
                </div>
                <span className="text-2xl font-extrabold text-terracotta-700" id="cart-grand-total">
                  ₹{parseFloat(cart.total_amount).toFixed(2)}
                </span>
              </div>

              {/* Checkout CTA */}
              <button
                onClick={() => navigate("/checkout")}
                id="proceed-to-checkout-btn"
                className="w-full mt-4 py-4 px-6 bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold rounded-2xl shadow-lg shadow-terracotta-600/30 flex items-center justify-center space-x-2 transition transform hover:-translate-y-0.5"
              >
                <span>Proceed to Checkout</span>
                <ArrowRight className="w-5 h-5" />
              </button>

              <p className="text-center text-[11px] text-stone-400">
                Safe & Encrypted 256-bit Checkout Guarantee
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
