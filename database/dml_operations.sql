-- =====================================================================
-- GOURMETCLOUD: CLOUD KITCHEN MANAGEMENT & FOOD ORDERING PLATFORM
-- Relational DML Demonstration Script (Requirement M)
-- Target Engine: MySQL 8.0+ (InnoDB)
-- =====================================================================
-- Purpose:
-- This script provides formal, executable demonstrations of MySQL DML operations:
-- 1. INSERT (Single-row, Multi-row, Foreign-key ordered insertions)
-- 2. SELECT (Projections, Filtering, Sorting, Aggregations, Pagination)
-- 3. UPDATE (State changes, inventory adjustments, price updates, address changes)
-- 4. DELETE (Safe transactional soft-deletions and hard-delete rollbacks)
-- 5. ACID Transactions (START TRANSACTION, COMMIT, ROLLBACK demonstrations)
--
-- Note: All queries use the authoritative singular table names (payment, 
-- order_item, menu_item, orders, etc.) matching database/schema.sql.
-- =====================================================================

-- ---------------------------------------------------------------------
-- SECTION 1: INSERT OPERATIONS (Foreign Key Dependency Order)
-- ---------------------------------------------------------------------

-- Step 1.1: Insert a new User (Root entity in 1:1 Polymorphic hierarchy)
INSERT INTO users (
    email, 
    phone_number, 
    password_hash, 
    first_name, 
    last_name, 
    role, 
    is_active
) VALUES (
    'priya.sharma@example.com', 
    '+919876543210', 
    '$2b$12$K8Z0g6ZzKk4vY.jQ8rJ2U.oE9jF7Q4mH2w0k8L9b5P3t7u4g2', 
    'Priya', 
    'Sharma', 
    'CUSTOMER', 
    TRUE
);

-- Capture the generated surrogate key into a user session variable
SET @v_demo_user_id = LAST_INSERT_ID();

-- Step 1.2: Insert Customer Profile (Child specialization entity)
INSERT INTO customer (
    customer_id, 
    loyalty_points, 
    dietary_preference
) VALUES (
    @v_demo_user_id, 
    150, 
    'VEGETARIAN'
);

-- Step 1.3: Insert Customer Delivery Address (Satisfies compound candidate key)
INSERT INTO address (
    customer_id, 
    address_label, 
    recipient_name, 
    recipient_phone, 
    address_line1, 
    address_line2, 
    landmark, 
    city, 
    state, 
    postal_code, 
    latitude, 
    longitude, 
    is_default
) VALUES (
    @v_demo_user_id, 
    'Home', 
    'Priya Sharma', 
    '+919876543210', 
    'Flat 402, Green Glen Layout', 
    'Bellandur Outer Ring Road', 
    'Opposite EcoSpace Tech Park', 
    'Bengaluru', 
    'Karnataka', 
    '560103', 
    12.92790000, 
    77.67910000, 
    TRUE
);

SET @v_demo_address_id = LAST_INSERT_ID();

-- Step 1.4: Multi-row INSERT for Raw Materials (Ingredients)
INSERT INTO ingredient (name, category, unit_of_measure) VALUES
('Organic Baby Spinach', 'Produce', 'GRAM'),
('Cold Pressed Olive Oil', 'Oils & Fats', 'MILLILITER'),
('Kalamata Black Olives', 'Canned Goods', 'GRAM')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- Step 1.5: Insert Menu Items into a Specific Kitchen Branch
INSERT INTO menu_item (
    kitchen_id, 
    category_id, 
    cuisine_id, 
    name, 
    description, 
    base_price, 
    is_vegetarian, 
    is_available, 
    preparation_time_minutes, 
    calories
) VALUES (
    1, 
    2, 
    1, 
    'Artisan Spinach & Feta Bowl', 
    'Organic fresh baby spinach tossed with authentic Greek feta and extra virgin olive oil.', 
    380.00, 
    TRUE, 
    TRUE, 
    15, 
    420
);

SET @v_demo_item_id = LAST_INSERT_ID();

-- ---------------------------------------------------------------------
-- SECTION 2: SELECT OPERATIONS (Queries, Filters, Projections & Sorts)
-- ---------------------------------------------------------------------

-- Query 2.1: Basic Projection with Filtering and Sorting
-- Retrieve all available vegetarian dishes priced under 400 INR in Kitchen Branch 1
SELECT 
    menu_item_id,
    name AS dish_name,
    base_price,
    preparation_time_minutes,
    calories
FROM menu_item
WHERE kitchen_id = 1
  AND is_vegetarian = TRUE
  AND is_available = TRUE
  AND base_price <= 400.00
