-- =====================================================================
-- GOURMETCLOUD: CLOUD KITCHEN MANAGEMENT & FOOD ORDERING PLATFORM
-- Advanced Academic & Analytical SQL Queries (Requirement N)
-- Target RDBMS: MySQL 8.0+ (InnoDB)
-- =====================================================================
-- Table Name Convention Reminder:
-- - All tables use the authoritative schema definitions:
--   orders, order_item, menu_item, payment, address, customer, users,
--   kitchen, ingredient, inventory, inventory_movement, delivery, review,
--   coupon, coupon_usage, cuisine, category, admin_audit_log.
-- =====================================================================

-- =====================================================================
-- PART A: RELATIONAL JOIN QUERIES
-- =====================================================================

-- ---------------------------------------------------------------------
-- Query A.1: INNER JOIN
-- Title: Active Cloud Kitchen Branches and Their Assigned Staff Roster
-- Purpose: Retrieve kitchen operational contact details alongside employed staff,
--          filtering only for active staff currently assigned to open branches.
-- Explanation:
--   - Performs an INNER JOIN between kitchen, staff, and users.
--   - Ensures that only users who have valid staff records and active accounts
--     in an active kitchen are retrieved.
-- Expected Output:
--   - branch_code, kitchen_name, staff_name, staff_role, shift_timing, hired_date.
-- ---------------------------------------------------------------------
SELECT 
    k.branch_code,
    k.name AS kitchen_name,
    CONCAT(u.first_name, ' ', u.last_name) AS staff_name,
    s.staff_role,
    s.shift_timing,
    s.hired_date
FROM kitchen k
INNER JOIN staff s ON k.kitchen_id = s.kitchen_id
INNER JOIN users u ON s.staff_id = u.user_id
WHERE k.operating_status = 'ACTIVE'
  AND u.is_active = TRUE
ORDER BY k.branch_code ASC, s.staff_role ASC;


-- ---------------------------------------------------------------------
-- Query A.2: LEFT JOIN
-- Title: Complete Menu Catalog with Customer Review Aggregations
-- Purpose: Display every menu item in the catalog along with its average customer
--          rating and review count, ensuring items with zero reviews are not omitted.
-- Explanation:
--   - LEFT JOIN connects menu_item to order_item, orders, and review.
--   - Dishes with no orders or reviews return NULL, converted to 0.0 using COALESCE.
-- Expected Output:
--   - menu_item_id, item_name, base_price, review_count, average_rating.
-- ---------------------------------------------------------------------
SELECT 
    m.menu_item_id,
    m.name AS item_name,
    m.base_price,
    c.name AS category_name,
    COUNT(r.review_id) AS total_reviews,
    COALESCE(ROUND(AVG(r.rating), 2), 0.00) AS average_rating
FROM menu_item m
INNER JOIN category c ON m.category_id = c.category_id
LEFT JOIN order_item oi ON m.menu_item_id = oi.menu_item_id
LEFT JOIN orders o ON oi.order_id = o.order_id AND o.order_status = 'DELIVERED'
LEFT JOIN review r ON o.order_id = r.order_id
GROUP BY m.menu_item_id, m.name, m.base_price, c.name
ORDER BY average_rating DESC, total_reviews DESC;


-- ---------------------------------------------------------------------
-- Query A.3: RIGHT JOIN
-- Title: Delivery Driver Roster with Dispatch Assignment Coverage
-- Purpose: Inspect all registered delivery personnel and evaluate their fulfillment
--          activity, highlighting any couriers who have never received an assignment.
-- Explanation:
--   - Performs a RIGHT JOIN from delivery to delivery_person and users.
--   - Ensures every delivery courier is represented even if delivery records are empty.
-- Expected Output:
--   - driver_name, vehicle_type, vehicle_number, current_status, total_dispatches, completed_deliveries.
-- ---------------------------------------------------------------------
SELECT 
    CONCAT(u.first_name, ' ', u.last_name) AS driver_name,
    dp.vehicle_type,
    dp.vehicle_number,
    dp.current_status,
    COUNT(d.delivery_id) AS total_assigned_deliveries,
    COUNT(CASE WHEN d.delivery_status = 'DELIVERED' THEN 1 END) AS successful_deliveries
