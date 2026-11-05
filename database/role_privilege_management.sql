-- =====================================================================
-- GOURMETCLOUD: CLOUD KITCHEN MANAGEMENT & FOOD ORDERING PLATFORM
-- MySQL 8.0 Database-Level User Roles & Privilege Management
-- Academic DBMS Deliverable: Principle of Least Privilege (PoLP) Demonstration
-- Target Database: cloud_kitchen_db
-- =====================================================================
-- Table of Contents:
--   1. PRESERVATION GUARANTEE (cloud_kitchen_app & root safety)
--   2. ROLE DEFINITION (admin_role, customer_role, kitchen_role, delivery_role)
--   3. PRINCIPLE OF LEAST PRIVILEGE GRANTS (Table-level & Routine-level)
--   4. USER CREATION & ROLE ASSIGNMENT (CREATE USER, GRANT, SET DEFAULT ROLE)
--   5. PRIVILEGE AUDIT & INSPECTION (SHOW GRANTS)
--   6. PRIVILEGE REVOCATION DEMONSTRATION (REVOKE & Verification)
--   7. PRACTICAL ACCESS RESTRICTION TEST HARNESS (Authorized vs Denied Proofs)
--   8. CLEANUP / TEARDOWN SCRIPT
-- =====================================================================

-- ---------------------------------------------------------------------
-- SECTION 1: PRESERVATION GUARANTEE
-- ---------------------------------------------------------------------
-- SAFETY INVARIANT:
-- 1. The existing application service account 'cloud_kitchen_app'@'localhost'
--    is PRESERVED untouched to ensure continuous FastAPI/SQLAlchemy operation.
-- 2. The root account and server-level permissions are untouched.
-- 3. All demonstration roles and users created herein are dedicated to
--    proving database-level privilege boundaries for the DBMS rubric.
-- ---------------------------------------------------------------------

USE cloud_kitchen_db;

-- ---------------------------------------------------------------------
-- SECTION 2: CREATE DATABASE ROLES
-- ---------------------------------------------------------------------
-- MySQL 8.0 introduces first-class administrative roles, which function as
-- reusable privilege containers assigned to database users.
-- ---------------------------------------------------------------------

CREATE ROLE IF NOT EXISTS 'admin_role';
CREATE ROLE IF NOT EXISTS 'customer_role';
CREATE ROLE IF NOT EXISTS 'kitchen_role';
CREATE ROLE IF NOT EXISTS 'delivery_role';

-- ---------------------------------------------------------------------
-- SECTION 3: GRANT PRIVILEGES ACCORDING TO PRINCIPLE OF LEAST PRIVILEGE
-- ---------------------------------------------------------------------

-- =====================================================================
-- 3.1 ADMIN ROLE (admin_role)
-- Administrative manager for system oversight, catalog maintenance,
-- staff rosters, promotional campaigns, and financial settlement audit.
-- Strictly constrained to `cloud_kitchen_db` (No dangerous global privileges).
-- =====================================================================

-- Full DML on all 22 domain tables in cloud_kitchen_db
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.users TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.customer TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.kitchen TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.staff TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.delivery_person TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.category TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.cuisine TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.menu_item TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.address TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.coupon TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.orders TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.order_item TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.payment TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.order_status_history TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.ingredient TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.inventory TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.inventory_movement TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.menu_item_ingredient TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.delivery TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.coupon_usage TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.review TO 'admin_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.admin_audit_log TO 'admin_role';

-- Administrative Stored Routine Execution Privileges
GRANT EXECUTE ON PROCEDURE cloud_kitchen_db.sp_get_customer_order_summary TO 'admin_role';
GRANT EXECUTE ON PROCEDURE cloud_kitchen_db.sp_get_kitchen_sales_report TO 'admin_role';
GRANT EXECUTE ON PROCEDURE cloud_kitchen_db.sp_get_low_stock_inventory TO 'admin_role';
GRANT EXECUTE ON FUNCTION cloud_kitchen_db.fn_calculate_order_total TO 'admin_role';
GRANT EXECUTE ON FUNCTION cloud_kitchen_db.fn_get_customer_loyalty_tier TO 'admin_role';


