-- =====================================================================
-- CLOUD KITCHEN MANAGEMENT & FOOD ORDERING SYSTEM
-- Performance Indexes & Query Optimization Script
-- Target RDBMS: MySQL 8.0+ (InnoDB)
-- =====================================================================

-- This script creates performance-tuning secondary indexes for high-frequency
-- query access paths, filtering, ordering, joins, and aggregations.
-- Primary keys and UNIQUE constraints already possess B-tree indexes automatically.

-- ---------------------------------------------------------------------
-- 1. Table: users
-- ---------------------------------------------------------------------
-- Supports filtering active staff, active drivers, or administrators in portals.
CREATE INDEX idx_users_role_status 
ON users (role, is_active);

-- ---------------------------------------------------------------------
-- 2. Table: customer
-- ---------------------------------------------------------------------
-- Supports tier-based loyalty calculations and VIP promotion targeting.
CREATE INDEX idx_customer_loyalty 
ON customer (loyalty_points);

-- ---------------------------------------------------------------------
-- 3. Table: kitchen
-- ---------------------------------------------------------------------
-- Speeds up discovery of operating kitchens within a specific delivery city.
CREATE INDEX idx_kitchen_status_city 
ON kitchen (operating_status, city);

-- ---------------------------------------------------------------------
-- 4. Table: staff
-- ---------------------------------------------------------------------
-- Optimizes roster lookups and shift planning for kitchen managers.
CREATE INDEX idx_staff_kitchen_role 
ON staff (kitchen_id, staff_role);

-- ---------------------------------------------------------------------
-- 5. Table: delivery_person
-- ---------------------------------------------------------------------
-- Optimizes automated dispatch algorithms querying for available drivers.
CREATE INDEX idx_delivery_person_status 
ON delivery_person (current_status);

-- Enables spatial/proximity bounding box queries for nearby courier assignment.
CREATE INDEX idx_delivery_person_location 
ON delivery_person (current_latitude, current_longitude);

-- ---------------------------------------------------------------------
-- 6. Table: category
-- ---------------------------------------------------------------------
-- Powers fast retrieval of active menu categories sorted by display order.
CREATE INDEX idx_category_active_order 
ON category (is_active, display_order);

-- ---------------------------------------------------------------------
-- 7. Table: menu_item
-- ---------------------------------------------------------------------
-- Composite covering index for customer menu browsing within a specific branch and category.
CREATE INDEX idx_menu_item_search 
ON menu_item (kitchen_id, category_id, is_available);

-- Fast dietary filtering (Vegetarian only) for customer app menus.
CREATE INDEX idx_menu_item_veg 
ON menu_item (is_vegetarian, is_available);

-- Price sorting (Low to High / High to Low).
CREATE INDEX idx_menu_item_price 
ON menu_item (base_price);

-- ---------------------------------------------------------------------
-- 8. Table: address
-- ---------------------------------------------------------------------
-- Retrieves customer addresses with the default address preselected first.
CREATE INDEX idx_address_customer_default 
ON address (customer_id, is_default);

-- ---------------------------------------------------------------------
-- 9. Table: coupon
-- ---------------------------------------------------------------------
-- Checkout promo code validation: filters active campaigns within current timestamp.
CREATE INDEX idx_coupon_validity 
ON coupon (is_active, valid_from, valid_to);

-- ---------------------------------------------------------------------
-- 10. Table: orders
-- ---------------------------------------------------------------------
-- Speeds up customer order history listing (chronological reverse sort).
CREATE INDEX idx_orders_customer_date 
ON orders (customer_id, placed_at);

-- Kitchen dispatch dashboard: Real-time active orders (e.g. PREPARING, READY_FOR_PICKUP).
CREATE INDEX idx_orders_kitchen_status 
ON orders (kitchen_id, order_status);

-- Analytical index: Daily / weekly sales reports filtered by status (DELIVERED).
CREATE INDEX idx_orders_placed_status 
ON orders (placed_at, order_status);

