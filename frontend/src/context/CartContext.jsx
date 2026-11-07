import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { cartApi } from "../services/api";
import { useAuth } from "./AuthContext";

const CartContext = createContext(null);

export const CartProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const resp = await cartApi.getCart();
      if (resp.data.success) {
        setCart(resp.data.data);
      }
    } catch (err) {
      console.error("Cart fetch error:", err);
      // Cart might be empty or Redis temporarily unavailable
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addItem = async (menuItemId, quantity = 1, notes = null) => {
    if (!isAuthenticated) {
      throw new Error("Please log in to add items to your cart");
    }
    setError(null);
    try {
      const resp = await cartApi.addItem({
        menu_item_id: menuItemId,
        quantity,
        customization_notes: notes,
      });
      if (resp.data.success) {
        setCart(resp.data.data);
        return resp.data.data;
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Could not add item to cart";
      setError(msg);
      throw new Error(msg);
    }
  };

  const updateQuantity = async (menuItemId, newQuantity) => {
    if (newQuantity <= 0) {
      return removeItem(menuItemId);
    }
    setError(null);
    try {
      const resp = await cartApi.updateItemQuantity(menuItemId, newQuantity);
      if (resp.data.success) {
        setCart(resp.data.data);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Could not update item quantity";
      setError(msg);
      throw new Error(msg);
    }
  };

  const removeItem = async (menuItemId) => {
    setError(null);
    try {
      const resp = await cartApi.removeItem(menuItemId);
      if (resp.data.success) {
        setCart(resp.data.data);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Could not remove item";
      setError(msg);
      throw new Error(msg);
    }
  };

  const clearCart = async () => {
    setError(null);
    try {
      await cartApi.clearCart();
      setCart({
        items: [],
        subtotal_amount: "0.00",
        discount_amount: "0.00",
        delivery_fee: "0.00",
        tax_amount: "0.00",
        total_amount: "0.00",
        applied_coupon_code: null,
      });
    } catch (err) {
      console.error("Clear cart error:", err);
    }
  };

  const applyCoupon = async (couponCode) => {
    setError(null);
    try {
      const resp = await cartApi.applyCoupon(couponCode);
      if (resp.data.success) {
        setCart(resp.data.data);
        return resp.data.data;
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Invalid or ineligible coupon code";
      setError(msg);
      throw new Error(msg);
    }
  };

  const removeCoupon = async () => {
    setError(null);
    try {
      const resp = await cartApi.removeCoupon();
      if (resp.data.success) {
        setCart(resp.data.data);
      }
    } catch (err) {
      console.error("Remove coupon error:", err);
    }
  };

  const itemCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;

  return (
    <CartContext.Provider
      value={{
        cart,
        itemCount,
        loading,
        error,
        fetchCart,
        addItem,
        updateQuantity,
        removeItem,
        clearCart,
        applyCoupon,
        removeCoupon,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);