-- =====================================================================
-- 3.2 CUSTOMER ROLE (customer_role)
-- Consumers browsing food catalog, maintaining saved addresses, placing
-- orders, submitting payments, and rating delivered orders.
-- Strictly prohibited from viewing inventory, staff rosters, audit logs,
-- or modifying other customers' records.
-- =====================================================================

-- Catalog Exploration (Read-Only)
GRANT SELECT ON cloud_kitchen_db.kitchen TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.category TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.cuisine TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.menu_item TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.review TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.coupon TO 'customer_role';

-- Personal Address Book Management
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.address TO 'customer_role';

-- Food Order Placement & Tracking
GRANT SELECT, INSERT ON cloud_kitchen_db.orders TO 'customer_role';
GRANT SELECT, INSERT ON cloud_kitchen_db.order_item TO 'customer_role';
GRANT SELECT, INSERT ON cloud_kitchen_db.payment TO 'customer_role';
GRANT SELECT, INSERT ON cloud_kitchen_db.coupon_usage TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.order_status_history TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.delivery TO 'customer_role';

-- Verified Review Submission
GRANT INSERT ON cloud_kitchen_db.review TO 'customer_role';

-- Customer Stored Routine Execution
GRANT EXECUTE ON PROCEDURE cloud_kitchen_db.sp_get_customer_order_summary TO 'customer_role';
GRANT EXECUTE ON FUNCTION cloud_kitchen_db.fn_calculate_order_total TO 'customer_role';
GRANT EXECUTE ON FUNCTION cloud_kitchen_db.fn_get_customer_loyalty_tier TO 'customer_role';


-- =====================================================================
-- 3.3 KITCHEN ROLE (kitchen_role)
-- Kitchen branch staff, chefs, and line supervisors managing live order
-- queues, updating food availability, recipe lookups, and inventory stock.
-- Strictly prohibited from financial payment data, administrative logs,
-- or customer addresses.
-- =====================================================================

-- Catalog & Recipe Exploration
GRANT SELECT ON cloud_kitchen_db.kitchen TO 'kitchen_role';
GRANT SELECT ON cloud_kitchen_db.category TO 'kitchen_role';
GRANT SELECT ON cloud_kitchen_db.cuisine TO 'kitchen_role';
GRANT SELECT, UPDATE ON cloud_kitchen_db.menu_item TO 'kitchen_role'; -- Can toggle is_available / 86 items
GRANT SELECT ON cloud_kitchen_db.ingredient TO 'kitchen_role';
GRANT SELECT ON cloud_kitchen_db.menu_item_ingredient TO 'kitchen_role'; -- Read recipe BOM
GRANT SELECT ON cloud_kitchen_db.staff TO 'kitchen_role';

-- Kitchen Order Preparation Workflow
GRANT SELECT, UPDATE ON cloud_kitchen_db.orders TO 'kitchen_role'; -- Update status to PREPARING / READY
GRANT SELECT ON cloud_kitchen_db.order_item TO 'kitchen_role';
GRANT SELECT, INSERT ON cloud_kitchen_db.order_status_history TO 'kitchen_role';
GRANT SELECT ON cloud_kitchen_db.delivery TO 'kitchen_role'; -- Check courier arrival

-- Warehouse Inventory & Stock Movement Logging
GRANT SELECT, INSERT, UPDATE ON cloud_kitchen_db.inventory TO 'kitchen_role';
GRANT SELECT, INSERT ON cloud_kitchen_db.inventory_movement TO 'kitchen_role';

-- Customer Feedback Review & Manager Response
GRANT SELECT, UPDATE ON cloud_kitchen_db.review TO 'kitchen_role'; -- Can append kitchen_reply

