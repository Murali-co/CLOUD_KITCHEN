import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  MapPin,
  CreditCard,
  Banknote,
  Smartphone,
  ShieldCheck,
  AlertCircle,
  Plus,
  Check,
  ChevronLeft,
  ArrowRight,
} from "lucide-react";
import { customerApi, checkoutApi, orderApi, cartApi } from "../services/api";
import { useCart } from "../context/CartContext";

export const CheckoutPage = () => {
  const navigate = useNavigate();
  const { cart, fetchCart } = useCart();

  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [validationErrors, setValidationErrors] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState("UPI");
  const [specialInstructions, setSpecialInstructions] = useState("");
  const [placingOrder, setPlacingOrder] = useState(false);
  const [showNewAddressModal, setShowNewAddressModal] = useState(false);

  // New Address form state
  const [newAddr, setNewAddr] = useState({
    address_label: "Home",
    recipient_name: "",
    recipient_phone: "",
    address_line1: "",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "",
    is_default: true,
  });

  // Load addresses on mount
  useEffect(() => {
    const loadAddresses = async () => {
      try {
        const resp = await customerApi.getAddresses();
        if (resp.data.success && resp.data.data.length > 0) {
          setAddresses(resp.data.data);
          const defaultAddr = resp.data.data.find((a) => a.is_default) || resp.data.data[0];
          setSelectedAddressId(defaultAddr.address_id);
        }
      } catch (err) {
        console.error("Failed to load customer addresses:", err);
      }
    };
    loadAddresses();
  }, []);

  // Fetch server summary whenever selected address changes
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoadingSummary(true);
        const resp = await checkoutApi.getSummary(selectedAddressId);
        if (resp.data.success) {
          setSummary(resp.data.data);
          setValidationErrors(resp.data.data.validation_errors || []);
        }
      } catch (err) {
        console.error("Summary fetch error:", err);
      } finally {
        setLoadingSummary(false);
      }
    };

    fetchSummary();
  }, [selectedAddressId]);

  const handleCreateAddress = async (e) => {
    e.preventDefault();
    try {
      const resp = await customerApi.createAddress(newAddr);
      if (resp.data.success) {
        const created = resp.data.data;
        setAddresses([created, ...addresses]);
        setSelectedAddressId(created.address_id);
        setShowNewAddressModal(false);
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Could not save address");
    }
  };

  const handlePlaceOrder = async () => {
    if (!selectedAddressId) {
      alert("Please select or add a delivery address.");
      return;
    }
    if (validationErrors.length > 0) {
      alert("Please resolve validation errors before placing order.");
      return;
    }

    setPlacingOrder(true);
    try {
      // Generate a client-side idempotency key for this order attempt
      const idempotencyKey = `idemp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

      const payload = {
        delivery_address_id: selectedAddressId,
        payment_method: paymentMethod,
        special_instructions: specialInstructions.trim() || null,
        idempotency_key: idempotencyKey,
      };

      const resp = await orderApi.placeOrder(payload);
      if (resp.data.success) {
        // Refresh cart so navbar badge updates to 0
        await fetchCart();
        const order = resp.data.data;
        navigate(`/orders/${order.order_id}/confirmation`, { state: { order } });
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Order creation failed. Please try again.";
      alert(msg);
    } finally {
      setPlacingOrder(false);
    }
  };

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-charcoal-900 mb-4">No items to checkout</h2>
        <p className="text-stone-600 mb-6">Your cart is currently empty. Add dishes to proceed.</p>
        <Link
          to="/menu"
          className="inline-flex px-6 py-3 bg-terracotta-600 text-white font-bold rounded-2xl shadow"
        >
          Browse Menu
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <Link to="/cart" className="inline-flex items-center text-sm text-stone-500 hover:text-terracotta-600 mb-2">
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Cart
        </Link>
        <h1 className="text-3xl font-extrabold text-charcoal-900 tracking-tight">Checkout & Review</h1>
      </div>

      {validationErrors.length > 0 && (
        <div className="mb-8 p-5 bg-red-50 border border-red-200 rounded-3xl text-red-900 text-sm">
          <div className="flex items-center space-x-2 font-bold mb-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span>Please review the following requirements:</span>
          </div>
          <ul className="list-disc list-inside space-y-1">
            {validationErrors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Delivery Address & Payment Method */}
        <div className="lg:col-span-8 space-y-8">
          {/* 1. Delivery Address Card */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-charcoal-900 flex items-center">
                <MapPin className="w-5 h-5 mr-2 text-terracotta-600" />
                1. Delivery Address
              </h2>
              <button
                onClick={() => setShowNewAddressModal(true)}
                className="text-xs font-bold text-terracotta-600 hover:text-terracotta-700 flex items-center"
                id="add-new-address-btn"
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Add New Address
              </button>
            </div>

            {addresses.length === 0 ? (
              <div className="text-center py-6 border border-dashed border-stone-200 rounded-2xl">
                <p className="text-sm text-stone-500 mb-3">No addresses found on file.</p>
                <button
                  onClick={() => setShowNewAddressModal(true)}
                  className="px-4 py-2 bg-stone-900 text-white rounded-xl text-xs font-semibold"
                >
                  Create Address
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {addresses.map((addr) => (
                  <div
                    key={addr.address_id}
                    onClick={() => setSelectedAddressId(addr.address_id)}
                    className={`p-4 rounded-2xl border-2 cursor-pointer transition relative ${
                      selectedAddressId === addr.address_id
                        ? "border-terracotta-600 bg-terracotta-50/20"
                        : "border-stone-200 hover:border-stone-300"
                    }`}
                  >
                    {selectedAddressId === addr.address_id && (
                      <span className="absolute top-3 right-3 w-5 h-5 bg-terracotta-600 text-white rounded-full flex items-center justify-center">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </span>
                    )}
                    <span className="text-xs font-bold uppercase tracking-wider text-stone-400 block mb-1">
                      {addr.address_label}
                    </span>
                    <p className="text-sm font-bold text-charcoal-900">{addr.recipient_name}</p>
                    <p className="text-xs text-stone-600 mt-1 line-clamp-2">
                      {addr.address_line1}, {addr.city} {addr.postal_code}
                    </p>
                    <p className="text-xs text-stone-400 mt-1">{addr.recipient_phone}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 2. Payment Method Card */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70">
            <h2 className="text-lg font-bold text-charcoal-900 mb-6 flex items-center">
              <CreditCard className="w-5 h-5 mr-2 text-terracotta-600" />
              2. Select Payment Option
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* UPI */}
              <div
                onClick={() => setPaymentMethod("UPI")}
                className={`p-4 rounded-2xl border-2 cursor-pointer transition ${
                  paymentMethod === "UPI"
                    ? "border-terracotta-600 bg-terracotta-50/20"
                    : "border-stone-200 hover:border-stone-300"
                }`}
              >
                <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center mb-3">
                  <Smartphone className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm text-charcoal-900">Instant UPI</h4>
                <p className="text-xs text-stone-500 mt-1">GPay, PhonePe, Paytm, BHIM</p>
              </div>

              {/* Card */}
              <div
                onClick={() => setPaymentMethod("CREDIT_CARD")}
                className={`p-4 rounded-2xl border-2 cursor-pointer transition ${
                  paymentMethod === "CREDIT_CARD"
                    ? "border-terracotta-600 bg-terracotta-50/20"
                    : "border-stone-200 hover:border-stone-300"
                }`}
              >
                <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center mb-3">
                  <CreditCard className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm text-charcoal-900">Cards</h4>
                <p className="text-xs text-stone-500 mt-1">Visa, Mastercard, RuPay</p>
              </div>

              {/* COD */}
              <div
                onClick={() => setPaymentMethod("CASH_ON_DELIVERY")}
                className={`p-4 rounded-2xl border-2 cursor-pointer transition ${
                  paymentMethod === "CASH_ON_DELIVERY"
                    ? "border-terracotta-600 bg-terracotta-50/20"
                    : "border-stone-200 hover:border-stone-300"
                }`}
              >
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3">
                  <Banknote className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-sm text-charcoal-900">Cash on Delivery</h4>
                <p className="text-xs text-stone-500 mt-1">Pay in cash or UPI at delivery</p>
              </div>
            </div>

            {/* Special Instructions */}
            <div className="mt-6">
              <label className="block text-xs font-bold uppercase tracking-wider text-stone-500 mb-2">
                Special Delivery Notes (Optional)
              </label>
              <textarea
                value={specialInstructions}
                onChange={(e) => setSpecialInstructions(e.target.value)}
                placeholder="e.g. Leave with security, ring door bell twice..."
                rows={2}
                className="w-full px-4 py-3 bg-stone-50 border border-stone-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-terracotta-500"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Server Summary */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/70 space-y-4">
            <h3 className="text-base font-bold text-charcoal-900 border-b border-stone-100 pb-3">
              Server-Calculated Bill
            </h3>

            {loadingSummary ? (
              <div className="py-8 text-center">
                <div className="w-6 h-6 border-2 border-terracotta-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-xs text-stone-400">Verifying prices with cloud kitchen...</p>
              </div>
            ) : summary ? (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between text-stone-600">
                  <span>Item Subtotal ({summary.item_count} items)</span>
                  <span className="font-semibold text-charcoal-900">
                    ₹{parseFloat(summary.subtotal_amount).toFixed(2)}
                  </span>
                </div>

                {parseFloat(summary.discount_amount) > 0 && (
                  <div className="flex justify-between text-emerald-600 font-medium">
                    <span>Coupon Discount</span>
                    <span>-₹{parseFloat(summary.discount_amount).toFixed(2)}</span>
                  </div>
                )}

                <div className="flex justify-between text-stone-600">
                  <span>Delivery Partner Fee</span>
                  <span className="font-semibold text-charcoal-900">
                    ₹{parseFloat(summary.delivery_fee).toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between text-stone-600">
                  <span>GST & Kitchen Taxes</span>
                  <span className="font-semibold text-charcoal-900">
                    ₹{parseFloat(summary.tax_amount).toFixed(2)}
                  </span>
                </div>

                <div className="border-t border-stone-200 pt-4 flex justify-between items-baseline">
                  <div>
                    <span className="text-base font-bold text-charcoal-900 block">Total Payable</span>
                    <span className="text-xs text-stone-400">All taxes included</span>
                  </div>
                  <span className="text-2xl font-black text-terracotta-700" id="checkout-total-amount">
                    ₹{parseFloat(summary.total_amount).toFixed(2)}
                  </span>
                </div>
              </div>
            ) : null}

            {/* Place Order CTA */}
            <button
              onClick={handlePlaceOrder}
              disabled={placingOrder || !summary?.can_place_order}
              id="confirm-place-order-btn"
              className="w-full mt-6 py-4 px-6 bg-terracotta-600 hover:bg-terracotta-700 disabled:opacity-50 text-white font-bold rounded-2xl shadow-lg shadow-terracotta-600/30 flex items-center justify-center space-x-2 transition transform hover:-translate-y-0.5"
            >
              <span>{placingOrder ? "Placing Order..." : "Place Order"}</span>
              <ArrowRight className="w-5 h-5" />
            </button>

            <div className="pt-2 flex items-center justify-center space-x-2 text-stone-400 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Idempotent Transaction Protection Enabled</span>
            </div>
          </div>
        </div>
      </div>

      {/* New Address Modal */}
      {showNewAddressModal && (
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
                  onClick={() => setShowNewAddressModal(false)}
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
