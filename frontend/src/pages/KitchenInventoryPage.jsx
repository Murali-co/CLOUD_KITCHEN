import React, { useState, useEffect } from "react";
import {
  Package,
  Plus,
  ArrowDownRight,
  ArrowUpRight,
  AlertTriangle,
  Search,
  Filter,
  CheckCircle,
  Clock,
  FileText,
  RotateCcw,
  Edit2,
  Trash2,
  RefreshCw,
  Layers,
  TrendingDown,
  Building2,
} from "lucide-react";
import { KitchenLayout } from "../components/KitchenLayout";
import { inventoryApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

export const KitchenInventoryPage = () => {
  const { isManager } = useAuth();
  const [activeTab, setActiveTab] = useState("stock"); // "stock" | "movements" | "ingredients"

  // Inventory Stock State
  const [inventory, setInventory] = useState([]);
  const [lowStockAlerts, setLowStockAlerts] = useState([]);
  const [stockLoading, setStockLoading] = useState(true);
  const [lowStockFilter, setLowStockFilter] = useState(false);
  const [searchStock, setSearchStock] = useState("");

  // Movements Audit Log State
  const [movements, setMovements] = useState([]);
  const [movementTotal, setMovementTotal] = useState(0);
  const [movementPage, setMovementPage] = useState(1);
  const [movementFilterType, setMovementFilterType] = useState("");
  const [movementLoading, setMovementLoading] = useState(false);

  // Master Ingredients State
  const [ingredients, setIngredients] = useState([]);
  const [ingredientsLoading, setIngredientsLoading] = useState(false);

  // Stock In Modal State
  const [showStockInModal, setShowStockInModal] = useState(false);
  const [stockInForm, setStockInForm] = useState({
    ingredient_id: "",
    quantity: "",
    unit_cost: "",
    notes: "",
  });
  const [stockInLoading, setStockInLoading] = useState(false);
  const [stockInError, setStockInError] = useState("");

  // Stock Adjustment Modal State
  const [showAdjustmentModal, setShowAdjustmentModal] = useState(false);
  const [adjustmentForm, setAdjustmentForm] = useState({
    ingredient_id: "",
    quantity_delta: "",
    movement_type: "AUDIT_ADJUSTMENT",
    notes: "",
  });
  const [adjLoading, setAdjLoading] = useState(false);
  const [adjError, setAdjError] = useState("");

  // New Ingredient Modal State
  const [showNewIngModal, setShowNewIngModal] = useState(false);
  const [newIngForm, setNewIngForm] = useState({
    name: "",
    category: "Produce",
    unit_of_measure: "KG",
    initial_stock: "0",
    reorder_level: "5",
  });
  const [newIngLoading, setNewIngLoading] = useState(false);
  const [newIngError, setNewIngError] = useState("");

  // Reorder Level Modal
  const [editingReorderItem, setEditingReorderItem] = useState(null);
  const [newReorderLevel, setNewReorderLevel] = useState("");
  const [reorderLoading, setReorderLoading] = useState(false);

  const fetchInventoryData = async () => {
    setStockLoading(true);
    try {
      const [invRes, alertRes] = await Promise.all([
        inventoryApi.getInventory({
          low_stock_only: lowStockFilter ? true : undefined,
          search: searchStock.trim() || undefined,
        }),
        inventoryApi.getLowStockAlerts(),
      ]);

      if (invRes.data?.success) setInventory(invRes.data.data);
      if (alertRes.data?.success) setLowStockAlerts(alertRes.data.data);
    } catch (err) {
      console.error("Failed to load inventory stock", err);
    } finally {
      setStockLoading(false);
    }
  };

  const fetchMovements = async () => {
    setMovementLoading(true);
    try {
      const params = {
        page: movementPage,
        page_size: 15,
      };
      if (movementFilterType) params.movement_type = movementFilterType;
      const resp = await inventoryApi.getMovements(params);
      if (resp.data?.success) {
        setMovements(resp.data.data.items);
        setMovementTotal(resp.data.data.meta.total_count);
      }
    } catch (err) {
      console.error("Failed to load stock movements", err);
    } finally {
      setMovementLoading(false);
    }
  };

  const fetchIngredients = async () => {
    setIngredientsLoading(true);
    try {
      const resp = await inventoryApi.getIngredients();
      if (resp.data?.success) {
        setIngredients(resp.data.data);
      }
    } catch (err) {
      console.error("Failed to load master ingredients", err);
    } finally {
      setIngredientsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "stock") fetchInventoryData();
    if (activeTab === "movements") fetchMovements();
    if (activeTab === "ingredients") fetchIngredients();
  }, [activeTab, lowStockFilter, movementPage, movementFilterType]);

  const handleStockInSubmit = async (e) => {
    e.preventDefault();
    setStockInLoading(true);
    setStockInError("");
    try {
      const payload = {
        ingredient_id: Number(stockInForm.ingredient_id),
        quantity: parseFloat(stockInForm.quantity),
        unit_cost: stockInForm.unit_cost ? parseFloat(stockInForm.unit_cost) : undefined,
        notes: stockInForm.notes.trim() || undefined,
      };
      const resp = await inventoryApi.stockIn(payload);
      if (resp.data?.success) {
        setShowStockInModal(false);
        setStockInForm({ ingredient_id: "", quantity: "", unit_cost: "", notes: "" });
        fetchInventoryData();
      }
    } catch (err) {
      setStockInError(err.response?.data?.detail || "Stock-in recording failed");
    } finally {
      setStockInLoading(false);
    }
  };

  const handleAdjustmentSubmit = async (e) => {
    e.preventDefault();
    setAdjLoading(true);
    setAdjError("");
    try {
      const payload = {
        ingredient_id: Number(adjustmentForm.ingredient_id),
        quantity_delta: parseFloat(adjustmentForm.quantity_delta),
        movement_type: adjustmentForm.movement_type,
        notes: adjustmentForm.notes.trim(),
      };
      const resp = await inventoryApi.stockAdjustment(payload);
      if (resp.data?.success) {
        setShowAdjustmentModal(false);
        setAdjustmentForm({ ingredient_id: "", quantity_delta: "", movement_type: "AUDIT_ADJUSTMENT", notes: "" });
        fetchInventoryData();
      }
    } catch (err) {
      setAdjError(err.response?.data?.detail || "Stock adjustment rejected");
    } finally {
      setAdjLoading(false);
    }
  };

  const handleNewIngredientSubmit = async (e) => {
    e.preventDefault();
    setNewIngLoading(true);
    setNewIngError("");
    try {
      const payload = {
        name: newIngForm.name.trim(),
        category: newIngForm.category.trim(),
        unit_of_measure: newIngForm.unit_of_measure,
        initial_stock: parseFloat(newIngForm.initial_stock || "0"),
        reorder_level: parseFloat(newIngForm.reorder_level || "1"),
      };
      const resp = await inventoryApi.createIngredient(payload);
      if (resp.data?.success) {
        setShowNewIngModal(false);
        setNewIngForm({ name: "", category: "Produce", unit_of_measure: "KG", initial_stock: "0", reorder_level: "5" });
        fetchInventoryData();
        fetchIngredients();
      }
    } catch (err) {
      setNewIngError(err.response?.data?.detail || "Failed to create ingredient");
    } finally {
      setNewIngLoading(false);
    }
  };

  const handleSaveReorder = async (e) => {
    e.preventDefault();
    if (!editingReorderItem) return;
    setReorderLoading(true);
    try {
      const resp = await inventoryApi.updateReorderLevel(
        editingReorderItem.ingredient_id,
        parseFloat(newReorderLevel)
      );
      if (resp.data?.success) {
        setEditingReorderItem(null);
        fetchInventoryData();
      }
    } catch (err) {
      alert("Failed to update reorder threshold");
    } finally {
      setReorderLoading(false);
    }
  };

  return (
    <KitchenLayout
      title="Kitchen Inventory & Stock Control"
      subtitle="Per-kitchen storage balances, automated replenishment alerts, and immutable movement audits"
      actionButton={
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              fetchIngredients();
              setShowStockInModal(true);
            }}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-sm"
          >
            <ArrowDownRight className="w-4 h-4" />
            <span>Stock-In</span>
          </button>

          <button
            onClick={() => {
              fetchIngredients();
              setShowAdjustmentModal(true);
            }}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-charcoal-900 hover:bg-charcoal-800 text-white text-xs font-bold transition shadow-sm"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Stock Adjustment</span>
          </button>

          {isManager && (
            <button
              onClick={() => setShowNewIngModal(true)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-terracotta-600 hover:bg-terracotta-700 text-white text-xs font-bold transition shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>New Ingredient</span>
            </button>
          )}
        </div>
      }
    >
      {/* Sub-tab Navigation */}
      <div className="flex space-x-2 mb-6 border-b border-stone-200 pb-2">
        <button
          onClick={() => setActiveTab("stock")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === "stock"
              ? "bg-terracotta-600 text-white shadow-sm"
              : "text-stone-600 hover:bg-stone-100"
          }`}
        >
          <Package className="w-4 h-4" />
          <span>On-Hand Balances ({inventory.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("movements")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === "movements"
              ? "bg-terracotta-600 text-white shadow-sm"
              : "text-stone-600 hover:bg-stone-100"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Movement History Audit</span>
        </button>

        <button
          onClick={() => setActiveTab("ingredients")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === "ingredients"
              ? "bg-terracotta-600 text-white shadow-sm"
              : "text-stone-600 hover:bg-stone-100"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Master Ingredients Catalog</span>
        </button>
      </div>

      {/* TAB 1: ON-HAND STOCK BALANCES */}
      {activeTab === "stock" && (
        <div className="space-y-6">
          {/* Low Stock Banners (if any) */}
          {lowStockAlerts.length > 0 && (
            <div className="p-4 rounded-3xl bg-amber-50 border border-amber-200 shadow-sm">
              <div className="flex items-center space-x-2 text-amber-900 font-bold text-sm mb-2">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <span>{lowStockAlerts.length} Ingredients Below Minimum Threshold</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {lowStockAlerts.map((a) => (
                  <div key={a.ingredient_id} className="p-3 rounded-2xl bg-white border border-amber-200 flex justify-between items-center text-xs">
                    <div>
                      <span className="font-bold text-charcoal-900 block">{a.ingredient_name}</span>
                      <span className="text-amber-800">
                        Stock: <strong>{parseFloat(a.current_stock).toFixed(2)}</strong> {a.unit_of_measure} (Reorder: {parseFloat(a.reorder_level).toFixed(2)})
                      </span>
                    </div>
                    <span className="text-xs font-extrabold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-lg">
                      +{parseFloat(a.suggested_replenishment).toFixed(1)} {a.unit_of_measure}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Search & Low-Stock Toggle Filter */}
          <div className="bg-white rounded-3xl border border-stone-200/80 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-stone-400" />
              <input
                type="text"
                placeholder="Search raw ingredients by name..."
                value={searchStock}
                onChange={(e) => setSearchStock(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchInventoryData()}
                className="w-full pl-10 pr-4 py-2 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
              />
            </div>

            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2 cursor-pointer text-xs font-semibold text-stone-700">
                <input
                  type="checkbox"
                  checked={lowStockFilter}
                  onChange={(e) => setLowStockFilter(e.target.checked)}
                  className="w-4 h-4 text-terracotta-600 rounded focus:ring-terracotta-500 border-stone-300"
                />
                <span>Show Low-Stock Only</span>
              </label>

              <button
                onClick={fetchInventoryData}
                className="p-2 rounded-xl border border-stone-200 hover:bg-stone-50 text-stone-600 transition"
                title="Refresh balances"
              >
                <RefreshCw className={`w-4 h-4 ${stockLoading ? "animate-spin text-terracotta-600" : ""}`} />
              </button>
            </div>
          </div>

          {/* Balances Table */}
          <div className="bg-white rounded-3xl border border-stone-200/80 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-stone-50 border-b border-stone-200 text-xs font-bold text-stone-600 uppercase tracking-wider">
                    <th className="py-4 px-6">Ingredient</th>
                    <th className="py-4 px-6">Category</th>
                    <th className="py-4 px-6">Current Stock</th>
                    <th className="py-4 px-6">Reorder Level</th>
                    <th className="py-4 px-6">Stock Status</th>
                    <th className="py-4 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 text-sm">
                  {stockLoading ? (
                    <tr>
                      <td colSpan="6" className="py-12 text-center text-stone-400">
                        <div className="w-8 h-8 border-3 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-2"></div>
                        Fetching kitchen stock balances...
                      </td>
                    </tr>
                  ) : inventory.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="py-12 text-center text-stone-500">
                        No inventory records found. Use "Stock-In" or "New Ingredient" to record items.
                      </td>
                    </tr>
                  ) : (
                    inventory.map((row) => (
                      <tr key={row.inventory_id} className="hover:bg-stone-50/60 transition">
                        <td className="py-4 px-6">
                          <span className="font-extrabold text-charcoal-900 block">{row.ingredient_name}</span>
                          <span className="text-[11px] text-stone-400">ID: #{row.ingredient_id}</span>
                        </td>
                        <td className="py-4 px-6">
                          <span className="px-2 py-0.5 rounded-lg bg-stone-100 text-stone-700 text-xs font-medium">
                            {row.category}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <span
                            className={`font-black text-base ${
                              row.is_low_stock ? "text-rose-600" : "text-charcoal-900"
                            }`}
                          >
                            {parseFloat(row.current_stock).toFixed(3)}
                          </span>{" "}
                          <span className="text-xs text-stone-500 font-semibold">{row.unit_of_measure}</span>
                        </td>
                        <td className="py-4 px-6">
                          <span className="font-semibold text-stone-700">
                            {parseFloat(row.reorder_level).toFixed(3)}
                          </span>{" "}
                          <span className="text-xs text-stone-400">{row.unit_of_measure}</span>
                        </td>
                        <td className="py-4 px-6">
                          {row.is_low_stock ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              Low Stock
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Adequate
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-6 text-right space-x-2">
                          {isManager && (
                            <button
                              onClick={() => {
                                setEditingReorderItem(row);
                                setNewReorderLevel(row.reorder_level);
                              }}
                              className="px-2.5 py-1 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-semibold transition"
                              title="Edit reorder threshold"
                            >
                              Edit Threshold
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: AUDIT MOVEMENT HISTORY LOG */}
      {activeTab === "movements" && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-stone-200/80 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <span className="text-xs font-bold text-stone-600">Filter Type:</span>
              <select
                value={movementFilterType}
                onChange={(e) => {
                  setMovementFilterType(e.target.value);
                  setMovementPage(1);
                }}
                className="px-3 py-1.5 rounded-xl border border-stone-200 text-xs bg-white focus:outline-none"
              >
                <option value="">All Movement Types</option>
                <option value="RESTOCK">RESTOCK (Stock In)</option>
                <option value="ORDER_CONSUMPTION">ORDER_CONSUMPTION (Recipe Fire)</option>
                <option value="AUDIT_ADJUSTMENT">AUDIT_ADJUSTMENT</option>
                <option value="SPOILAGE">SPOILAGE</option>
                <option value="WASTE">WASTE</option>
              </select>
            </div>

            <button
              onClick={fetchMovements}
              className="p-2 rounded-xl border border-stone-200 hover:bg-stone-50 text-stone-600 transition"
            >
              <RefreshCw className={`w-4 h-4 ${movementLoading ? "animate-spin text-terracotta-600" : ""}`} />
            </button>
          </div>

          <div className="bg-white rounded-3xl border border-stone-200/80 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-stone-50 border-b border-stone-200 text-xs font-bold text-stone-600 uppercase tracking-wider">
                    <th className="py-4 px-6">Timestamp</th>
                    <th className="py-4 px-6">Ingredient</th>
                    <th className="py-4 px-6">Type</th>
                    <th className="py-4 px-6">Quantity Delta</th>
                    <th className="py-4 px-6">Order Ref</th>
                    <th className="py-4 px-6">Actor / Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 text-sm">
                  {movementLoading ? (
                    <tr>
                      <td colSpan="6" className="py-12 text-center text-stone-400">
                        <div className="w-8 h-8 border-3 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-2"></div>
                        Loading movement logs...
                      </td>
                    </tr>
                  ) : movements.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="py-12 text-center text-stone-500">
                        No movement audit logs recorded yet.
                      </td>
                    </tr>
                  ) : (
                    movements.map((m) => (
                      <tr key={m.movement_id} className="hover:bg-stone-50/60 transition">
                        <td className="py-4 px-6 text-xs text-stone-500 whitespace-nowrap">
                          {new Date(m.created_at).toLocaleString()}
                        </td>
                        <td className="py-4 px-6">
                          <span className="font-bold text-charcoal-900 block">{m.ingredient_name}</span>
                          <span className="text-[11px] text-stone-400">{m.unit_of_measure}</span>
                        </td>
                        <td className="py-4 px-6">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-bold uppercase tracking-wider ${
                              m.movement_type === "RESTOCK"
                                ? "bg-emerald-100 text-emerald-800"
                                : m.movement_type === "ORDER_CONSUMPTION"
                                ? "bg-sky-100 text-sky-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {m.movement_type}
                          </span>
                        </td>
                        <td className="py-4 px-6 font-mono font-bold">
                          <span
                            className={
                              parseFloat(m.quantity_delta) >= 0 ? "text-emerald-600" : "text-rose-600"
                            }
                          >
                            {parseFloat(m.quantity_delta) >= 0 ? "+" : ""}
                            {parseFloat(m.quantity_delta).toFixed(3)}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-xs text-stone-600">
                          {m.reference_order_id ? (
                            <span className="font-semibold text-terracotta-600">Order #{m.reference_order_id}</span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="py-4 px-6 text-xs">
                          <span className="font-medium text-stone-800 block">
                            User #{m.recorded_by_user_id || "System"} ({m.recorded_by_name || "Auto"})
                          </span>
                          <span className="text-stone-500">{m.notes || "No notes"}</span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: MASTER INGREDIENTS */}
      {activeTab === "ingredients" && (
        <div className="bg-white rounded-3xl border border-stone-200/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-stone-100 flex justify-between items-center">
            <h4 className="text-sm font-bold text-charcoal-900">Culinary Ingredients Catalog</h4>
            {isManager && (
              <button
                onClick={() => setShowNewIngModal(true)}
                className="px-3 py-1.5 bg-terracotta-600 hover:bg-terracotta-700 text-white rounded-xl text-xs font-bold transition"
              >
                + Register New Ingredient
              </button>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-stone-50 border-b border-stone-200 text-xs font-bold text-stone-600 uppercase tracking-wider">
                  <th className="py-4 px-6">ID</th>
                  <th className="py-4 px-6">Name</th>
                  <th className="py-4 px-6">Category</th>
                  <th className="py-4 px-6">Standard Unit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 text-sm">
                {ingredients.map((ing) => (
                  <tr key={ing.ingredient_id} className="hover:bg-stone-50/60 transition">
                    <td className="py-4 px-6 font-mono text-xs text-stone-500">#{ing.ingredient_id}</td>
                    <td className="py-4 px-6 font-bold text-charcoal-900">{ing.name}</td>
                    <td className="py-4 px-6 text-xs text-stone-600">{ing.category}</td>
                    <td className="py-4 px-6 font-semibold text-xs text-stone-700">{ing.unit_of_measure}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: STOCK IN */}
      {showStockInModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-charcoal-900 mb-1">Receive Raw Stock (Stock-In)</h3>
            <p className="text-xs text-stone-500 mb-4">
              Add received raw culinary materials into your kitchen's on-hand storage balance.
            </p>

            {stockInError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium mb-4">
                {stockInError}
              </div>
            )}

            <form onSubmit={handleStockInSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Select Ingredient *</label>
                <select
                  required
                  value={stockInForm.ingredient_id}
                  onChange={(e) => setStockInForm({ ...stockInForm, ingredient_id: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
                >
                  <option value="">-- Choose Ingredient --</option>
                  {ingredients.map((i) => (
                    <option key={i.ingredient_id} value={i.ingredient_id}>
                      {i.name} ({i.unit_of_measure})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Quantity *</label>
                  <input
                    type="number"
                    step="0.001"
                    min="0.001"
                    required
                    placeholder="10.000"
                    value={stockInForm.quantity}
                    onChange={(e) => setStockInForm({ ...stockInForm, quantity: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Unit Cost (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="120.00"
                    value={stockInForm.unit_cost}
                    onChange={(e) => setStockInForm({ ...stockInForm, unit_cost: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Shipment Reference / Notes</label>
                <input
                  type="text"
                  placeholder="e.g. Invoice #PO-9912, fresh morning delivery"
                  value={stockInForm.notes}
                  onChange={(e) => setStockInForm({ ...stockInForm, notes: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  disabled={stockInLoading}
                  onClick={() => setShowStockInModal(false)}
                  className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={stockInLoading}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition shadow-sm flex items-center space-x-1.5"
                >
                  {stockInLoading && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                  <span>Commit Stock-In</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: STOCK ADJUSTMENT */}
      {showAdjustmentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-charcoal-900 mb-1">Inventory Adjustment (Audit/Spoilage)</h3>
            <p className="text-xs text-stone-500 mb-4">
              Apply manual adjustments. Negative stock prevention is strictly enforced by the backend transaction.
            </p>

            {adjError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium mb-4">
                {adjError}
              </div>
            )}

            <form onSubmit={handleAdjustmentSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Select Ingredient *</label>
                <select
                  required
                  value={adjustmentForm.ingredient_id}
                  onChange={(e) => setAdjustmentForm({ ...adjustmentForm, ingredient_id: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
                >
                  <option value="">-- Choose Ingredient --</option>
                  {ingredients.map((i) => (
                    <option key={i.ingredient_id} value={i.ingredient_id}>
                      {i.name} ({i.unit_of_measure})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Delta Quantity *</label>
                  <input
                    type="number"
                    step="0.001"
                    required
                    placeholder="-2.500 or +1.000"
                    value={adjustmentForm.quantity_delta}
                    onChange={(e) => setAdjustmentForm({ ...adjustmentForm, quantity_delta: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                  <span className="text-[10px] text-stone-400">Negative to deduct, positive to add</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Reason Type *</label>
                  <select
                    value={adjustmentForm.movement_type}
                    onChange={(e) => setAdjustmentForm({ ...adjustmentForm, movement_type: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
                  >
                    <option value="AUDIT_ADJUSTMENT">AUDIT_ADJUSTMENT</option>
                    <option value="SPOILAGE">SPOILAGE</option>
                    <option value="WASTE">WASTE</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Audit Explanation / Note *</label>
                <input
                  type="text"
                  required
                  placeholder="Reason for variance (e.g. Spoilage in walk-in cooler)"
                  value={adjustmentForm.notes}
                  onChange={(e) => setAdjustmentForm({ ...adjustmentForm, notes: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  disabled={adjLoading}
                  onClick={() => setShowAdjustmentModal(false)}
                  className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={adjLoading}
                  className="px-5 py-2 rounded-xl bg-charcoal-900 hover:bg-charcoal-800 text-white font-bold text-xs transition shadow-sm flex items-center space-x-1.5"
                >
                  {adjLoading && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                  <span>Apply Adjustment</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: NEW INGREDIENT */}
      {showNewIngModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-charcoal-900 mb-1">Register Master Ingredient</h3>
            <p className="text-xs text-stone-500 mb-4">
              Registers a new culinary ingredient in the central catalog and creates an initial inventory row for this kitchen.
            </p>

            {newIngError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium mb-4">
                {newIngError}
              </div>
            )}

            <form onSubmit={handleNewIngredientSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Ingredient Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Saffron Strands"
                  value={newIngForm.name}
                  onChange={(e) => setNewIngForm({ ...newIngForm, name: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Category *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Spices, Dairy, Meat"
                    value={newIngForm.category}
                    onChange={(e) => setNewIngForm({ ...newIngForm, category: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Unit of Measure *</label>
                  <select
                    value={newIngForm.unit_of_measure}
                    onChange={(e) => setNewIngForm({ ...newIngForm, unit_of_measure: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500 bg-white"
                  >
                    <option value="KG">KG (Kilograms)</option>
                    <option value="GRAM">GRAM (Grams)</option>
                    <option value="LITER">LITER (Liters)</option>
                    <option value="ML">ML (Milliliters)</option>
                    <option value="PIECE">PIECE (Unit count)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Initial Stock</label>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    value={newIngForm.initial_stock}
                    onChange={(e) => setNewIngForm({ ...newIngForm, initial_stock: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Reorder Level *</label>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    required
                    value={newIngForm.reorder_level}
                    onChange={(e) => setNewIngForm({ ...newIngForm, reorder_level: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  disabled={newIngLoading}
                  onClick={() => setShowNewIngModal(false)}
                  className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={newIngLoading}
                  className="px-5 py-2 rounded-xl bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold text-xs transition shadow-sm flex items-center space-x-1.5"
                >
                  {newIngLoading && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                  <span>Save Ingredient</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT REORDER LEVEL */}
      {editingReorderItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl border border-stone-200 max-w-sm w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-charcoal-900 mb-1">
              Update Reorder Threshold
            </h3>
            <p className="text-xs text-stone-500 mb-4">
              For <strong>{editingReorderItem.ingredient_name}</strong> ({editingReorderItem.unit_of_measure})
            </p>

            <form onSubmit={handleSaveReorder}>
              <div className="mb-4">
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Minimum Reorder Level ({editingReorderItem.unit_of_measure})
                </label>
                <input
                  type="number"
                  step="0.001"
                  min="0"
                  required
                  value={newReorderLevel}
                  onChange={(e) => setNewReorderLevel(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:border-terracotta-500"
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  disabled={reorderLoading}
                  onClick={() => setEditingReorderItem(null)}
                  className="px-4 py-2 rounded-xl text-stone-600 font-medium hover:bg-stone-100 text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reorderLoading}
                  className="px-5 py-2 rounded-xl bg-terracotta-600 hover:bg-terracotta-700 text-white font-bold text-xs transition shadow-sm"
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </KitchenLayout>
  );
};