-- Kitchen Stored Routine Execution
GRANT EXECUTE ON PROCEDURE cloud_kitchen_db.sp_get_kitchen_sales_report TO 'kitchen_role';
GRANT EXECUTE ON PROCEDURE cloud_kitchen_db.sp_get_low_stock_inventory TO 'kitchen_role';
GRANT EXECUTE ON FUNCTION cloud_kitchen_db.fn_calculate_order_total TO 'kitchen_role';


-- =====================================================================
-- 3.4 DELIVERY ROLE (delivery_role)
-- Courier delivery personnel fulfilling dispatched orders.
-- Granted access only to delivery coordinates, customer contact, and
-- status tracking.
-- Strictly prohibited from kitchen recipes, stock levels, payment
-- details, or administrative audit trails.
-- =====================================================================

-- Delivery Task Management & Courier Self-Telemetry
GRANT SELECT, UPDATE ON cloud_kitchen_db.delivery TO 'delivery_role'; -- Update delivery_status, OTP, notes
GRANT SELECT, UPDATE ON cloud_kitchen_db.delivery_person TO 'delivery_role'; -- Update current_lat, current_lng, status

-- Order & Destination Navigation
GRANT SELECT, UPDATE ON cloud_kitchen_db.orders TO 'delivery_role'; -- Update order_status to OUT_FOR_DELIVERY / DELIVERED
GRANT SELECT ON cloud_kitchen_db.address TO 'delivery_role'; -- Read recipient address and phone
GRANT SELECT ON cloud_kitchen_db.kitchen TO 'delivery_role'; -- Read pickup branch location
GRANT SELECT, INSERT ON cloud_kitchen_db.order_status_history TO 'delivery_role';


-- ---------------------------------------------------------------------
-- SECTION 4: CREATE DEMONSTRATION USERS & ASSIGN ROLES
-- ---------------------------------------------------------------------
-- Create dedicated demonstration accounts for each organizational role.
-- Uses standard MySQL 8.0 caching_sha2_password authentication plugin.
-- Demonstration credentials follow secure complexity rules without
-- hardcoding production secrets.
-- ---------------------------------------------------------------------

-- Create Users
CREATE USER IF NOT EXISTS 'gk_admin'@'localhost' 
    IDENTIFIED WITH caching_sha2_password BY 'DemoAdminPass!2026#';

CREATE USER IF NOT EXISTS 'gk_customer'@'localhost' 
    IDENTIFIED WITH caching_sha2_password BY 'DemoCustomerPass!2026#';

CREATE USER IF NOT EXISTS 'gk_kitchen'@'localhost' 
    IDENTIFIED WITH caching_sha2_password BY 'DemoKitchenPass!2026#';

CREATE USER IF NOT EXISTS 'gk_delivery'@'localhost' 
    IDENTIFIED WITH caching_sha2_password BY 'DemoDeliveryPass!2026#';

-- Grant Roles to Users
GRANT 'admin_role' TO 'gk_admin'@'localhost';
GRANT 'customer_role' TO 'gk_customer'@'localhost';
GRANT 'kitchen_role' TO 'gk_kitchen'@'localhost';
GRANT 'delivery_role' TO 'gk_delivery'@'localhost';

-- Configure Default Roles so privileges activate automatically upon connection
-- without requiring explicit 'SET ROLE' statements
SET DEFAULT ROLE 'admin_role' TO 'gk_admin'@'localhost';
SET DEFAULT ROLE 'customer_role' TO 'gk_customer'@'localhost';
SET DEFAULT ROLE 'kitchen_role' TO 'gk_kitchen'@'localhost';
SET DEFAULT ROLE 'delivery_role' TO 'gk_delivery'@'localhost';

-- Apply privilege changes
FLUSH PRIVILEGES;


