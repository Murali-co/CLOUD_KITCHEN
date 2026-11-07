import React from "react";
import { Link } from "react-router-dom";
import { UtensilsCrossed, ShieldCheck, Clock, Award, Phone, Mail, MapPin } from "lucide-react";

export const Footer = () => {
  return (
    <footer className="bg-stone-900 text-stone-300 mt-24 border-t border-stone-800">
      {/* Feature Highlights Bar */}
      <div className="border-b border-stone-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-2xl bg-stone-800 flex items-center justify-center text-terracotta-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-white font-semibold">Lightning Delivery</h4>
              <p className="text-sm text-stone-400">Fresh from the kitchen in 30–45 mins</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-2xl bg-stone-800 flex items-center justify-center text-terracotta-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-white font-semibold">100% Certified Hygiene</h4>
              <p className="text-sm text-stone-400">Strict HACCP-compliant food safety</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-2xl bg-stone-800 flex items-center justify-center text-terracotta-400">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-white font-semibold">Chef Curated Recipes</h4>
              <p className="text-sm text-stone-400">Artisan ingredients & authentic flavors</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer Links */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 grid grid-cols-1 md:grid-cols-4 gap-10">
        <div>
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-9 h-9 rounded-xl bg-terracotta-600 flex items-center justify-center text-white">
              <UtensilsCrossed className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">
              Gourmet<span className="text-terracotta-500">Cloud</span>
            </span>
          </div>
          <p className="text-sm text-stone-400 leading-relaxed mb-4">
            Next-generation decentralized cloud kitchen network providing freshly prepped gourmet meals across metropolitan hubs.
          </p>
        </div>

        <div>
          <h5 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">Explore</h5>
          <ul className="space-y-2.5 text-sm">
            <li><Link to="/kitchens" className="hover:text-terracotta-400 transition">Our Cloud Kitchens</Link></li>
            <li><Link to="/menu" className="hover:text-terracotta-400 transition">Full Artisan Menu</Link></li>
            <li><Link to="/cart" className="hover:text-terracotta-400 transition">View Cart</Link></li>
            <li><Link to="/orders" className="hover:text-terracotta-400 transition">Track Your Order</Link></li>
          </ul>
        </div>

        <div>
          <h5 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">Cuisines</h5>
          <ul className="space-y-2.5 text-sm text-stone-400">
            <li>Gourmet Rice Bowls & Curries</li>
            <li>Neapolitan Woodfired Pizzas</li>
            <li>Hyderabadi Dum Biryanis</li>
            <li>Artisan Pasta & Desserts</li>
          </ul>
        </div>

        <div>
          <h5 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">Contact & Support</h5>
          <div className="space-y-3 text-sm text-stone-400">
            <p className="flex items-center">
              <Phone className="w-4 h-4 mr-2.5 text-terracotta-400 shrink-0" />
              <a href="tel:7975828623" className="hover:text-white transition">
                7975828623
              </a>
            </p>
            <p className="flex items-center">
              <Mail className="w-4 h-4 mr-2.5 text-terracotta-400 shrink-0" />
              <a href="mailto:mr1121629@gmail.com" className="hover:text-white transition break-all">
                mr1121629@gmail.com
              </a>
            </p>
            <p className="flex items-start">
              <MapPin className="w-4 h-4 mr-2.5 text-terracotta-400 mt-1 shrink-0" />
              <span>PES University, Room No. 509</span>
            </p>
            <div className="pt-2">
              <a
                href="mailto:mr1121629@gmail.com?subject=GourmetCloud%20Customer%20Support"
                className="inline-flex items-center px-3.5 py-2 bg-terracotta-600 hover:bg-terracotta-500 text-white text-xs font-bold rounded-xl transition shadow-xs"
              >
                <Mail className="w-3.5 h-3.5 mr-1.5" />
                Contact Support via Email
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-stone-800/80 py-6 text-center text-xs text-stone-500">
        <p>© 2026 GourmetCloud Management System. DBMS Mini-Project (Phases 0–7). All rights reserved.</p>
      </div>
    </footer>
  );
};
