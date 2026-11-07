import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { MapPin, Phone, Mail, ArrowRight, Utensils, CheckCircle } from "lucide-react";
import { catalogApi } from "../services/api";

export const KitchensPage = () => {
  const [kitchens, setKitchens] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchKitchens = async () => {
      try {
        setLoading(true);
        const resp = await catalogApi.getKitchens();
        if (resp.data.success) {
          const items = resp.data.data?.items || (Array.isArray(resp.data.data) ? resp.data.data : []);
          setKitchens(items);
        }
      } catch (err) {
        console.error("Kitchens load error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchKitchens();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-10 text-center max-w-2xl mx-auto">
        <h1 className="text-3xl sm:text-4xl font-black text-charcoal-900 tracking-tight">
          Cloud Kitchen Hubs
        </h1>
        <p className="text-sm text-stone-500 mt-2">
          State-of-the-art culinary production hubs strategically positioned across metropolitan hubs for rapid order dispatch.
        </p>
      </div>

      {loading ? (
        <div className="py-24 text-center">
          <div className="w-10 h-10 border-4 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm text-stone-500">Locating cloud kitchen branches...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {kitchens.map((k) => (
            <div
              key={k.kitchen_id}
              className="bg-white rounded-3xl p-8 shadow-sm border border-stone-200/70 hover:shadow-xl hover:border-terracotta-200 transition duration-300 flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-terracotta-700 bg-terracotta-50 px-3 py-1 rounded-full uppercase tracking-wider font-mono">
                    {k.branch_code}
                  </span>
                  <span className="text-xs text-emerald-700 bg-emerald-50 font-bold px-2.5 py-0.5 rounded-full flex items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mr-1.5 animate-pulse" />
                    Accepting Orders
                  </span>
                </div>

                <div>
                  <h3 className="text-xl font-bold text-charcoal-900">{k.name}</h3>
                  <p className="text-xs text-stone-500 mt-1 flex items-start">
                    <MapPin className="w-4 h-4 text-stone-400 mr-1.5 flex-shrink-0 mt-0.5" />
                    {k.address_line1}, {k.city}, {k.state} {k.postal_code}
                  </p>
                </div>

                <div className="text-xs text-stone-500 space-y-1 pt-2 border-t border-stone-100">
                  <p className="flex items-center">
                    <Phone className="w-3.5 h-3.5 mr-2 text-stone-400" />
                    {k.contact_phone}
                  </p>
                  <p className="flex items-center">
                    <Mail className="w-3.5 h-3.5 mr-2 text-stone-400" />
                    {k.email}
                  </p>
                </div>
              </div>

              <div className="pt-6 mt-6 border-t border-stone-100 flex items-center justify-between">
                <span className="text-xs text-stone-400">Prep Speed: 15–20 mins</span>
                <Link
                  to={`/kitchens/${k.kitchen_id}`}
                  className="px-4 py-2 bg-stone-900 hover:bg-stone-800 text-white font-bold rounded-xl text-xs transition flex items-center space-x-1"
                >
                  <span>Explore Menu</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