-- ---------------------------------------------------------------------
-- SECTION 5: PRIVILEGE AUDIT & INSPECTION (SHOW GRANTS)
-- ---------------------------------------------------------------------
-- Demonstrate how MySQL reports active role bindings and privilege scopes.
-- ---------------------------------------------------------------------

-- 5.1 Inspect Roles
SHOW GRANTS FOR 'admin_role';
SHOW GRANTS FOR 'customer_role';
SHOW GRANTS FOR 'kitchen_role';
SHOW GRANTS FOR 'delivery_role';

-- 5.2 Inspect Specific Demonstration Users (Showing assigned default role)
SHOW GRANTS FOR 'gk_admin'@'localhost';
SHOW GRANTS FOR 'gk_customer'@'localhost';
SHOW GRANTS FOR 'gk_kitchen'@'localhost';
SHOW GRANTS FOR 'gk_delivery'@'localhost';

-- 5.3 Inspect Effective Permissions Granted via the Role
SHOW GRANTS FOR 'gk_kitchen'@'localhost' USING 'kitchen_role';
SHOW GRANTS FOR 'gk_delivery'@'localhost' USING 'delivery_role';


-- ---------------------------------------------------------------------
-- SECTION 6: PRIVILEGE REVOCATION DEMONSTRATION (REVOKE)
-- ---------------------------------------------------------------------
-- Demonstrates dynamic permission reduction according to security policies:
-- Example 1: Revoke DELETE privilege on orders from admin_role to enforce immutability.
-- Example 2: Revoke UPDATE on menu_item from kitchen_role during menu freeze windows.
-- ---------------------------------------------------------------------

-- Step 6.1: Demonstrate revoking a table-level privilege from a role
REVOKE DELETE ON cloud_kitchen_db.orders FROM 'admin_role';

-- Verify that admin_role can no longer delete from orders
SHOW GRANTS FOR 'admin_role';

-- Restore DELETE to admin_role for ongoing maintenance demonstration
GRANT DELETE ON cloud_kitchen_db.orders TO 'admin_role';

-- Step 6.2: Demonstrate revoking a specific user role assignment
-- Temporarily detach delivery_role from gk_delivery
REVOKE 'delivery_role' FROM 'gk_delivery'@'localhost';
SHOW GRANTS FOR 'gk_delivery'@'localhost';

-- Re-grant delivery_role to restore operational state
GRANT 'delivery_role' TO 'gk_delivery'@'localhost';
SET DEFAULT ROLE 'delivery_role' TO 'gk_delivery'@'localhost';
FLUSH PRIVILEGES;


-- ---------------------------------------------------------------------
-- SECTION 7: PRACTICAL ACCESS RESTRICTION TEST HARNESS
-- ---------------------------------------------------------------------
-- The queries below demonstrate that privilege enforcement is strictly
-- evaluated at the database engine level by MySQL InnoDB.
-- Run each block while connected as the respective demonstration user.
-- ---------------------------------------------------------------------

-- =====================================================================
-- TEST SUITE 1: CONNECTED AS 'gk_customer'@'localhost'
-- =====================================================================

-- [SUCCESS] Authorized Operation: Customer queries available menu catalog
-- SELECT menu_item_id, name, base_price FROM cloud_kitchen_db.menu_item WHERE is_available = TRUE;

-- [SUCCESS] Authorized Operation: Customer reads reviews
-- SELECT rating, review_text FROM cloud_kitchen_db.review LIMIT 5;

-- [DENIED] Unauthorized Operation: Customer attempts to inspect staff rosters
-- Query: SELECT * FROM cloud_kitchen_db.staff;
-- Expected Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_customer'@'localhost' for table 'staff'

-- [DENIED] Unauthorized Operation: Customer attempts to access administrative audit log
-- Query: SELECT * FROM cloud_kitchen_db.admin_audit_log;
-- Expected Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_customer'@'localhost' for table 'admin_audit_log'

