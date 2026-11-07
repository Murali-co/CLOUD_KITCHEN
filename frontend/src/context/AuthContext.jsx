import React, { createContext, useContext, useState, useEffect } from "react";
import { authApi, customerApi, kitchenApi, deliveryApi } from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [customer, setCustomer] = useState(null);
  const [staff, setStaff] = useState(null);
  const [deliveryPerson, setDeliveryPerson] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("auth_token") || null);
  const [loading, setLoading] = useState(true);

  // Load current user profile on initial render
  useEffect(() => {
    const fetchProfile = async () => {
      if (token) {
        try {
          const meResp = await authApi.getMe();
          if (meResp.data?.success) {
            const u = meResp.data.data;
            setUser(u);

            if (u.role === "KITCHEN_STAFF" || u.role === "KITCHEN_MANAGER") {
              try {
                const staffResp = await kitchenApi.getMyProfile();
                if (staffResp.data?.success) {
                  setStaff(staffResp.data.data);
                }
              } catch (e) {
                console.warn("Could not fetch staff details", e);
              }
            } else if (u.role === "DELIVERY_PERSON") {
              try {
                const delResp = await deliveryApi.getProfile();
                if (delResp.data?.success) {
                  setDeliveryPerson(delResp.data.data);
                }
              } catch (e) {
                console.warn("Could not fetch delivery profile", e);
              }
            } else if (u.role === "CUSTOMER") {
              try {
                const custResp = await customerApi.getProfile();
                if (custResp.data?.success) {
                  setCustomer(custResp.data.data?.customer || custResp.data.data);
                }
              } catch (e) {
                // Not a customer or customer record not initialized
              }
            }
          }
        } catch (err) {
          console.warn("Failed to fetch initial profile, clearing stale token");
          logout();
        }
      }
      setLoading(false);
    };

    fetchProfile();
  }, [token]);

  const login = async (email, password) => {
    const resp = await authApi.login({ email, password });
    if (resp.data.success) {
      const { access_token, user: userData } = resp.data.data;
      localStorage.setItem("auth_token", access_token);
      setToken(access_token);
      setUser(userData);

      if (userData.role === "KITCHEN_STAFF" || userData.role === "KITCHEN_MANAGER") {
        try {
          const staffResp = await kitchenApi.getMyProfile();
          if (staffResp.data?.success) {
            setStaff(staffResp.data.data);
          }
        } catch (e) {
          console.warn("Could not load staff profile upon login", e);
        }
      } else if (userData.role === "DELIVERY_PERSON") {
        try {
          const delResp = await deliveryApi.getProfile();
          if (delResp.data?.success) {
            setDeliveryPerson(delResp.data.data);
          }
        } catch (e) {
          console.warn("Could not load delivery profile upon login", e);
        }
      } else if (userData.role === "CUSTOMER") {
        try {
          const custResp = await customerApi.getProfile();
          if (custResp.data?.success) {
            setCustomer(custResp.data.data?.customer || custResp.data.data);
          }
        } catch (e) {
          // customer profile fallback
        }
      }
      return userData;
    }
  };

  const register = async (formData) => {
    const resp = await authApi.register(formData);
    return resp.data;
  };

  const logout = async () => {
    try {
      if (token) {
        await authApi.logout();
      }
    } catch (e) {
      // ignore network errors on logout
    } finally {
      localStorage.removeItem("auth_token");
      setToken(null);
      setUser(null);
      setCustomer(null);
      setStaff(null);
      setDeliveryPerson(null);
    }
  };

  const isStaff = user?.role === "KITCHEN_STAFF" || user?.role === "KITCHEN_MANAGER";
  const isManager = user?.role === "KITCHEN_MANAGER";
  const isDelivery = user?.role === "DELIVERY_PERSON";
  const isAdmin = user?.role === "ADMIN";

  return (
    <AuthContext.Provider
      value={{
        user,
        customer,
        staff,
        deliveryPerson,
        token,
        isAuthenticated: !!token,
        isStaff,
        isManager,
        isDelivery,
        isAdmin,
        loading,
        login,
        register,
        logout,
        setCustomer,
        setStaff,
        setDeliveryPerson,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