ORDER BY base_price ASC;

-- Query 2.2: Relational JOIN with Formatted Computed Columns
-- Retrieve full order details including customer name, kitchen name, and delivery destination
SELECT 
    o.order_number,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    k.name AS kitchen_branch,
    o.order_status,
    o.total_amount,
    CONCAT(a.address_line1, ', ', a.city, ' - ', a.postal_code) AS destination,
    o.placed_at
FROM orders o
INNER JOIN customer c ON o.customer_id = c.customer_id
INNER JOIN users u ON c.customer_id = u.user_id
INNER JOIN kitchen k ON o.kitchen_id = k.kitchen_id
INNER JOIN address a ON o.delivery_address_id = a.address_id
WHERE o.order_status NOT IN ('CANCELLED')
ORDER BY o.placed_at DESC
LIMIT 10;

-- Query 2.3: Aggregation with GROUP BY and HAVING
-- Identify cloud kitchens with average order basket size exceeding 500 INR
SELECT 
    k.kitchen_id,
    k.name AS kitchen_name,
    k.city,
    COUNT(o.order_id) AS total_orders_fulfilled,
    ROUND(AVG(o.total_amount), 2) AS average_order_value,
    ROUND(SUM(o.total_amount), 2) AS total_gross_revenue
FROM kitchen k
INNER JOIN orders o ON k.kitchen_id = o.kitchen_id
WHERE o.order_status = 'DELIVERED'
GROUP BY k.kitchen_id, k.name, k.city
HAVING COUNT(o.order_id) >= 1 AND AVG(o.total_amount) > 500.00
ORDER BY total_gross_revenue DESC;

-- Query 2.4: Paginated Inventory Stock Level Lookup with Low Stock Flag
SELECT 
    i.inventory_id,
    k.name AS kitchen_name,
    ing.name AS ingredient_name,
    i.current_stock,
    i.reorder_level,
    ing.unit_of_measure,
    CASE 
        WHEN i.current_stock <= i.reorder_level THEN 'ALERT: REORDER REQUIRED'
        WHEN i.current_stock <= (i.reorder_level * 1.5) THEN 'WARNING: LOW'
        ELSE 'OPTIMAL'
    END AS stock_status
FROM inventory i
INNER JOIN kitchen k ON i.kitchen_id = k.kitchen_id
INNER JOIN ingredient ing ON i.ingredient_id = ing.ingredient_id
WHERE k.kitchen_id = 1
ORDER BY (i.current_stock - i.reorder_level) ASC
LIMIT 10 OFFSET 0;

-- ---------------------------------------------------------------------
-- SECTION 3: UPDATE OPERATIONS (State Changes & Integrity Updates)
-- ---------------------------------------------------------------------

-- Update 3.1: Kitchen Operational State Change (86 / Out-of-Stock Toggle)
UPDATE menu_item
SET 
    is_available = FALSE,
    updated_at = CURRENT_TIMESTAMP(6)
WHERE menu_item_id = @v_demo_item_id;

-- Update 3.2: Customer Profile Dietary Preference Update
UPDATE customer
SET 
    dietary_preference = 'VEGAN',
    loyalty_points = loyalty_points + 25,
    updated_at = CURRENT_TIMESTAMP(6)
WHERE customer_id = @v_demo_user_id;

-- Update 3.3: Price Adjustment with Percentage Surge across a Category
UPDATE menu_item
SET 
    base_price = ROUND(base_price * 1.05, 2),
    updated_at = CURRENT_TIMESTAMP(6)
WHERE kitchen_id = 1 
  AND category_id = 2 
  AND is_available = TRUE;

-- Update 3.4: Order Status Progression with Timestamp Validation
UPDATE orders
SET 
    order_status = 'PREPARING',
    updated_at = CURRENT_TIMESTAMP(6)
WHERE order_id = 1 
  AND order_status = 'CONFIRMED';

-- Update 3.5: Physical Inventory Restock Update
UPDATE inventory
SET 
    current_stock = current_stock + 15.500,
    last_restocked_at = CURRENT_TIMESTAMP(6),
    updated_at = CURRENT_TIMESTAMP(6)
WHERE kitchen_id = 1 
  AND ingredient_id = 1;

-- ---------------------------------------------------------------------
-- SECTION 4: DELETE OPERATIONS (Safe Deletions & Soft-Delete Standards)
-- ---------------------------------------------------------------------

-- Demonstration 4.1: Recommended Enterprise Soft-Delete Pattern
-- Deactivate user rather than deleting, preserving foreign key referential integrity
UPDATE users
SET 
    is_active = FALSE,
    updated_at = CURRENT_TIMESTAMP(6)
