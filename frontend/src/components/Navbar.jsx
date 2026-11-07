import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { ShoppingBag, User, LogOut, UtensilsCrossed, Menu as MenuIcon, X, MapPin, ChefHat, Bike, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

export const Navbar = () => {
  const { user, isAuthenticated, isStaff, isDelivery, isAdmin, staff, logout } = useAuth();
  const { itemCount } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    setUserDropdownOpen(false);
    navigate("/login");
  };

  const navLinks = [
    { name: "Home", path: "/" },
    { name: "Cloud Kitchens", path: "/kitchens" },
    { name: "Explore Menu", path: "/menu" },
    { name: "Contact & Support", path: "/#contact" },
    ...(isAuthenticated ? [{ name: "My Orders", path: "/orders" }] : []),
    ...(isStaff ? [{ name: "Kitchen Hub", path: "/kitchen/dashboard", highlight: true }] : []),
    ...(isDelivery ? [{ name: "Delivery Portal", path: "/delivery/dashboard", highlight: true }] : []),
    ...(isAdmin ? [{ name: "Admin Portal", path: "/admin/dashboard", highlight: true }] : []),
  ];

  const isActive = (path) => {
    if (path === "/" && (location.pathname !== "/" || location.hash)) return false;
    if (path === "/#contact") return location.hash === "#contact";
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-50 glass-nav border-b border-stone-200/70 transition-all duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-terracotta-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-terracotta-500/20 group-hover:scale-105 transition-transform">
              <UtensilsCrossed className="w-6 h-6" />
            </div>
            <div>
              <span className="text-2xl font-bold tracking-tight text-charcoal-900 flex items-center">
                Gourmet<span className="text-terracotta-600">Cloud</span>
              </span>
              <span className="text-[11px] block text-stone-500 font-medium -mt-1 tracking-wider uppercase">
                Artisan Kitchen Network
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`text-sm font-semibold transition-colors py-1 border-b-2 ${
                  isActive(link.path)
                    ? "text-terracotta-600 border-terracotta-600"
                    : "text-stone-700 hover:text-terracotta-600 border-transparent"
                }`}
              >
                {link.name}
              </Link>
            ))}
          </nav>

          {/* Right Action Icons & Controls */}
          <div className="flex items-center space-x-4">
            {/* Cart Link with Badge */}
            <Link
              to="/cart"
              id="navbar-cart-button"
              className="relative p-2.5 rounded-full text-stone-700 hover:text-terracotta-600 hover:bg-stone-100 transition-colors"
              title="Shopping Cart"
            >
              <ShoppingBag className="w-6 h-6" />
              {itemCount > 0 && (
                <span
                  id="cart-badge-count"
                  className="absolute -top-1 -right-1 bg-terracotta-600 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center shadow-sm animate-pulse"
                >
                  {itemCount}
                </span>
              )}
            </Link>

            {/* Auth Dropdown / Buttons */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center space-x-2 p-1.5 rounded-full hover:bg-stone-100 border border-stone-200/80 transition"
                  id="user-profile-menu-button"
                >
                  <div className="w-8 h-8 rounded-full bg-amber-100 text-terracotta-700 flex items-center justify-center font-bold text-sm">
                    {user?.first_name?.[0] || "U"}
                  </div>
                  <span className="hidden sm:inline text-sm font-medium text-stone-800 pr-2">
                    {user?.first_name || "Account"}
                  </span>
                </button>

                {/* Dropdown Menu */}
                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-stone-200/80 py-2 z-50 animate-in fade-in slide-in-from-top-2">
                    <div className="px-4 py-2 border-b border-stone-100">
                      <p className="text-sm font-semibold text-charcoal-900">
                        {user?.first_name} {user?.last_name}
                      </p>
                      <p className="text-xs text-stone-500 truncate">{user?.email}</p>
                    </div>
                    {isStaff && (
                      <Link
                        to="/kitchen/dashboard"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center px-4 py-2.5 text-sm font-semibold text-terracotta-700 bg-amber-50/70 hover:bg-amber-100/70 border-b border-amber-100/80"
                      >
                        <ChefHat className="w-4 h-4 mr-3 text-terracotta-600" />
                        Kitchen Operations
                      </Link>
                    )}
                    {isDelivery && (
                      <Link
                        to="/delivery/dashboard"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center px-4 py-2.5 text-sm font-semibold text-blue-700 bg-blue-50/70 hover:bg-blue-100/70 border-b border-blue-100/80"
                      >
                        <Bike className="w-4 h-4 mr-3 text-blue-600" />
                        Delivery Portal
                      </Link>
                    )}
                    {isAdmin && (
                      <Link
                        to="/admin/dashboard"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center px-4 py-2.5 text-sm font-semibold text-purple-700 bg-purple-50/70 hover:bg-purple-100/70 border-b border-purple-100/80"
                      >
                        <ShieldCheck className="w-4 h-4 mr-3 text-purple-600" />
                        Admin Control Panel
                      </Link>
                    )}
                    <Link
                      to="/profile"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center px-4 py-2.5 text-sm text-stone-700 hover:bg-stone-50 hover:text-terracotta-600"
                    >
                      <User className="w-4 h-4 mr-3 text-stone-400" />
                      Profile & Saved Addresses
                    </Link>
                    <Link
                      to="/orders"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center px-4 py-2.5 text-sm text-stone-700 hover:bg-stone-50 hover:text-terracotta-600"
                    >
                      <ShoppingBag className="w-4 h-4 mr-3 text-stone-400" />
                      Order History
                    </Link>
                    <div className="border-t border-stone-100 my-1"></div>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 text-left"
                    >
                      <LogOut className="w-4 h-4 mr-3 text-red-400" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="hidden sm:flex items-center space-x-3">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-semibold text-stone-700 hover:text-terracotta-600 transition"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-semibold text-white bg-terracotta-600 hover:bg-terracotta-700 rounded-xl shadow-sm shadow-terracotta-600/30 transition transform hover:-translate-y-0.5"
                >
                  Create Account
                </Link>
              </div>
            )}

            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-stone-700 hover:bg-stone-100"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <MenuIcon className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-stone-200/70 space-y-3">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2 rounded-xl text-base font-semibold ${
                  isActive(link.path)
                    ? "bg-terracotta-50 text-terracotta-600"
                    : "text-stone-700 hover:bg-stone-100"
                }`}
              >
                {link.name}
              </Link>
            ))}
            {!isAuthenticated && (
              <div className="pt-2 border-t border-stone-200/50 flex flex-col space-y-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 text-sm font-semibold text-stone-800 bg-stone-100 rounded-xl"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 text-sm font-semibold text-white bg-terracotta-600 rounded-xl"
                >
                  Create Account
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
