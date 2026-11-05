-- =====================================================================
-- GOURMETCLOUD: CLOUD KITCHEN MANAGEMENT & FOOD ORDERING PLATFORM
-- Advanced Database Programmability Objects (Requirement O)
-- Target RDBMS: MySQL 8.0+ (InnoDB)
-- =====================================================================
-- Table of Contents:
--   1. STORED PROCEDURES (3 Business Procedures)
--   2. STORED FUNCTIONS (2 Deterministic Functions)
--   3. TRIGGERS (Existing Audit & New Administrative Audits)
--   4. COMMON TABLE EXPRESSIONS (3 Analytical CTEs)
--   5. VERIFICATION & SAMPLE EXECUTION HARNESS
--
-- Note: Do not execute CREATE PROCEDURE / FUNCTION / TRIGGER directly 
-- on live production databases without explicit change-window approval.
-- =====================================================================

DELIMITER $$

-- =====================================================================
-- SECTION 1: STORED PROCEDURES
-- =====================================================================

-- ---------------------------------------------------------------------
-- Procedure 1: sp_get_customer_order_summary
-- Purpose: Return lifetime ordering metrics for a specific customer.
-- Parameters:
--   IN p_customer_id BIGINT UNSIGNED
-- Result Set:
--   total_orders, completed_orders, cancelled_orders, total_spent, 
--   avg_order_value, first_order_date, last_order_date
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_customer_order_summary$$

CREATE PROCEDURE sp_get_customer_order_summary(
    IN p_customer_id BIGINT UNSIGNED
)
BEGIN
    -- Declare local handler for not found / invalid parameters
    IF p_customer_id IS NULL OR p_customer_id = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Validation Error: Customer ID cannot be NULL or zero.';
    END IF;

    SELECT 
        c.customer_id,
        CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
        u.email,
        c.loyalty_points,
        COUNT(o.order_id) AS total_orders,
        COUNT(CASE WHEN o.order_status = 'DELIVERED' THEN 1 END) AS completed_orders,
        COUNT(CASE WHEN o.order_status = 'CANCELLED' THEN 1 END) AS cancelled_orders,
        COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.total_amount ELSE 0 END), 2), 0.00) AS total_spent,
        COALESCE(ROUND(AVG(CASE WHEN o.order_status = 'DELIVERED' THEN o.total_amount ELSE NULL END), 2), 0.00) AS avg_order_value,
        MIN(o.placed_at) AS first_order_date,
        MAX(o.placed_at) AS last_order_date
    FROM customer c
    INNER JOIN users u ON c.customer_id = u.user_id
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE c.customer_id = p_customer_id
    GROUP BY c.customer_id, u.first_name, u.last_name, u.email, c.loyalty_points;
END$$


-- ---------------------------------------------------------------------
-- Procedure 2: sp_get_kitchen_sales_report
-- Purpose: Generate an aggregate financial and volume sales report for a
--          kitchen branch within an inclusive date window.
-- Parameters:
--   IN p_kitchen_id BIGINT UNSIGNED
--   IN p_start_date DATETIME
--   IN p_end_date   DATETIME
-- Result Set:
--   kitchen_id, kitchen_name, orders_count, gross_subtotal, total_discounts,
--   total_taxes, total_delivery_fees, net_revenue, avg_ticket_size
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_kitchen_sales_report$$

CREATE PROCEDURE sp_get_kitchen_sales_report(
    IN p_kitchen_id BIGINT UNSIGNED,
    IN p_start_date DATETIME,
    IN p_end_date   DATETIME
)
BEGIN
    -- Validate date arguments
    IF p_start_date IS NULL OR p_end_date IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Validation Error: Start date and end date must both be provided.';
    END IF;

    IF p_start_date > p_end_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Validation Error: Start date cannot be after end date.';
    END IF;

    SELECT 
        k.kitchen_id,
        k.name AS kitchen_name,
        k.branch_code,
        k.city,
        p_start_date AS report_start,
        p_end_date AS report_end,
        COUNT(o.order_id) AS total_orders,
        COUNT(CASE WHEN o.order_status = 'DELIVERED' THEN 1 END) AS delivered_orders,
        COUNT(CASE WHEN o.order_status = 'CANCELLED' THEN 1 END) AS cancelled_orders,
        COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.subtotal_amount ELSE 0 END), 2), 0.00) AS gross_subtotal,
        COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.discount_amount ELSE 0 END), 2), 0.00) AS total_discounts,
        COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.tax_amount ELSE 0 END), 2), 0.00) AS total_taxes,
        COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.delivery_fee ELSE 0 END), 2), 0.00) AS total_delivery_fees,
        COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.total_amount ELSE 0 END), 2), 0.00) AS net_revenue,
        COALESCE(ROUND(AVG(CASE WHEN o.order_status = 'DELIVERED' THEN o.total_amount ELSE NULL END), 2), 0.00) AS avg_ticket_size
    FROM kitchen k
    LEFT JOIN orders o ON k.kitchen_id = o.kitchen_id 
        AND o.placed_at >= p_start_date 
        AND o.placed_at <= p_end_date
    WHERE k.kitchen_id = p_kitchen_id
    GROUP BY k.kitchen_id, k.name, k.branch_code, k.city;
