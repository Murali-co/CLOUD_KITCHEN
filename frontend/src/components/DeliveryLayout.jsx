import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  Bike, 
  Package, 
  History, 
  Power, 
  MapPin, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  Phone,
  ShieldCheck,
  ChevronRight
} from "lucide-react";
import { deliveryApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

export const DeliveryLayout = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchProfile = async () => {
    try {
      const resp = await deliveryApi.getProfile();
      if (resp.data.success) {
        setProfile(resp.data.data);
      }
    } catch (err) {
      console.error("Failed to load delivery profile:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleToggleAvailability = async () => {
    if (!profile) return;
    setToggling(true);
    setErrorMsg("");
    try {
      const newStatus = profile.current_status === "AVAILABLE" ? "OFFLINE" : "AVAILABLE";
      const resp = await deliveryApi.updateAvailability({ current_status: newStatus });
      if (resp.data.success) {
        setProfile(resp.data.data);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to update availability");
    } finally {
      setToggling(false);
    }
  };

  const navItems = [
    { label: "Dashboard", path: "/delivery/dashboard", icon: Bike },
    { label: "Assignments", path: "/delivery/assignments", icon: Package },
    { label: "Delivery History", path: "/delivery/history", icon: History },
  ];

  return (
    <div className="min-h-screen bg-stone-100 pb-20 md:pb-10">
      {/* Mobile-First Header */}
      <header className="bg-charcoal-900 text-white sticky top-20 z-40 shadow-md">
        <div className="max-w-4xl mx-auto px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-terracotta-500 flex items-center justify-center text-white shadow-sm font-bold">
                <Bike className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-base sm:text-lg font-bold leading-tight flex items-center gap-2">
                  <span>{profile ? `${profile.first_name} ${profile.last_name}` : user?.first_name || "Courier"}</span>
                  {profile && (
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-stone-800 text-amber-300 border border-amber-400/20">
                      {profile.vehicle_type} • {profile.vehicle_number}
                    </span>
                  )}
                </h1>
                <p className="text-xs text-stone-400">
                  Rating: <span className="text-amber-400 font-semibold">{profile?.rating ? Number(profile.rating).toFixed(1) : "5.0"} ★</span> • Orders: <span className="text-stone-200 font-medium">{profile?.total_deliveries_completed || 0}</span>
                </p>
              </div>
            </div>

            {/* Availability Toggle */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleToggleAvailability}
                disabled={toggling || profile?.current_status === "ON_DELIVERY"}
                id="delivery-availability-toggle"
                className={`flex items-center space-x-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-xl text-xs sm:text-sm font-bold transition-all shadow-sm ${
                  profile?.current_status === "AVAILABLE"
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-900/30"
                    : profile?.current_status === "ON_DELIVERY"
                    ? "bg-amber-600 text-white cursor-not-allowed"
                    : "bg-stone-700 hover:bg-stone-600 text-stone-300"
                }`}
                title={profile?.current_status === "ON_DELIVERY" ? "Active order in progress" : "Toggle Availability"}
              >
                <span className={`w-2 h-2 rounded-full ${profile?.current_status === "AVAILABLE" ? "bg-white animate-ping" : profile?.current_status === "ON_DELIVERY" ? "bg-amber-300" : "bg-stone-400"}`}></span>
                <span>
                  {toggling
                    ? "Updating..."
                    : profile?.current_status === "AVAILABLE"
                    ? "ONLINE"
                    : profile?.current_status === "ON_DELIVERY"
                    ? "DELIVERING"
                    : "OFFLINE"}
                </span>
                <Power className="w-3.5 h-3.5 ml-1 opacity-80" />
              </button>
            </div>
          </div>

          {errorMsg && (
            <div className="mt-2 text-xs bg-red-950/70 border border-red-800 text-red-200 px-3 py-1.5 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        {/* Desktop Tab Navigation */}
        <div className="hidden md:block border-t border-stone-800 bg-charcoal-950/60">
          <div className="max-w-4xl mx-auto px-4 flex space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
                    active
                      ? "text-amber-400 border-amber-400 bg-white/5"
                      : "text-stone-400 border-transparent hover:text-stone-200"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-4xl mx-auto px-4 py-5 sm:py-6">
        {children}
      </main>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-stone-200 shadow-xl z-50 flex items-center justify-around py-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center py-1 px-3 text-[11px] font-semibold transition ${
                active ? "text-terracotta-600" : "text-stone-500 hover:text-stone-800"
              }`}
            >
              <Icon className={`w-5 h-5 mb-0.5 ${active ? "stroke-[2.5]" : ""}`} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
};