-- Coupon redemption audits.
CREATE INDEX idx_orders_applied_coupon 
ON orders (applied_coupon_id);

-- ---------------------------------------------------------------------
-- 11. Table: order_item
-- ---------------------------------------------------------------------
-- Optimizes order invoice rendering (fetching all dishes for an order).
CREATE INDEX idx_order_item_order 
ON order_item (order_id);

-- Best-seller analytics (aggregation across order items by menu item).
CREATE INDEX idx_order_item_menu 
ON order_item (menu_item_id);

-- ---------------------------------------------------------------------
-- 12. Table: payment
-- ---------------------------------------------------------------------
-- Checking payment status for checkout reconciliation.
CREATE INDEX idx_payment_order_status 
ON payment (order_id, payment_status);

-- Financial audit and daily settlement reconciliation.
CREATE INDEX idx_payment_initiated 
ON payment (initiated_at);

-- ---------------------------------------------------------------------
-- 13. Table: order_status_history
-- ---------------------------------------------------------------------
-- Chronological order transition history timeline rendering.
CREATE INDEX idx_status_history_order 
ON order_status_history (order_id, created_at);

-- Operational audits for user-triggered cancellations or adjustments.
CREATE INDEX idx_status_history_user 
ON order_status_history (changed_by_user_id);

-- ---------------------------------------------------------------------
-- 14. Table: ingredient
-- ---------------------------------------------------------------------
-- Raw ingredient grouping for procurement and vendor orders.
CREATE INDEX idx_ingredient_category 
ON ingredient (category);

-- ---------------------------------------------------------------------
-- 15. Table: inventory
-- ---------------------------------------------------------------------
-- Low-stock alert trigger: Finds ingredients where current_stock <= reorder_level.
CREATE INDEX idx_inventory_reorder 
ON inventory (kitchen_id, current_stock, reorder_level);

-- Foreign key lookup on ingredient.
CREATE INDEX idx_inventory_ingredient 
ON inventory (ingredient_id);

-- ---------------------------------------------------------------------
-- 16. Table: inventory_movement
-- ---------------------------------------------------------------------
-- Chronological inventory audit trail per kitchen.
CREATE INDEX idx_inv_movement_kitchen_date 
ON inventory_movement (kitchen_id, created_at);

-- Stock consumption analysis per ingredient.
CREATE INDEX idx_inv_movement_ingredient 
ON inventory_movement (ingredient_id);

-- Order-to-stock consumption reconciliation.
CREATE INDEX idx_inv_movement_order 
ON inventory_movement (reference_order_id);

-- ---------------------------------------------------------------------
-- 17. Table: menu_item_ingredient
-- ---------------------------------------------------------------------
-- Recipe lookup to find all dishes containing a specific raw ingredient (allergen check).
CREATE INDEX idx_recipe_ingredient 
ON menu_item_ingredient (ingredient_id);

-- ---------------------------------------------------------------------
-- 18. Table: delivery
-- ---------------------------------------------------------------------
-- Driver assignment and active delivery transit queries.
CREATE INDEX idx_delivery_driver_status 
ON delivery (delivery_person_id, delivery_status);

-- Fleet management queue for unassigned orders.
CREATE INDEX idx_delivery_status_assigned 
ON delivery (delivery_status, assigned_at);

-- ---------------------------------------------------------------------
-- 19. Table: coupon_usage
-- ---------------------------------------------------------------------
-- Enforcing per-customer coupon redemption limit during checkout.
CREATE INDEX idx_coupon_cust_usage 
ON coupon_usage (coupon_id, customer_id);

-- Customer profile promo redemption history.
CREATE INDEX idx_coupon_usage_customer 
ON coupon_usage (customer_id);

-- ---------------------------------------------------------------------
-- 20. Table: review
-- ---------------------------------------------------------------------
-- Kitchen branch review summary and average rating calculations.
CREATE INDEX idx_review_kitchen_rating 
ON review (kitchen_id, rating);

-- Customer profile review history.
CREATE INDEX idx_review_customer 
ON review (customer_id);