FROM delivery d
RIGHT JOIN delivery_person dp ON d.delivery_person_id = dp.delivery_person_id
INNER JOIN users u ON dp.delivery_person_id = u.user_id
GROUP BY dp.delivery_person_id, u.first_name, u.last_name, dp.vehicle_type, dp.vehicle_number, dp.current_status
ORDER BY total_assigned_deliveries DESC;


-- ---------------------------------------------------------------------
-- Query A.4: Multi-Table JOIN (7 Tables)
-- Title: Comprehensive Order Fulfillment & Logistics Audit Journal
-- Purpose: Traverse the complete lifecycle of delivered orders linking customer,
--          kitchen, destination address, line items, settlement, courier, and review.
-- Explanation:
--   - Joins 7 core tables: orders -> customer/users -> kitchen -> address -> 
--     payment -> delivery -> delivery_person.
-- Expected Output:
--   - order_number, customer_name, kitchen_name, recipient_phone, payment_method, 
--     courier_name, total_amount, order_status.
-- ---------------------------------------------------------------------
SELECT 
    o.order_number,
    CONCAT(u_cust.first_name, ' ', u_cust.last_name) AS customer_name,
    k.name AS kitchen_branch,
    a.city AS delivery_city,
    p.payment_method,
    p.payment_status,
    CONCAT(u_drv.first_name, ' ', u_drv.last_name) AS delivery_courier,
    d.delivery_status,
    o.total_amount,
    o.placed_at
FROM orders o
INNER JOIN customer c ON o.customer_id = c.customer_id
INNER JOIN users u_cust ON c.customer_id = u_cust.user_id
INNER JOIN kitchen k ON o.kitchen_id = k.kitchen_id
INNER JOIN address a ON o.delivery_address_id = a.address_id
LEFT JOIN payment p ON o.order_id = p.order_id AND p.payment_status = 'SUCCESS'
LEFT JOIN delivery d ON o.order_id = d.order_id
LEFT JOIN delivery_person dp ON d.delivery_person_id = dp.delivery_person_id
LEFT JOIN users u_drv ON dp.delivery_person_id = u_drv.user_id
ORDER BY o.placed_at DESC;


-- ---------------------------------------------------------------------
-- Query A.5: Aggregate JOIN with GROUP BY and HAVING
-- Title: High-Performance Kitchen Branches by Gross Volume and Order Count
-- Purpose: Identify dark kitchen branches that have completed at least 2 delivered
--          orders with an average ticket size greater than 350.00 INR.
-- Explanation:
--   - Aggregates orders fulfilled per kitchen branch.
--   - Applies HAVING filter on aggregate functions COUNT() and AVG().
-- Expected Output:
--   - kitchen_id, branch_name, city, completed_orders, total_revenue, avg_order_value.
-- ---------------------------------------------------------------------
SELECT 
    k.kitchen_id,
    k.name AS branch_name,
    k.city,
    COUNT(o.order_id) AS completed_orders,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value
FROM kitchen k
INNER JOIN orders o ON k.kitchen_id = o.kitchen_id
WHERE o.order_status = 'DELIVERED'
GROUP BY k.kitchen_id, k.name, k.city
HAVING COUNT(o.order_id) >= 2 
   AND AVG(o.total_amount) > 350.00
ORDER BY total_revenue DESC;


-- =====================================================================
-- PART B: NESTED SUBQUERIES (WHERE, FROM, SELECT)
-- =====================================================================

-- ---------------------------------------------------------------------
-- Query B.1: Subquery in WHERE
-- Title: Customers Who Have Never Placed an Order (Unconverted Registrations)
-- Purpose: Target marketing campaigns to registered customers without purchases.
-- Explanation:
--   - Uses NOT IN with an independent nested subquery on orders.
-- Expected Output:
--   - customer_id, full_name, email, phone_number, registered_date.
-- ---------------------------------------------------------------------
SELECT 
    c.customer_id,
    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
    u.email,
    u.phone_number,
    c.created_at AS registered_date
FROM customer c
INNER JOIN users u ON c.customer_id = u.user_id
WHERE c.customer_id NOT IN (
    SELECT DISTINCT customer_id 
    FROM orders 
    WHERE customer_id IS NOT NULL
)
ORDER BY c.created_at DESC;