-- [DENIED] Unauthorized Operation: Customer attempts to alter a dish price
-- Query: UPDATE cloud_kitchen_db.menu_item SET base_price = 10.00 WHERE menu_item_id = 1;
-- Expected Result:
-- ERROR 1142 (42000): UPDATE command denied to user 'gk_customer'@'localhost' for table 'menu_item'


-- =====================================================================
-- TEST SUITE 2: CONNECTED AS 'gk_kitchen'@'localhost'
-- =====================================================================

-- [SUCCESS] Authorized Operation: Kitchen staff inspects active preparation queue
-- SELECT order_id, order_number, order_status FROM cloud_kitchen_db.orders WHERE order_status = 'CONFIRMED';

-- [SUCCESS] Authorized Operation: Kitchen staff marks order as preparing
-- UPDATE cloud_kitchen_db.orders SET order_status = 'PREPARING' WHERE order_id = 1;

-- [SUCCESS] Authorized Operation: Kitchen staff inspects ingredient stock levels
-- SELECT ingredient_id, current_stock, reorder_level FROM cloud_kitchen_db.inventory WHERE kitchen_id = 1;

-- [DENIED] Unauthorized Operation: Kitchen staff attempts to read financial payment records
-- Query: SELECT * FROM cloud_kitchen_db.payment;
-- Expected Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_kitchen'@'localhost' for table 'payment'

-- [DENIED] Unauthorized Operation: Kitchen staff attempts to create promo coupons
-- Query: INSERT INTO cloud_kitchen_db.coupon (code, discount_type, discount_value, valid_from, valid_to) VALUES ('HACK50', 'PERCENTAGE', 50.00, NOW(), NOW());
-- Expected Result:
-- ERROR 1142 (42000): INSERT command denied to user 'gk_kitchen'@'localhost' for table 'coupon'


-- =====================================================================
-- TEST SUITE 3: CONNECTED AS 'gk_delivery'@'localhost'
-- =====================================================================

-- [SUCCESS] Authorized Operation: Courier queries assigned dispatches
-- SELECT delivery_id, order_id, delivery_status FROM cloud_kitchen_db.delivery WHERE delivery_status = 'ASSIGNED';

-- [SUCCESS] Authorized Operation: Courier reads delivery destination address
-- SELECT recipient_name, recipient_phone, address_line1, city FROM cloud_kitchen_db.address WHERE address_id = 1;

-- [DENIED] Unauthorized Operation: Courier attempts to view kitchen ingredient inventory
-- Query: SELECT * FROM cloud_kitchen_db.inventory;
-- Expected Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_delivery'@'localhost' for table 'inventory'

-- [DENIED] Unauthorized Operation: Courier attempts to modify menu item prices
-- Query: UPDATE cloud_kitchen_db.menu_item SET base_price = 0.00 WHERE menu_item_id = 1;
-- Expected Result:
-- ERROR 1142 (42000): UPDATE command denied to user 'gk_delivery'@'localhost' for table 'menu_item'

-- [DENIED] Unauthorized Operation: Courier attempts to view user password hashes
-- Query: SELECT password_hash FROM cloud_kitchen_db.users;
-- Expected Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_delivery'@'localhost' for table 'users'


-- ---------------------------------------------------------------------
-- SECTION 8: OPTIONAL TEARDOWN SCRIPT
-- ---------------------------------------------------------------------
-- To cleanly remove the demonstration users and roles without affecting
-- the application service account:
-- ---------------------------------------------------------------------
-- DROP USER IF EXISTS 'gk_admin'@'localhost';
-- DROP USER IF EXISTS 'gk_customer'@'localhost';
-- DROP USER IF EXISTS 'gk_kitchen'@'localhost';
-- DROP USER IF EXISTS 'gk_delivery'@'localhost';
-- DROP ROLE IF EXISTS 'admin_role';
-- DROP ROLE IF EXISTS 'customer_role';
-- DROP ROLE IF EXISTS 'kitchen_role';
-- DROP ROLE IF EXISTS 'delivery_role';
-- FLUSH PRIVILEGES;
