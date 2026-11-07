import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { 
  Package, 
  MapPin, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  Search, 
  ArrowRight,
  Filter,
  RefreshCw,
  Phone
} from "lucide-react";
import { DeliveryLayout } from "../components/DeliveryLayout";
import { deliveryApi } from "../services/api";

export const DeliveryAssignmentsPage = () => {
  const [activeTab, setActiveTab] = useState("all"); // 'all', 'active', 'completed'
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const fetchAssignments = async () => {
    setLoading(true);
    try {
      const params = {};
      if (activeTab === "active") params.is_active = true;
      if (activeTab === "completed") params.status = "DELIVERED";
      const resp = await deliveryApi.getAssignments(params);
      if (resp.data.success) {
        setAssignments(resp.data.data.items || []);
      }
    } catch (err) {
      console.error("Failed to load assignments:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, [activeTab]);

  const filtered = assignments.filter((a) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      a.order_number.toLowerCase().includes(s) ||
      a.customer_name.toLowerCase().includes(s) ||
      a.kitchen_name.toLowerCase().includes(s)
    );
  });

  return (
    <DeliveryLayout>
      <div className="space-y-5">
        {/* Header & Search */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-charcoal-900">Delivery Assignments</h1>
            <p className="text-xs text-stone-500">Track and manage your courier dispatches</p>
          </div>

          <div className="relative">
            <Search className="w-4 h-4 text-stone-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by order or customer..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full sm:w-64 pl-9 pr-3 py-1.5 text-xs bg-white border border-stone-200 rounded-xl focus:outline-none focus:border-terracotta-500"
            />
          </div>
        </div>

        {/* Tab Filters */}
        <div className="flex border-b border-stone-200 space-x-2">
          {[
            { id: "all", label: "All Tasks" },
            { id: "active", label: "Active" },
            { id: "completed", label: "Completed" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition ${
                activeTab === tab.id
                  ? "text-terracotta-600 border-terracotta-600"
                  : "text-stone-500 border-transparent hover:text-stone-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Assignments List */}
        {loading ? (
          <div className="py-12 text-center text-stone-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-terracotta-500" />
            <span className="text-xs">Loading delivery assignments...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-2xl p-10 text-center border border-dashed border-stone-300">
            <Package className="w-8 h-8 mx-auto text-stone-400 mb-2" />
            <h3 className="text-sm font-bold text-charcoal-900">No Assignments Found</h3>
            <p className="text-xs text-stone-500 mt-1">There are no assignments matching this filter.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((del) => {
              const isDelivered = del.delivery_status === "DELIVERED";
              const isOut = del.delivery_status === "OUT_FOR_DELIVERY";
              const isPicked = del.delivery_status === "PICKED_UP";

              return (
                <Link
                  key={del.delivery_id}
                  to={`/delivery/assignments/${del.delivery_id}`}
                  className="block bg-white rounded-2xl p-4 border border-stone-200/80 shadow-sm hover:shadow-md transition group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-charcoal-900 group-hover:text-terracotta-600 transition">
                          Order #{del.order_number}
                        </span>
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                            isDelivered
                              ? "bg-emerald-100 text-emerald-800"
                              : isOut
                              ? "bg-purple-100 text-purple-800"
                              : isPicked
                              ? "bg-blue-100 text-blue-800"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {del.delivery_status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <span className="text-[11px] text-stone-400 mt-0.5 block">
                        Assigned: {new Date(del.assigned_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        {del.delivered_at && ` • Delivered: ${new Date(del.delivered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-sm font-black text-charcoal-900 block">
                        ₹{Number(del.total_amount).toFixed(2)}
                      </span>
                      <span className="text-[11px] text-stone-400">{del.item_count} items</span>
                    </div>
                  </div>

                  {/* Route Summary */}
                  <div className="mt-3 pt-3 border-t border-stone-100 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-stone-600">
                    <div className="flex items-center space-x-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-terracotta-500 shrink-0"></span>
                      <span className="truncate">From: <strong>{del.kitchen_name}</strong></span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
                      <span className="truncate">To: <strong>{del.customer_name}</strong> ({del.delivery_address?.split(',')[0]})</span>
                    </div>
                  </div>

                  <div className="mt-2 text-right">
                    <span className="text-[11px] font-bold text-terracotta-600 group-hover:underline inline-flex items-center">
                      <span>View Assignment Details</span>
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </DeliveryLayout>
  );
};