-- ---------------------------------------------------------------------
-- Query B.2: Subquery in FROM (Derived Table)
-- Title: Category Sales Summary with Basket Contribution Metrics
-- Purpose: Aggregate item sales within an inline derived table, then calculate
--          overall proportion across categories.
-- Explanation:
--   - The subquery `item_aggregates` summarizes sales per menu item.
--   - The outer query groups by category to produce consolidated metrics.
-- Expected Output:
--   - category_name, items_sold_count, total_category_revenue.
-- ---------------------------------------------------------------------
SELECT 
    cat_summary.category_name,
    SUM(cat_summary.total_quantity_sold) AS total_units_sold,
    ROUND(SUM(cat_summary.total_item_revenue), 2) AS gross_category_revenue
FROM (
    SELECT 
        c.name AS category_name,
        mi.menu_item_id,
        COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
        COALESCE(SUM(oi.subtotal_price), 0.00) AS total_item_revenue
    FROM category c
    INNER JOIN menu_item mi ON c.category_id = mi.category_id
    LEFT JOIN order_item oi ON mi.menu_item_id = oi.menu_item_id
    GROUP BY c.name, mi.menu_item_id
) AS cat_summary
GROUP BY cat_summary.category_name
ORDER BY gross_category_revenue DESC;


-- ---------------------------------------------------------------------
-- Query B.3: Subquery in SELECT (Scalar Subquery)
-- Title: Menu Item Pricing Relative to Global Catalog Average Price
-- Purpose: Compare each menu item's base price against the system-wide average.
-- Explanation:
--   - Computes `(SELECT AVG(base_price) FROM menu_item)` as a scalar subquery.
-- Expected Output:
--   - menu_item_id, item_name, base_price, global_avg_price, price_variance.
-- ---------------------------------------------------------------------
SELECT 
    m.menu_item_id,
    m.name AS item_name,
    m.base_price,
    ROUND((SELECT AVG(base_price) FROM menu_item WHERE is_available = TRUE), 2) AS global_avg_price,
    ROUND(m.base_price - (SELECT AVG(base_price) FROM menu_item WHERE is_available = TRUE), 2) AS price_variance,
    CASE 
        WHEN m.base_price > (SELECT AVG(base_price) FROM menu_item WHERE is_available = TRUE) THEN 'PREMIUM'
        ELSE 'STANDARD'
    END AS price_tier
FROM menu_item m
WHERE m.is_available = TRUE
ORDER BY m.base_price DESC;


-- =====================================================================
-- PART C: CORRELATED SUBQUERIES (EXISTS, NOT EXISTS & Aggregations)
-- =====================================================================

-- ---------------------------------------------------------------------
-- Query C.1: Correlated Subquery with Comparison
-- Title: VIP Customers Whose Order Count Exceeds the Platform Average
-- Purpose: Identify frequent shoppers placing more orders than the average customer.
-- Explanation:
--   - Inner subquery computes the global average orders per customer.
--   - Outer query correlates customer order counts against that threshold.
-- Expected Output:
--   - customer_id, customer_name, order_count, total_spend.
-- ---------------------------------------------------------------------
SELECT 
    c.customer_id,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    COUNT(o.order_id) AS customer_order_count,
    ROUND(SUM(o.total_amount), 2) AS total_spend
FROM customer c
INNER JOIN users u ON c.customer_id = u.user_id
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'DELIVERED'
GROUP BY c.customer_id, u.first_name, u.last_name
HAVING COUNT(o.order_id) > (
    SELECT AVG(cust_orders.cnt) 
    FROM (
        SELECT COUNT(order_id) AS cnt 
        FROM orders 
        WHERE order_status = 'DELIVERED' 
        GROUP BY customer_id
    ) AS cust_orders
)
ORDER BY customer_order_count DESC, total_spend DESC;


-- ---------------------------------------------------------------------
-- Query C.2: Correlated Subquery across Categories
-- Title: Menu Items Priced Above the Average Price of Their Own Category
-- Purpose: Identify premium specialty offerings within each specific course/category.
-- Explanation:
--   - The subquery correlates `category_id` from the outer menu_item row (`m1.category_id = m2.category_id`).
-- Expected Output:
--   - category_name, item_name, base_price, category_avg_price, premium_markup.
-- ---------------------------------------------------------------------
SELECT 
    c.name AS category_name,
    m1.name AS item_name,
    m1.base_price,
    ROUND((
        SELECT AVG(m2.base_price) 
        FROM menu_item m2 
        WHERE m2.category_id = m1.category_id
    ), 2) AS category_avg_price,
    ROUND(m1.base_price - (
        SELECT AVG(m2.base_price) 
        FROM menu_item m2 
        WHERE m2.category_id = m1.category_id
    ), 2) AS premium_markup
