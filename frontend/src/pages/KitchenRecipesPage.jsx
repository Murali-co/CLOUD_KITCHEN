import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  BookOpen,
  Plus,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Flame,
  Package,
  UtensilsCrossed,
  Search,
  Save,
  HelpCircle,
  Info,
} from "lucide-react";
import { KitchenLayout } from "../components/KitchenLayout";
import { kitchenApi, inventoryApi } from "../services/api";
import { useAuth } from "../context/AuthContext";

export const KitchenRecipesPage = () => {
  const { isManager } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialItemId = searchParams.get("item_id");

  const [menuItems, setMenuItems] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [selectedItemId, setSelectedItemId] = useState(initialItemId || "");
  const [recipeData, setRecipeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recipeLoading, setRecipeLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // Editable Bill of Materials Items
  const [recipeItems, setRecipeItems] = useState([]);

  // Add Item to BOM form state
  const [newIngredientId, setNewIngredientId] = useState("");
  const [newQuantity, setNewQuantity] = useState("");

  const loadMenuAndIngredients = async () => {
    setLoading(true);
    try {
      const [menuRes, ingRes] = await Promise.all([
        kitchenApi.getMenu(),
        inventoryApi.getIngredients(),
      ]);

      if (menuRes.data?.success) {
        setMenuItems(menuRes.data.data);
        if (!selectedItemId && menuRes.data.data.length > 0) {
          setSelectedItemId(String(menuRes.data.data[0].menu_item_id));
        }
      }
      if (ingRes.data?.success) {
        setIngredients(ingRes.data.data);
      }
    } catch (err) {
      console.error("Failed to load catalog data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMenuAndIngredients();
  }, []);

  const loadRecipe = async (itemId) => {
    if (!itemId) return;
    setRecipeLoading(true);
    setErrorMessage("");
    setSaveSuccess(false);
    try {
      const resp = await inventoryApi.getRecipe(itemId);
      if (resp.data?.success) {
        setRecipeData(resp.data.data);
        setRecipeItems(
          resp.data.data.ingredients.map((ing) => ({
            ingredient_id: ing.ingredient_id,
            ingredient_name: ing.ingredient_name,
            unit_of_measure: ing.unit_of_measure,
            quantity_required: ing.quantity_required,
            current_stock: ing.current_stock,
          }))
        );
      }
    } catch (err) {
      console.error("Failed to load recipe", err);
      setErrorMessage("Could not load recipe details for selected dish");
    } finally {
      setRecipeLoading(false);
    }
  };

  useEffect(() => {
    if (selectedItemId) {
      setSearchParams({ item_id: selectedItemId });
      loadRecipe(selectedItemId);
    }
  }, [selectedItemId]);

  const handleAddIngredient = (e) => {
    e.preventDefault();
    if (!newIngredientId || !newQuantity || parseFloat(newQuantity) <= 0) {
      alert("Please select an ingredient and enter a positive quantity");
      return;
    }

    const ingId = Number(newIngredientId);
    if (recipeItems.some((i) => i.ingredient_id === ingId)) {
      alert("Ingredient is already included in this recipe. Update its quantity instead.");
      return;
    }

    const ingObj = ingredients.find((i) => i.ingredient_id === ingId);
    if (!ingObj) return;

    setRecipeItems([
      ...recipeItems,
      {
        ingredient_id: ingId,
        ingredient_name: ingObj.name,
        unit_of_measure: ingObj.unit_of_measure,
        quantity_required: parseFloat(newQuantity),
        current_stock: "0.000",
      },
    ]);

    setNewIngredientId("");
    setNewQuantity("");
  };

  const handleQuantityChange = (ingredientId, val) => {
    setRecipeItems((prev) =>
      prev.map((itm) => (itm.ingredient_id === ingredientId ? { ...itm, quantity_required: val } : itm))
    );
  };

  const handleRemoveIngredient = (ingredientId) => {
    setRecipeItems((prev) => prev.filter((i) => i.ingredient_id !== ingredientId));
  };

  const handleSaveRecipe = async () => {
    if (!selectedItemId) return;
    setSaveLoading(true);
    setErrorMessage("");
    setSaveSuccess(false);

    try {
      const payload = {
        ingredients: recipeItems.map((itm) => ({
          ingredient_id: itm.ingredient_id,
          quantity_required: parseFloat(itm.quantity_required),
          unit_of_measure: itm.unit_of_measure,
        })),
      };

      const resp = await inventoryApi.updateRecipe(selectedItemId, payload);
      if (resp.data?.success) {
        setSaveSuccess(true);
        loadRecipe(selectedItemId);
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || "Failed to commit recipe specification");
    } finally {
      setSaveLoading(false);
    }
  };

  const selectedItemObj = menuItems.find((m) => String(m.menu_item_id) === String(selectedItemId));

  return (
    <KitchenLayout
      title="Recipe Bill of Materials (BOM)"
      subtitle="Configure ingredient consumption per dish portion for automated order inventory deduction"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Dish Selector & Explanation */}
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-stone-200/80 p-6 shadow-sm">
            <label className="block text-xs font-bold text-stone-600 uppercase tracking-wider mb-2">
              Select Menu Dish
            </label>
            <select
              value={selectedItemId}
              onChange={(e) => setSelectedItemId(e.target.value)}
              className="w-full px-3.5 py-3 rounded-2xl border border-stone-200 text-sm font-semibold focus:outline-none focus:border-terracotta-500 bg-white"
            >
              {menuItems.map((item) => (
                <option key={item.menu_item_id} value={item.menu_item_id}>
                  {item.name} — ₹{parseFloat(item.base_price).toFixed(2)} ({item.category_name})
                </option>
              ))}
            </select>

            {selectedItemObj && (
              <div className="mt-4 p-4 rounded-2xl bg-stone-50 border border-stone-100 text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-stone-500">Category:</span>
                  <strong className="text-charcoal-900">{selectedItemObj.category_name}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Prep Time:</span>
                  <strong className="text-charcoal-900">{selectedItemObj.preparation_time_minutes} minutes</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Status:</span>
                  <strong className={selectedItemObj.is_available ? "text-emerald-700" : "text-rose-700"}>
                    {selectedItemObj.is_available ? "In Stock" : "86'd / Sold Out"}
                  </strong>
                </div>
              </div>
            )}
          </div>

          {/* Educational Info Card */}
          <div className="bg-gradient-to-tr from-stone-900 to-charcoal-800 text-white rounded-3xl p-6 shadow-sm space-y-3">
            <div className="flex items-center space-x-2 text-amber-400 font-bold text-sm">
              <Flame className="w-5 h-5 text-terracotta-500" />
              <span>How Auto-Deduction Works</span>
            </div>
            <p className="text-xs text-stone-300 leading-relaxed">
              When an order ticket is advanced from <strong>CONFIRMED</strong> to <strong>PREPARING</strong>, the backend multiplies each ingredient's quantity by the ordered item count:
            </p>
            <div className="p-3 rounded-xl bg-charcoal-900 text-amber-300 font-mono text-[11px] border border-charcoal-700">
              consumed_stock = quantity_required × item_quantity
            </div>
            <p className="text-xs text-stone-400">
              MySQL executes row locks with <code>SELECT ... FOR UPDATE</code>. If any ingredient is insufficient, the status transition rolls back completely to prevent negative inventory.
            </p>
          </div>
        </div>

        {/* Right Column (2 Cols): Recipe Builder & Bill of Materials */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-3xl border border-stone-200/80 p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-stone-100 mb-6 gap-3">
              <div>
                <span className="text-xs font-bold text-terracotta-600 uppercase tracking-wider block">
                  Bill of Materials (BOM)
                </span>
                <h3 className="text-xl font-bold text-charcoal-900">
                  {selectedItemObj?.name || "Select a dish"}
                </h3>
              </div>

              {isManager && (
                <button
                  onClick={handleSaveRecipe}
                  disabled={saveLoading || recipeLoading}
                  className="flex items-center space-x-1.5 px-4 py-2 bg-terracotta-600 hover:bg-terracotta-700 text-white text-xs font-bold rounded-2xl transition shadow-sm self-start sm:self-auto"
                >
                  <Save className="w-4 h-4" />
                  <span>{saveLoading ? "Saving..." : "Save Recipe BOM"}</span>
                </button>
              )}
            </div>

            {saveSuccess && (
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-bold mb-4 flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Recipe specifications updated and saved to database successfully!</span>
              </div>
            )}

            {errorMessage && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium mb-4">
                {errorMessage}
              </div>
            )}

            {/* Recipe Table */}
            {recipeLoading ? (
              <div className="py-16 text-center text-stone-400">
                <div className="w-8 h-8 border-3 border-terracotta-200 border-t-terracotta-600 rounded-full animate-spin mx-auto mb-2"></div>
                Loading recipe components...
              </div>
            ) : recipeItems.length === 0 ? (
              <div className="py-12 text-center bg-stone-50 rounded-2xl border border-stone-200 mb-6">
                <BookOpen className="w-10 h-10 text-stone-300 mx-auto mb-2" />
                <p className="text-sm font-semibold text-stone-700">No ingredients linked yet</p>
                <p className="text-xs text-stone-400 max-w-sm mx-auto mt-0.5">
                  Use the component adder below to specify raw materials consumed per serving.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto mb-6">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-stone-50 border-b border-stone-200 text-xs font-bold text-stone-600 uppercase tracking-wider">
                      <th className="py-3 px-4">Raw Ingredient</th>
                      <th className="py-3 px-4">Standard Unit</th>
                      <th className="py-3 px-4">Quantity / Serving</th>
                      <th className="py-3 px-4">On-Hand Stock</th>
                      {isManager && <th className="py-3 px-4 text-right">Remove</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100 text-sm">
                    {recipeItems.map((item) => (
                      <tr key={item.ingredient_id} className="hover:bg-stone-50/50">
                        <td className="py-3.5 px-4 font-bold text-charcoal-900">
                          {item.ingredient_name}
                        </td>
                        <td className="py-3.5 px-4 text-xs font-semibold text-stone-500">
                          {item.unit_of_measure}
                        </td>
                        <td className="py-3.5 px-4">
                          {isManager ? (
                            <input
                              type="number"
                              step="0.001"
                              min="0.001"
                              value={item.quantity_required}
                              onChange={(e) => handleQuantityChange(item.ingredient_id, e.target.value)}
                              className="w-28 px-2.5 py-1.5 rounded-xl border border-stone-200 text-sm font-bold text-charcoal-900 focus:outline-none focus:border-terracotta-500"
                            />
                          ) : (
                            <span className="font-bold text-charcoal-900">
                              {parseFloat(item.quantity_required).toFixed(3)}
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-xs font-semibold text-stone-600">
                          {parseFloat(item.current_stock || "0").toFixed(2)} {item.unit_of_measure}
                        </td>
                        {isManager && (
                          <td className="py-3.5 px-4 text-right">
                            <button
                              type="button"
                              onClick={() => handleRemoveIngredient(item.ingredient_id)}
                              className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 transition"
                              title="Remove from recipe"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Add Ingredient Form (Managers Only) */}
            {isManager && (
              <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200">
                <h4 className="text-xs font-bold text-charcoal-900 uppercase tracking-wider mb-3">
                  + Add Component to Recipe
                </h4>
                <form onSubmit={handleAddIngredient} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-2">
                    <select
                      value={newIngredientId}
                      onChange={(e) => setNewIngredientId(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-stone-200 text-xs font-medium focus:outline-none focus:border-terracotta-500 bg-white"
                    >
                      <option value="">-- Select Culinary Ingredient --</option>
                      {ingredients.map((ing) => (
                        <option key={ing.ingredient_id} value={ing.ingredient_id}>
                          {ing.name} ({ing.unit_of_measure}) — {ing.category}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="number"
                      step="0.001"
                      min="0.001"
                      placeholder="Qty / serving"
                      value={newQuantity}
                      onChange={(e) => setNewQuantity(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-stone-200 text-xs font-bold focus:outline-none focus:border-terracotta-500"
                    />
                    <button
                      type="submit"
                      className="px-3.5 py-2 bg-charcoal-900 hover:bg-charcoal-800 text-white rounded-xl text-xs font-bold transition shrink-0"
                    >
                      Add
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </KitchenLayout>
  );
};