END$$


-- ---------------------------------------------------------------------
-- Procedure 3: sp_get_low_stock_inventory
-- Purpose: Extract all raw ingredient materials for a given kitchen branch
--          that have fallen at or below their assigned reorder threshold.
-- Parameters:
--   IN p_kitchen_id BIGINT UNSIGNED
-- Result Set:
--   inventory_id, ingredient_id, ingredient_name, category, current_stock,
--   reorder_level, unit_of_measure, deficit_amount, urgency_level
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_low_stock_inventory$$

CREATE PROCEDURE sp_get_low_stock_inventory(
    IN p_kitchen_id BIGINT UNSIGNED
)
BEGIN
    IF p_kitchen_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Validation Error: Kitchen ID is mandatory.';
    END IF;

    SELECT 
        i.inventory_id,
        k.name AS kitchen_name,
        ing.ingredient_id,
        ing.name AS ingredient_name,
        ing.category AS ingredient_category,
        i.current_stock,
        i.reorder_level,
        ing.unit_of_measure,
        ROUND(i.reorder_level - i.current_stock, 3) AS deficit_amount,
        CASE 
            WHEN i.current_stock = 0 THEN 'CRITICAL (OUT OF STOCK)'
            WHEN i.current_stock <= (i.reorder_level * 0.5) THEN 'HIGH (IMMEDIATE REORDER)'
            ELSE 'MEDIUM (REORDER THRESHOLD REACHED)'
        END AS urgency_level,
        i.last_restocked_at
    FROM inventory i
    INNER JOIN kitchen k ON i.kitchen_id = k.kitchen_id
    INNER JOIN ingredient ing ON i.ingredient_id = ing.ingredient_id
    WHERE i.kitchen_id = p_kitchen_id
      AND i.current_stock <= i.reorder_level
    ORDER BY (i.current_stock / NULLIF(i.reorder_level, 0)) ASC;
END$$


-- =====================================================================
-- SECTION 2: STORED FUNCTIONS
-- =====================================================================

-- ---------------------------------------------------------------------
-- Function 1: fn_calculate_order_total
-- Purpose: Compute the total billable amount for an order from its line-items,
--          incorporating subtotal, applicable coupon discount, tax (5%), and delivery fee.
-- Returns: DECIMAL(10, 2)
-- ---------------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_calculate_order_total$$