FROM menu_item m1
INNER JOIN category c ON m1.category_id = c.category_id
WHERE m1.base_price > (
    SELECT AVG(m2.base_price) 
    FROM menu_item m2 
    WHERE m2.category_id = m1.category_id
)
ORDER BY c.name ASC, premium_markup DESC;


-- ---------------------------------------------------------------------
-- Query C.3: Correlated Subquery with Kitchen Branch Revenue
-- Title: Kitchen Branches Outperforming the System-Wide Average Branch Revenue
-- Purpose: Isolate flagship dark kitchen locations generating above-average revenue.
-- Explanation:
--   - Calculates total revenue for kitchen `k1`, comparing it with average branch revenue.
-- Expected Output:
--   - kitchen_id, branch_name, city, kitchen_revenue, platform_avg_kitchen_revenue.
-- ---------------------------------------------------------------------
SELECT 
    k1.kitchen_id,
    k1.name AS branch_name,
    k1.city,
    ROUND(SUM(o1.total_amount), 2) AS branch_revenue
FROM kitchen k1
INNER JOIN orders o1 ON k1.kitchen_id = o1.kitchen_id
WHERE o1.order_status = 'DELIVERED'
GROUP BY k1.kitchen_id, k1.name, k1.city
HAVING SUM(o1.total_amount) > (
    SELECT AVG(branch_totals.rev)
    FROM (
        SELECT SUM(o2.total_amount) AS rev
        FROM orders o2
        WHERE o2.order_status = 'DELIVERED'
        GROUP BY o2.kitchen_id
    ) AS branch_totals
)
ORDER BY branch_revenue DESC;


-- ---------------------------------------------------------------------
-- Query C.4: Correlated Subquery with EXISTS
-- Title: Cloud Kitchens with Imminent Inventory Stockouts
-- Purpose: Find kitchens that have at least one ingredient where stock is at or below reorder level.
-- Explanation:
--   - Uses EXISTS with correlation to `i.kitchen_id = k.kitchen_id`.
-- Expected Output:
--   - kitchen_id, name, contact_phone, city.
-- ---------------------------------------------------------------------
SELECT 
    k.kitchen_id,
    k.name AS kitchen_name,
    k.contact_phone,
    k.city
FROM kitchen k
WHERE EXISTS (
    SELECT 1 
    FROM inventory i 
    WHERE i.kitchen_id = k.kitchen_id 
      AND i.current_stock <= i.reorder_level
)
ORDER BY k.kitchen_id ASC;


-- ---------------------------------------------------------------------
-- Query C.5: Correlated Subquery with NOT EXISTS
-- Title: Available Menu Items Never Included in Any Placed Order
-- Purpose: Detect stagnant menu offerings that have never been purchased.
-- Explanation:
--   - Uses NOT EXISTS correlating `oi.menu_item_id = m.menu_item_id`.
-- Expected Output:
--   - menu_item_id, item_name, base_price, kitchen_name.
-- ---------------------------------------------------------------------
SELECT 
    m.menu_item_id,
    m.name AS item_name,
    m.base_price,
    k.name AS kitchen_name
FROM menu_item m
INNER JOIN kitchen k ON m.kitchen_id = k.kitchen_id
WHERE m.is_available = TRUE
  AND NOT EXISTS (
      SELECT 1 
      FROM order_item oi 
      WHERE oi.menu_item_id = m.menu_item_id
  )
ORDER BY m.base_price DESC;


-- =====================================================================
-- PART D: RECURSIVE QUERIES (MySQL 8 WITH RECURSIVE)
-- =====================================================================

-- ---------------------------------------------------------------------
-- Query D.1: Recursive CTE - Calendar Date Series with Left Join Sales Reporting
-- Title: Continuous 14-Day Daily Sales Summary (Zero-Sales Day Preservation)
-- Purpose: Generate a complete 14-day chronological sequence without gaps,
--          joining with actual order transactions to show daily revenue and order counts.
-- Explanation:
--   - Anchor member starts 13 days prior to current date.
--   - Recursive member increments date by 1 day up to CURRENT_DATE.
--   - Outer query LEFT JOINs with orders on DATE(placed_at).
-- Expected Output:
--   - sales_date, total_orders, gross_revenue, completed_orders.
-- ---------------------------------------------------------------------
WITH RECURSIVE calendar_days AS (
    -- Anchor Member: Starting date 13 days ago
    SELECT DATE_SUB(CURRENT_DATE(), INTERVAL 13 DAY) AS report_date
    UNION ALL
    -- Recursive Member: Increment by 1 day until today
    SELECT DATE_ADD(report_date, INTERVAL 1 DAY)
    FROM calendar_days
    WHERE report_date < CURRENT_DATE()
)
SELECT 
    cd.report_date AS sales_date,
    COUNT(o.order_id) AS total_orders_placed,
    COUNT(CASE WHEN o.order_status = 'DELIVERED' THEN 1 END) AS successful_orders,
    COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.total_amount ELSE 0 END), 2), 0.00) AS daily_revenue