WHERE user_id = @v_demo_user_id;

-- Demonstration 4.2: Safe Hard Delete in a Rolled-back Sandbox Block
-- Demonstrates deleting a draft coupon without risking accidental production loss
START TRANSACTION;

-- Create temporary demonstration coupon
INSERT INTO coupon (
    code, description, discount_type, discount_value, 
    min_order_value, valid_from, valid_to, usage_limit_per_user, is_active
) VALUES (
    'TEMPDEMO99', 'Temporary test promotion', 'FLAT', 50.00, 
    200.00, NOW(), DATE_ADD(NOW(), INTERVAL 1 DAY), 1, FALSE
);

-- Delete the unreferenced temporary coupon
DELETE FROM coupon 
WHERE code = 'TEMPDEMO99';

-- Verify removal
SELECT COUNT(*) AS should_be_zero FROM coupon WHERE code = 'TEMPDEMO99';

-- Roll back to leave database clean
ROLLBACK;

-- ---------------------------------------------------------------------
-- SECTION 5: COMPLETE TRANSACTION FLOW (ACID Checkout Demonstration)
-- ---------------------------------------------------------------------
-- Demonstrates an atomic food ordering transaction:
-- 1. Create order record
-- 2. Insert order items
-- 3. Lock & verify inventory rows
-- 4. Deduct inventory stock & write inventory movement audit journal
-- 5. Record initial payment attempt
-- 6. Log status transition history
-- 7. Atomically COMMIT or ROLLBACK on failure
-- ---------------------------------------------------------------------

START TRANSACTION;

-- Step T1: Insert Order
INSERT INTO orders (
    order_number,
    customer_id,
    kitchen_id,
    delivery_address_id,
    order_status,
    subtotal_amount,
    discount_amount,
    tax_amount,
    delivery_fee,
    total_amount,
    special_instructions,
    estimated_delivery_time,
    placed_at
) VALUES (
    CONCAT('ORD-', DATE_FORMAT(NOW(), '%Y%m%d'), '-TEST01'),
    1,
    1,
    1,
    'PLACED',
    450.00,
    0.00,
    22.50,
    40.00,
    512.50,
    'Ring doorbell twice. Leave at front security.',
    DATE_ADD(NOW(), INTERVAL 35 MINUTE),
    NOW()
);

SET @v_new_order_id = LAST_INSERT_ID();

-- Step T2: Insert Order Item Line Snapshot
INSERT INTO order_item (
    order_id,
    menu_item_id,
    item_name_snapshot,
    unit_price_snapshot,
    quantity,
    subtotal_price,
    customization_notes
) VALUES (
    @v_new_order_id,
    1,
    'Truffle Mushroom Pizza',
    450.00,
    1,
    450.00,
    'Extra oregano, crispy crust'
);

-- Step T3: Lock and Update Inventory (Pessimistic concurrency lock)
SELECT current_stock 
FROM inventory 
WHERE kitchen_id = 1 AND ingredient_id = 1 
FOR UPDATE;

UPDATE inventory 
SET current_stock = current_stock - 0.250,
    updated_at = CURRENT_TIMESTAMP(6)
WHERE kitchen_id = 1 AND ingredient_id = 1;

-- Step T4: Record Audit Inventory Movement
INSERT INTO inventory_movement (
    kitchen_id,
    ingredient_id,
    movement_type,
    quantity_delta,
    unit_cost,
    reference_order_id,
    notes,
    recorded_by_user_id
) VALUES (
    1,
    1,
    'CONSUMPTION',
    -0.250,
    120.00,
    @v_new_order_id,
    'Auto-deducted for order preparation',
    1
);

-- Step T5: Record Payment Attempt
INSERT INTO payment (
    order_id,
    payment_method,
    payment_status,
    transaction_reference,
    gateway_name,
    amount,
    currency,
    initiated_at
) VALUES (
    @v_new_order_id,
    'UPI',
    'PENDING',
    CONCAT('TXN-DEMO-', UNIX_TIMESTAMP()),
    'Razorpay',
    512.50,
    'INR',
    NOW()
);

-- Step T6: Record Status Audit History
INSERT INTO order_status_history (
    order_id,
    previous_status,
    new_status,
    changed_by_user_id,
    notes
) VALUES (
    @v_new_order_id,
    NULL,
    'PLACED',
    1,
    'Customer submitted order through web portal'
);

-- For testing demonstration purposes, we roll back to prevent polluting production data:
ROLLBACK;

-- End of DML operations demonstration