CREATE FUNCTION fn_calculate_order_total(
    p_order_id BIGINT UNSIGNED
) 
RETURNS DECIMAL(10, 2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_subtotal DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_discount DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_tax DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_delivery_fee DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_total DECIMAL(10, 2) DEFAULT 0.00;

    -- Compute raw subtotal from snapshot line items
    SELECT COALESCE(SUM(subtotal_price), 0.00)
    INTO v_subtotal
    FROM order_item
    WHERE order_id = p_order_id;

    -- Fetch recorded discount and delivery fee from orders table if present
    SELECT 
        COALESCE(discount_amount, 0.00),
        COALESCE(delivery_fee, 0.00)
    INTO v_discount, v_delivery_fee
    FROM orders
    WHERE order_id = p_order_id;

    -- Standard 5% GST tax rate applied to net food subtotal
    SET v_tax = ROUND(GREATEST(v_subtotal - v_discount, 0.00) * 0.05, 2);

    -- Calculate total
    SET v_total = ROUND(GREATEST(v_subtotal - v_discount, 0.00) + v_tax + v_delivery_fee, 2);

    RETURN v_total;
END$$


-- ---------------------------------------------------------------------
-- Function 2: fn_get_customer_loyalty_tier
-- Purpose: Evaluates a customer's accumulated loyalty points and returns
--          their VIP tier ('PLATINUM', 'GOLD', 'SILVER', or 'BRONZE').
-- Returns: VARCHAR(20)
-- ---------------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_get_customer_loyalty_tier$$

CREATE FUNCTION fn_get_customer_loyalty_tier(
    p_customer_id BIGINT UNSIGNED
) 
RETURNS VARCHAR(20)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_points INT DEFAULT 0;
    DECLARE v_tier VARCHAR(20);

    -- Retrieve points
    SELECT COALESCE(loyalty_points, 0)
    INTO v_points
    FROM customer
    WHERE customer_id = p_customer_id;

    -- Evaluate tier thresholds
    IF v_points >= 1000 THEN
        SET v_tier = 'PLATINUM';
    ELSEIF v_points >= 500 THEN
        SET v_tier = 'GOLD';
    ELSEIF v_points >= 200 THEN
        SET v_tier = 'SILVER';
    ELSE
        SET v_tier = 'BRONZE';
    END IF;

    RETURN v_tier;
END$$


-- =====================================================================
-- SECTION 3: TRIGGERS
-- =====================================================================

-- ---------------------------------------------------------------------
-- Existing Business Integrity Trigger (Preserved):
-- trg_order_item_kitchen_match
-- Purpose: Validates that an ordered dish belongs to the fulfilling kitchen.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_order_item_kitchen_match$$

CREATE TRIGGER trg_order_item_kitchen_match
BEFORE INSERT ON order_item
FOR EACH ROW
BEGIN
    DECLARE v_order_kitchen_id BIGINT UNSIGNED;
    DECLARE v_item_kitchen_id BIGINT UNSIGNED;

    SELECT kitchen_id INTO v_order_kitchen_id 
    FROM orders 
    WHERE order_id = NEW.order_id;

    SELECT kitchen_id INTO v_item_kitchen_id 
    FROM menu_item 
    WHERE menu_item_id = NEW.menu_item_id;

    IF v_order_kitchen_id IS NOT NULL AND v_item_kitchen_id IS NOT NULL THEN
        IF v_order_kitchen_id <> v_item_kitchen_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Integrity Violation: Menu item does not belong to the kitchen fulfilling this order.';
        END IF;
    END IF;
END$$


-- ---------------------------------------------------------------------
-- Trigger 2: trg_audit_menu_item_price_change
-- Purpose: Automatically writes an entry into admin_audit_log whenever
--          a menu item's base price or availability is altered.
-- Note: Dynamically resolves an administrative actor_user_id from users table.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_audit_menu_item_price_change$$

CREATE TRIGGER trg_audit_menu_item_price_change
AFTER UPDATE ON menu_item
FOR EACH ROW
BEGIN
    DECLARE v_actor_id BIGINT UNSIGNED;

    -- Only log when price or availability changes
    IF OLD.base_price <> NEW.base_price OR OLD.is_available <> NEW.is_available THEN
        -- Safely resolve an active administrative user ID for the audit journal
        SELECT user_id INTO v_actor_id 
        FROM users 
        WHERE role = 'ADMIN' AND is_active = TRUE 
        ORDER BY user_id ASC 
        LIMIT 1;

        IF v_actor_id IS NULL THEN
            SELECT user_id INTO v_actor_id FROM users ORDER BY user_id ASC LIMIT 1;
        END IF;

        IF v_actor_id IS NOT NULL THEN
            INSERT INTO admin_audit_log (
                actor_user_id,
                action,
                entity_type,
                entity_id,
                created_at
            ) VALUES (
                v_actor_id,
                CASE 
                    WHEN OLD.base_price <> NEW.base_price AND OLD.is_available <> NEW.is_available THEN 'MENU_PRICE_AND_AVAILABILITY_CHANGE'
                    WHEN OLD.base_price <> NEW.base_price THEN 'MENU_PRICE_CHANGE'
                    ELSE 'MENU_AVAILABILITY_CHANGE'
                END,
                'menu_item',
                NEW.menu_item_id,
                CURRENT_TIMESTAMP(6)
            );
        END IF;
    END IF;
END$$


-- ---------------------------------------------------------------------
-- Trigger 3: trg_order_status_history_auto_log
-- Purpose: Automatically records every order status modification in the
--          order_status_history journal table if not already explicitly captured.
-- Note: Dynamically resolves the user who authorized the transition.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_order_status_history_auto_log$$

CREATE TRIGGER trg_order_status_history_auto_log
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    DECLARE v_actor_id BIGINT UNSIGNED;

    IF OLD.order_status <> NEW.order_status THEN
        -- Resolve an administrative or system actor for background transitions
        SELECT user_id INTO v_actor_id 
        FROM users 
        WHERE role = 'ADMIN' AND is_active = TRUE 
        ORDER BY user_id ASC 
        LIMIT 1;

        IF v_actor_id IS NULL THEN
            SELECT user_id INTO v_actor_id FROM users ORDER BY user_id ASC LIMIT 1;
        END IF;

        IF v_actor_id IS NOT NULL THEN
            INSERT INTO order_status_history (
                order_id,
                previous_status,
                new_status,
                changed_by_user_id,
                notes,
                created_at
            ) VALUES (
                NEW.order_id,
                OLD.order_status,
                NEW.order_status,
                v_actor_id,
                CONCAT('Automatic status transition from ', OLD.order_status, ' to ', NEW.order_status),
                CURRENT_TIMESTAMP(6)
            );
        END IF;
    END IF;
END$$

DELIMITER ;


-- =====================================================================
-- SECTION 4: COMMON TABLE EXPRESSIONS (CTEs)
-- =====================================================================

-- ---------------------------------------------------------------------
-- CTE 1: Daily Sales Summary with Window Cumulative Running Total
-- Purpose: Compute daily delivered revenue alongside cumulative 30-day running total.
-- ---------------------------------------------------------------------
WITH daily_sales AS (
    SELECT 
        DATE(placed_at) AS sales_date,
        COUNT(order_id) AS orders_count,
        ROUND(SUM(total_amount), 2) AS daily_revenue
    FROM orders
    WHERE order_status = 'DELIVERED'
    GROUP BY DATE(placed_at)
)
SELECT 
    sales_date,
    orders_count,
    daily_revenue,
    ROUND(SUM(daily_revenue) OVER (ORDER BY sales_date ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_running_revenue,
    ROUND(AVG(daily_revenue) OVER (ORDER BY sales_date ASC ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS rolling_7day_avg_revenue
FROM daily_sales
ORDER BY sales_date DESC;


-- ---------------------------------------------------------------------
-- CTE 2: Kitchen Operational Performance Benchmark
-- Purpose: Rank kitchens by volume, on-time fulfillment, and rating score.
-- ---------------------------------------------------------------------
WITH kitchen_metrics AS (
    SELECT 
        k.kitchen_id,
        k.name AS kitchen_name,
        k.city,
        COUNT(o.order_id) AS total_fulfilled_orders,
        COALESCE(ROUND(SUM(o.total_amount), 2), 0.00) AS total_revenue,
        COALESCE(ROUND(AVG(r.rating), 2), 0.00) AS avg_rating
    FROM kitchen k
    LEFT JOIN orders o ON k.kitchen_id = o.kitchen_id AND o.order_status = 'DELIVERED'
    LEFT JOIN review r ON k.kitchen_id = r.kitchen_id
    GROUP BY k.kitchen_id, k.name, k.city
)
SELECT 
    kitchen_id,
    kitchen_name,
    city,
    total_fulfilled_orders,
    total_revenue,
    avg_rating,
    DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY avg_rating DESC) AS quality_rank
FROM kitchen_metrics
ORDER BY revenue_rank ASC;


-- ---------------------------------------------------------------------
-- CTE 3: Customer RFM (Recency, Frequency, Monetary) Segmentation
-- Purpose: Segment customer base into VIP, Active, and Churn Risk tiers.
-- ---------------------------------------------------------------------
WITH customer_rfm AS (
    SELECT 
        c.customer_id,
        CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
        DATEDIFF(CURRENT_DATE(), MAX(DATE(o.placed_at))) AS days_since_last_order,
        COUNT(o.order_id) AS order_frequency,
        COALESCE(ROUND(SUM(o.total_amount), 2), 0.00) AS monetary_value
    FROM customer c
    INNER JOIN users u ON c.customer_id = u.user_id
    LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status = 'DELIVERED'
    GROUP BY c.customer_id, u.first_name, u.last_name
)
SELECT 
    customer_id,
    customer_name,
    days_since_last_order,
    order_frequency,
    monetary_value,
    CASE 
        WHEN order_frequency >= 3 AND monetary_value >= 1000.00 THEN 'VIP PLATINUM'
        WHEN order_frequency >= 1 AND days_since_last_order <= 30 THEN 'ACTIVE'
        WHEN days_since_last_order > 30 THEN 'CHURN RISK'
        ELSE 'NEW / UNCONVERTED'
    END AS customer_segment
FROM customer_rfm
ORDER BY monetary_value DESC, order_frequency DESC;


-- =====================================================================
-- SECTION 5: VERIFICATION & SAMPLE EXECUTION STATEMENTS
-- =====================================================================
-- The following sample statements demonstrate how each stored object is invoked:
--
-- 1. Call Stored Procedures:
--    CALL sp_get_customer_order_summary(1);
--    CALL sp_get_kitchen_sales_report(1, '2026-01-01 00:00:00', '2026-12-31 23:59:59');
--    CALL sp_get_low_stock_inventory(1);
--
-- 2. Call Stored Functions:
--    SELECT fn_calculate_order_total(1) AS recalculated_total;
--    SELECT c.customer_id, fn_get_customer_loyalty_tier(c.customer_id) AS tier FROM customer c;
-- =====================================================================
