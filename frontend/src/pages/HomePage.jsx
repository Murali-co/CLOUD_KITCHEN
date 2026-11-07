import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  UtensilsCrossed,
  Sparkles,
  ArrowRight,
  Clock,
  ShieldCheck,
  Star,
  MapPin,
  Flame,
  Search,
  Globe,
  Phone,
  Mail,
  Headphones,
} from "lucide-react";
import { catalogApi } from "../services/api";
import { useCart } from "../context/CartContext";
import { getMenuItemImage, NEUTRAL_FOOD_PLACEHOLDER } from "../utils/menuImages";

export const HomePage = () => {
  const navigate = useNavigate();
  const { addItem } = useCart();
  const [kitchens, setKitchens] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cuisines, setCuisines] = useState([]);
  const [popularItems, setPopularItems] = useState([]);
  const [loadingCuisines, setLoadingCuisines] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [addingId, setAddingId] = useState(null);

  useEffect(() => {
    const loadHomeData = async () => {
      try {
        const [kResp, cResp, mResp, cuResp] = await Promise.all([
          catalogApi.getKitchens(),
          catalogApi.getCategories(),
          catalogApi.getMenu({ page: 1, page_size: 4 }),
          catalogApi.getCuisines(),
        ]);
        if (kResp.data.success) {
          const kItems = kResp.data.data?.items || (Array.isArray(kResp.data.data) ? kResp.data.data : []);
          setKitchens(kItems.slice(0, 3));
        }
        if (cResp.data.success) {
          const cItems = Array.isArray(cResp.data.data) ? cResp.data.data : (cResp.data.data?.items || []);
          setCategories(cItems.slice(0, 6));
        }
        if (cuResp.data.success) {
          const cuItems = Array.isArray(cuResp.data.data) ? cuResp.data.data : (cuResp.data.data?.items || []);
          setCuisines(cuItems);
        }
        if (mResp.data.success) setPopularItems(mResp.data.data?.items || []);
      } catch (err) {
        console.error("Home data load error:", err);
      } finally {
        setLoadingCuisines(false);
      }
    };
    loadHomeData();
  }, []);

  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash === "#contact") {
        setTimeout(() => {
          const el = document.getElementById("contact");
          if (el) {
            el.scrollIntoView({ behavior: "smooth" });
          }
        }, 100);
      }
    };
    handleHash();
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/menu?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleQuickAdd = async (item) => {
    setAddingId(item.menu_item_id);
    try {
      await addItem(item.menu_item_id, 1);
    } catch (err) {
      alert(err.message || "Failed to add to cart");
    } finally {
      setAddingId(null);
    }
  };

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-8 pb-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Content */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-amber-100/80 border border-amber-200/80 text-amber-900 text-xs font-bold tracking-wide">
                <Sparkles className="w-3.5 h-3.5 text-terracotta-600" />
                <span>State-of-the-art Cloud Kitchen Network</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-charcoal-900 tracking-tight leading-[1.1]">
                Chef-Crafted Flavors,{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-terracotta-600 via-amber-600 to-terracotta-500">
                  Delivered Hot & Fresh
                </span>
              </h1>

              <p className="text-base sm:text-lg text-stone-600 max-w-xl mx-auto lg:mx-0 leading-relaxed">
                Experience gourmet bowls, hand-stretched woodfired pizzas, and dum biryanis prepped in dedicated culinary dark kitchens with pure hygiene.
              </p>

              {/* Search Bar */}
              <form onSubmit={handleSearch} className="max-w-lg mx-auto lg:mx-0 flex items-center bg-white p-2 rounded-2xl shadow-lg shadow-stone-200/50 border border-stone-200">
                <Search className="w-5 h-5 text-stone-400 ml-3 mr-2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search gourmet bowls, pizzas, biryani..."
                  className="flex-1 bg-transparent border-none text-sm text-charcoal-900 focus:outline-none"
                />
                <button
                  type="submit"
                  className="px-6 py-3 bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold text-sm rounded-xl shadow transition"
                >
                  Search
                </button>
              </form>

              {/* Badges / Metrics */}
              <div className="pt-4 flex flex-wrap items-center justify-center lg:justify-start gap-6 text-xs text-stone-500 font-medium">
                <span className="flex items-center"><Clock className="w-4 h-4 mr-1.5 text-terracotta-600" /> 30-45 Mins Average Delivery</span>
                <span className="flex items-center"><ShieldCheck className="w-4 h-4 mr-1.5 text-emerald-600" /> 100% Contactless Safe Pack</span>
                <span className="flex items-center"><Star className="w-4 h-4 mr-1.5 text-amber-500 fill-amber-500" /> 4.8+ Customer Rating</span>
              </div>
            </div>

            {/* Right Visual Image */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                <div className="aspect-square rounded-3xl overflow-hidden shadow-2xl border-4 border-white transform rotate-1 hover:rotate-0 transition duration-300">
                  <img
                    src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80"
                    alt="Artisan culinary dish"
                    className="w-full h-full object-cover"
                  />
                </div>
                {/* Floating Kitchen Badge */}
                <div className="absolute -bottom-6 -left-6 bg-white/95 backdrop-blur-md p-4 rounded-2xl shadow-xl border border-stone-200/80 flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-terracotta-50 text-terracotta-600 flex items-center justify-center font-bold">
                    <Flame className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs text-stone-500 font-medium">Fulfilling Now</p>
                    <p className="text-sm font-bold text-charcoal-900">Indiranagar & Koramangala</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Cuisines Showcase Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-terracotta-50 text-terracotta-700 text-xs font-bold tracking-wide mb-2">
              <Globe className="w-3.5 h-3.5" />
              <span>Culinary Traditions</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-charcoal-900 tracking-tight">
              Explore by Cuisine
            </h2>
            <p className="text-xs sm:text-sm text-stone-500 mt-1">
              Journey through 15 authentic regional and global culinary styles crafted in dedicated dark kitchens
            </p>
          </div>
          <Link
            to="/menu"
            className="text-sm font-bold text-terracotta-600 hover:text-terracotta-700 flex items-center shrink-0"
          >
            <span>All Cuisines</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {loadingCuisines ? (
          /* Skeletons */
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
            {[...Array(10)].map((_, i) => (
              <div
                key={i}
                className="bg-stone-100 rounded-3xl h-56 animate-pulse border border-stone-200/50"
              />
            ))}
          </div>
        ) : cuisines.length === 0 ? (
          /* Empty State */
          <div className="bg-white rounded-3xl p-12 text-center border border-stone-200/70">
            <Globe className="w-10 h-10 text-stone-300 mx-auto mb-3" />
            <p className="text-sm font-bold text-stone-600">No cuisines currently available</p>
            <p className="text-xs text-stone-400 mt-1">Check back soon for freshly added culinary styles.</p>
          </div>
        ) : (
          /* Cuisines Grid */
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
            {cuisines.map((cuisine) => (
              <Link
                key={cuisine.cuisine_id}
                to={`/menu?cuisine=${cuisine.cuisine_id}`}
                className="group relative h-60 rounded-3xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1.5 transition-all duration-300 border border-stone-200/80 flex flex-col justify-end bg-stone-900"
                id={`cuisine-card-${cuisine.cuisine_slug}`}
              >
                {/* Background Image */}
                <img
                  src={
                    cuisine.cuisine_image_url ||
                    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80"
                  }
                  alt={cuisine.cuisine_name}
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src =
                      "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80";
                  }}
                  className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out"
                />

                {/* Dark Gradient Overlay for Contrast */}
                <div className="absolute inset-0 bg-gradient-to-t from-stone-950 via-stone-950/50 to-transparent group-hover:via-stone-950/60 transition duration-300" />

                {/* Content */}
                <div className="relative p-4 z-10 space-y-1">
                  <h3 className="font-extrabold text-white text-base sm:text-lg group-hover:text-amber-300 transition duration-200">
                    {cuisine.cuisine_name}
                  </h3>
                  {cuisine.cuisine_description && (
                    <p className="text-stone-300 text-xs line-clamp-2 leading-relaxed opacity-90 group-hover:opacity-100 transition">
                      {cuisine.cuisine_description}
                    </p>
                  )}
                  <div className="pt-2 flex items-center text-[11px] font-bold text-amber-400 group-hover:text-amber-300">
                    <span>Explore Dishes</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Food Categories Horizontal Showcase */}
      {categories.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-black text-charcoal-900 tracking-tight">Food Categories</h2>
              <p className="text-xs text-stone-500">Pick from culinary categories designed for high-speed delivery</p>
            </div>
            <Link to="/menu" className="text-sm font-bold text-terracotta-600 hover:text-terracotta-700 flex items-center">
              <span>View All Menu</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {categories.map((cat) => (
              <Link
                key={cat.category_id}
                to={`/menu?category=${cat.category_id}`}
                className="bg-white p-5 rounded-2xl border border-stone-200/70 hover:border-terracotta-400 hover:shadow-md transition text-center group"
              >
                <div className="w-12 h-12 rounded-xl bg-amber-50 group-hover:bg-terracotta-50 text-terracotta-600 flex items-center justify-center mx-auto mb-3 transition">
                  <UtensilsCrossed className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-charcoal-900 group-hover:text-terracotta-700 transition">
                  {cat.name}
                </h4>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured Cloud Kitchens */}
      {kitchens.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-black text-charcoal-900 tracking-tight">Our Cloud Kitchen Branches</h2>
              <p className="text-xs text-stone-500">Decentralized kitchens with dedicated packing and dispatch centers</p>
            </div>
            <Link to="/kitchens" className="text-sm font-bold text-terracotta-600 hover:text-terracotta-700 flex items-center">
              <span>All Kitchens</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {kitchens.map((k) => (
              <div
                key={k.kitchen_id}
                className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/70 hover:shadow-md transition space-y-4"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-terracotta-700 bg-terracotta-50 px-3 py-1 rounded-full uppercase tracking-wider">
                    {k.branch_code}
                  </span>
                  <span className="text-xs text-emerald-700 bg-emerald-50 font-bold px-2.5 py-0.5 rounded-full flex items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mr-1.5 animate-pulse" />
                    Operational
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-charcoal-900">{k.name}</h3>
                  <p className="text-xs text-stone-500 flex items-center mt-1">
                    <MapPin className="w-3.5 h-3.5 mr-1 text-stone-400" />
                    {k.address_line1}, {k.city} {k.postal_code}
                  </p>
                </div>

                <div className="border-t border-stone-100 pt-4 flex items-center justify-between">
                  <span className="text-xs text-stone-400">Dispatch: 30-40m</span>
                  <Link
                    to={`/kitchens/${k.kitchen_id}`}
                    className="text-xs font-bold text-stone-900 hover:text-terracotta-600 flex items-center"
                  >
                    View Kitchen Menu
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Popular Dishes Preview */}
      {popularItems.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-black text-charcoal-900 tracking-tight">Popular Chef Selections</h2>
              <p className="text-xs text-stone-500">Top-rated items freshly prepped across our cloud kitchens</p>
            </div>
            <Link to="/menu" className="text-sm font-bold text-terracotta-600 hover:text-terracotta-700 flex items-center">
              <span>View Full Menu</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {popularItems.map((dish) => (
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
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
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
                  </div>

                  <div className="p-5">
                    <h4 className="font-bold text-charcoal-900 text-base">{dish.name}</h4>
                    <p className="text-xs text-stone-500 mt-1 line-clamp-2">
                      {dish.description || "Freshly prepped with premium artisan ingredients."}
                    </p>
                  </div>
                </div>

                <div className="p-5 pt-0 flex items-center justify-between">
                  <span className="text-lg font-black text-charcoal-900">
                    ₹{parseFloat(dish.base_price).toFixed(2)}
                  </span>
                  <button
                    onClick={() => handleQuickAdd(dish)}
                    disabled={addingId === dish.menu_item_id || !dish.is_available}
                    className="px-4 py-2 bg-stone-900 hover:bg-stone-800 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-xs transition"
                  >
                    {addingId === dish.menu_item_id ? "Adding..." : "+ Add to Cart"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Contact & Support Section */}
      <section id="contact" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-24">
        <div className="bg-gradient-to-br from-stone-900 via-stone-900 to-stone-950 text-white rounded-3xl p-8 sm:p-12 lg:p-14 border border-stone-800 shadow-2xl relative overflow-hidden">
          {/* Subtle decorative background glow */}
          <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-terracotta-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 -mb-12 -ml-12 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-3xl mb-10">
            <span className="inline-flex items-center text-xs font-bold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-3 py-1 rounded-full uppercase tracking-wider mb-3">
              <Headphones className="w-3.5 h-3.5 mr-1.5" />
              Customer Care & Concierge
            </span>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
              Contact & Support
            </h2>
            <p className="text-stone-300 text-sm sm:text-base mt-2 leading-relaxed">
              Have questions about your order, special catering requests, or need instant assistance? Our dedicated support team is here to assist you.
            </p>
          </div>

          <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Phone Card */}
            <div className="bg-stone-800/80 backdrop-blur-sm p-6 sm:p-8 rounded-2xl border border-stone-700/60 hover:border-terracotta-500/60 transition group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-terracotta-500/10 text-terracotta-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-terracotta-500/20 transition">
                  <Phone className="w-6 h-6" />
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400 mb-1">Direct Phone Hotline</h3>
                <p className="text-sm text-stone-300 mb-3">Reach our support line directly for immediate order updates or inquiries.</p>
              </div>
              <a
                href="tel:7975828623"
                className="text-xl sm:text-2xl font-black text-white hover:text-terracotta-400 transition flex items-center group-hover:translate-x-1"
              >
                <span>7975828623</span>
                <ArrowRight className="w-4 h-4 ml-2 opacity-60 group-hover:opacity-100 transition" />
              </a>
            </div>

            {/* Email Card */}
            <div className="bg-stone-800/80 backdrop-blur-sm p-6 sm:p-8 rounded-2xl border border-stone-700/60 hover:border-terracotta-500/60 transition group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-terracotta-500/10 text-terracotta-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-terracotta-500/20 transition">
                  <Mail className="w-6 h-6" />
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400 mb-1">Support Email</h3>
                <p className="text-sm text-stone-300 mb-3">Send your feedback, order details, or queries for prompt assistance.</p>
              </div>
              <a
                href="mailto:mr1121629@gmail.com"
                className="text-base sm:text-lg font-black text-white hover:text-terracotta-400 transition break-all flex items-center group-hover:translate-x-1"
              >
                <span>mr1121629@gmail.com</span>
                <ArrowRight className="w-4 h-4 ml-2 shrink-0 opacity-60 group-hover:opacity-100 transition" />
              </a>
            </div>

            {/* Address Card */}
            <div className="bg-stone-800/80 backdrop-blur-sm p-6 sm:p-8 rounded-2xl border border-stone-700/60 hover:border-terracotta-500/60 transition group flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-terracotta-500/10 text-terracotta-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-terracotta-500/20 transition">
                  <MapPin className="w-6 h-6" />
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400 mb-1">Campus Hub & Operations</h3>
                <p className="text-sm text-stone-300 mb-3">Central coordination hub for campus operations and deliveries.</p>
              </div>
              <div className="text-base sm:text-lg font-bold text-white">
                PES University, Room No. 509
              </div>
            </div>
          </div>

          {/* Email Support CTA Button */}
          <div className="relative z-10 mt-10 pt-8 border-t border-stone-800/80 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-3 text-stone-400 text-xs sm:text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Dedicated support ready to assist you</span>
            </div>
            <a
              href="mailto:mr1121629@gmail.com?subject=GourmetCloud%20Customer%20Support%20Inquiry"
              className="w-full sm:w-auto px-7 py-3.5 bg-terracotta-600 hover:bg-terracotta-500 text-white font-bold text-sm rounded-xl transition shadow-lg shadow-terracotta-600/30 flex items-center justify-center space-x-2"
              id="contact-support-email-btn"
            >
              <Mail className="w-4 h-4" />
              <span>Contact Support via Email</span>
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};