FROM calendar_days cd
LEFT JOIN orders o ON DATE(o.placed_at) = cd.report_date
GROUP BY cd.report_date
ORDER BY cd.report_date ASC;


-- ---------------------------------------------------------------------
-- Query D.2: Recursive CTE - Sequence Generator for Reporting Buckets
-- Title: Hourly Operational Load Histogram (24-Hour Kitchen Activity Pattern)
-- Purpose: Generate 24 integer hour slots (0 to 23) and map order volume
--          to analyze peak lunch and dinner rush hours.
-- Explanation:
--   - Anchor generates hour 0.
--   - Recursive member increments up to hour 23.
--   - LEFT JOINs orders on EXTRACT(HOUR FROM placed_at).
-- Expected Output:
--   - hour_of_day, time_window, orders_count, total_sales.
-- ---------------------------------------------------------------------
WITH RECURSIVE hours_generator AS (
    SELECT 0 AS hour_slot
    UNION ALL
    SELECT hour_slot + 1 
    FROM hours_generator 
    WHERE hour_slot < 23
)
SELECT 
    hg.hour_slot,
    CONCAT(LPAD(hg.hour_slot, 2, '0'), ':00 - ', LPAD(hg.hour_slot, 2, '0'), ':59') AS time_window,
    COUNT(o.order_id) AS total_orders,
    COALESCE(ROUND(SUM(o.total_amount), 2), 0.00) AS hourly_sales_volume
FROM hours_generator hg
LEFT JOIN orders o ON EXTRACT(HOUR FROM o.placed_at) = hg.hour_slot
GROUP BY hg.hour_slot
ORDER BY hg.hour_slot ASC;


-- =====================================================================
-- PART E: BUSINESS-ORIENTED ANALYTICAL SQL
-- =====================================================================

-- ---------------------------------------------------------------------
-- Query E.1: Top-Selling Food Offerings with Window Function Ranking
-- Title: Dish Popularity Leaderboard by Volume and Gross Contribution
-- Purpose: Rank top-selling items using DENSE_RANK() based on total quantities ordered.
-- Expected Output:
--   - sales_rank, item_name, category_name, units_sold, gross_sales.
-- ---------------------------------------------------------------------
SELECT 
    DENSE_RANK() OVER (ORDER BY SUM(oi.quantity) DESC) AS sales_rank,
    mi.name AS item_name,
    c.name AS category_name,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.subtotal_price), 2) AS gross_sales,
    ROUND(AVG(oi.unit_price_snapshot), 2) AS avg_realized_price
FROM order_item oi
INNER JOIN menu_item mi ON oi.menu_item_id = mi.menu_item_id
INNER JOIN category c ON mi.category_id = c.category_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status <> 'CANCELLED'
GROUP BY mi.menu_item_id, mi.name, c.name
ORDER BY sales_rank ASC
LIMIT 10;


-- ---------------------------------------------------------------------
-- Query E.2: Monthly Cloud Kitchen Financial Performance
-- Title: Kitchen Branch Monthly P&L and Net Realization
-- Purpose: Track monthly revenue, discounts absorbed, and tax liabilities per kitchen.
-- Expected Output:
--   - sales_month, kitchen_name, orders_count, gross_subtotal, total_discounts, total_taxes, net_collected.
-- ---------------------------------------------------------------------
SELECT 
    DATE_FORMAT(o.placed_at, '%Y-%m') AS sales_month,
    k.name AS kitchen_name,
    COUNT(o.order_id) AS orders_count,
    ROUND(SUM(o.subtotal_amount), 2) AS gross_subtotal,
    ROUND(SUM(o.discount_amount), 2) AS total_discounts,
    ROUND(SUM(o.tax_amount), 2) AS total_taxes,
    ROUND(SUM(o.total_amount), 2) AS net_revenue
