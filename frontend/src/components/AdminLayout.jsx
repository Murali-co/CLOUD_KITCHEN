import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, 
  Users, 
  Building2, 
  UserCheck, 
  UtensilsCrossed, 
  ShoppingBag, 
  CreditCard, 
  Tag, 
  BarChart3, 
  ShieldAlert, 
  Menu as MenuIcon, 
  X,
  ShieldCheck,
  ChevronRight,
  LogOut,
  ExternalLink
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const AdminLayout = ({ children, title, subtitle, actions }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navLinks = [
    { label: "Overview", path: "/admin/dashboard", icon: LayoutDashboard },
    { label: "User Management", path: "/admin/users", icon: Users },
    { label: "Kitchen Facilities", path: "/admin/kitchens", icon: Building2 },
    { label: "Staff Roster", path: "/admin/staff", icon: UserCheck },
    { label: "Menu & Categories", path: "/admin/menu", icon: UtensilsCrossed },
    { label: "Order Administration", path: "/admin/orders", icon: ShoppingBag },
    { label: "Payment Monitoring", path: "/admin/payments", icon: CreditCard },
    { label: "Coupons & Discounts", path: "/admin/coupons", icon: Tag },
    { label: "Platform Analytics", path: "/admin/analytics", icon: BarChart3 },
    { label: "Audit Security Logs", path: "/admin/audit-logs", icon: ShieldAlert },
  ];

  return (
    <div className="min-h-screen bg-stone-100 flex flex-col md:flex-row">
      {/* Mobile Top Bar */}
      <div className="md:hidden bg-charcoal-950 text-white px-4 py-3 flex items-center justify-between sticky top-20 z-40 shadow">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-600 to-amber-500 flex items-center justify-center font-bold text-white">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <span className="font-bold text-sm tracking-wide">Admin Control Panel</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-1.5 rounded-lg text-stone-300 hover:bg-stone-800"
        >
          {sidebarOpen ? <X className="w-5 h-5" /> : <MenuIcon className="w-5 h-5" />}
        </button>
      </div>

      {/* Admin Sidebar */}
      <aside
        className={`fixed md:sticky top-0 md:top-20 z-40 md:z-30 h-screen md:h-[calc(100vh-5rem)] w-64 bg-charcoal-950 text-stone-300 flex flex-col transition-transform duration-200 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        } shadow-2xl md:shadow-none border-r border-stone-800`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-stone-800 hidden md:flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-amber-500 flex items-center justify-center text-white shadow-md font-bold">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-sm font-black text-white tracking-wider uppercase block">
              Admin Portal
            </span>
            <span className="text-[10px] text-purple-400 font-bold block">
              Platform Headquarters
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navLinks.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-bold transition ${
                  active
                    ? "bg-purple-600/90 text-white shadow-sm shadow-purple-900/50"
                    : "text-stone-400 hover:text-white hover:bg-stone-800/60"
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${active ? "text-white" : "text-stone-400"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer - Current Admin User */}
        <div className="p-3 border-t border-stone-800 bg-charcoal-900/50">
          <div className="flex items-center space-x-2.5 px-2 py-1.5">
            <div className="w-7 h-7 rounded-lg bg-purple-900/60 text-purple-300 border border-purple-700/50 flex items-center justify-center font-bold text-xs">
              {user?.first_name?.[0] || "A"}
            </div>
            <div className="overflow-hidden flex-1">
              <p className="text-xs font-bold text-white truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <span className="text-[10px] font-black text-amber-400 uppercase tracking-wider block">
                ADMINISTRATOR
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0">
        {/* Title Bar */}
        {(title || subtitle || actions) && (
          <div className="bg-white border-b border-stone-200 px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div>
              {title && <h1 className="text-xl font-black text-charcoal-900">{title}</h1>}
              {subtitle && <p className="text-xs text-stone-500 mt-0.5">{subtitle}</p>}
            </div>
            {actions && <div className="flex items-center space-x-2">{actions}</div>}
          </div>
        )}

        {/* Content Body */}
        <main className="p-4 sm:p-6 max-w-7xl mx-auto space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
};