FROM orders o
INNER JOIN kitchen k ON o.kitchen_id = k.kitchen_id
WHERE o.order_status = 'DELIVERED'
GROUP BY DATE_FORMAT(o.placed_at, '%Y-%m'), k.name
ORDER BY sales_month DESC, net_revenue DESC;


-- ---------------------------------------------------------------------
-- Query E.3: Low Stock Alert with Reorder Urgency Index
-- Title: Warehouse Stock Replenishment Priority Matrix
-- Purpose: Identify ingredients critically low on stock across all kitchen branches,
--          calculating an urgency percentage score for warehouse dispatchers.
-- Expected Output:
--   - kitchen_name, ingredient_name, current_stock, reorder_level, unit, stock_ratio_pct, priority_status.
-- ---------------------------------------------------------------------
SELECT 
    k.name AS kitchen_name,
    ing.name AS ingredient_name,
    i.current_stock,
    i.reorder_level,
    ing.unit_of_measure,
    ROUND((i.current_stock / NULLIF(i.reorder_level, 0)) * 100, 1) AS stock_ratio_pct,
    CASE 
        WHEN i.current_stock = 0 THEN 'CRITICAL: OUT OF STOCK'
        WHEN i.current_stock <= (i.reorder_level * 0.5) THEN 'HIGH: IMMEDIATE REORDER'
        WHEN i.current_stock <= i.reorder_level THEN 'MEDIUM: REORDER DUE'
        ELSE 'LOW'
    END AS priority_status
FROM inventory i
INNER JOIN kitchen k ON i.kitchen_id = k.kitchen_id
INNER JOIN ingredient ing ON i.ingredient_id = ing.ingredient_id
WHERE i.current_stock <= (i.reorder_level * 1.2)
ORDER BY (i.current_stock / NULLIF(i.reorder_level, 0)) ASC;


-- ---------------------------------------------------------------------
-- Query E.4: Delivery Driver Performance & Transit Duration SLA
-- Title: Courier Delivery Turnaround & Rating Analytics
-- Purpose: Analyze delivery personnel performance, including average delivery minutes,
--          total completed dispatches, and customer quality ratings.
-- Expected Output:
--   - courier_name, vehicle_type, completed_deliveries, avg_delivery_minutes, driver_rating.
-- ---------------------------------------------------------------------
SELECT 
    CONCAT(u.first_name, ' ', u.last_name) AS courier_name,
    dp.vehicle_type,
    COUNT(d.delivery_id) AS completed_deliveries,
    COALESCE(ROUND(AVG(TIMESTAMPDIFF(MINUTE, d.picked_up_at, d.delivered_at)), 1), 0.0) AS avg_transit_minutes,
    dp.rating AS driver_rating
FROM delivery_person dp
INNER JOIN users u ON dp.delivery_person_id = u.user_id
INNER JOIN delivery d ON dp.delivery_person_id = d.delivery_person_id
WHERE d.delivery_status = 'DELIVERED'
GROUP BY dp.delivery_person_id, u.first_name, u.last_name, dp.vehicle_type, dp.rating
ORDER BY completed_deliveries DESC, avg_transit_minutes ASC;


-- ---------------------------------------------------------------------
-- Query E.5: Marketing Campaign & Coupon ROI Analysis
-- Title: Promotional Coupon Redemption and Value Discount Impact
-- Purpose: Measure the efficiency and gross order volume unlocked by each promo code.
-- Expected Output:
--   - coupon_code, discount_type, times_used, total_discount_granted, gross_revenue_generated.
-- ---------------------------------------------------------------------
SELECT 
    cp.code AS coupon_code,
    cp.discount_type,
    cp.discount_value,
    COUNT(cu.usage_id) AS times_redeemed,
    ROUND(SUM(cu.discount_applied), 2) AS total_discount_granted,
    ROUND(SUM(o.total_amount), 2) AS gross_order_volume_unlocked,
    ROUND(AVG(o.total_amount), 2) AS avg_basket_size_with_coupon
FROM coupon cp
INNER JOIN coupon_usage cu ON cp.coupon_id = cu.coupon_id
INNER JOIN orders o ON cu.order_id = o.order_id
GROUP BY cp.coupon_id, cp.code, cp.discount_type, cp.discount_value
ORDER BY total_discount_granted DESC;

-- End of advanced SQL queries demonstration
