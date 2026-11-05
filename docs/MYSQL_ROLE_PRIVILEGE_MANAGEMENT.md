# MySQL Database-Level User Roles & Privilege Management

**Project:** Cloud Kitchen Management System (GourmetCloud)  
**Document:** `docs/MYSQL_ROLE_PRIVILEGE_MANAGEMENT.md`  
**Database Engine:** MySQL 8.0+ (InnoDB)  
**Architecture:** Role-Based Access Control (RBAC) & Principle of Least Privilege (PoLP)  
**Database Catalog:** `cloud_kitchen_db` (22 Authoritative Tables)  

---

## 1. Introduction to Database-Level Roles & RBAC in MySQL 8.0

Prior to MySQL 8.0, user privilege management required granting explicit database, table, or column privileges to each individual user account (`GRANT ... TO 'user'@'host'`). This led to administrative overhead, privilege drift, and security vulnerabilities as organizations scaled.

MySQL 8.0 introduced **First-Class Database Roles**:
- A **Role** is a named collection of privileges that acts as an authorization template.
- Privileges are granted to the role once (`GRANT ... TO 'role_name'`).
- Users are granted one or more roles (`GRANT 'role_name' TO 'user'@'host'`).
- Default roles can be activated automatically upon login (`SET DEFAULT ROLE ...`).
- When organizational responsibilities evolve, updating the role immediately updates the effective privileges of all assigned users without altering individual account schemas.

```text
+-----------------------------------------------------------------------------------+
|                           MySQL 8.0 RBAC Architecture                             |
+-----------------------------------------------------------------------------------+
|  [ admin_role ]     --> Granted to --> 'gk_admin'@'localhost'    (Manager)        |
|  [ customer_role ]  --> Granted to --> 'gk_customer'@'localhost' (Consumer)       |
|  [ kitchen_role ]   --> Granted to --> 'gk_kitchen'@'localhost'  (Chef / Packer)  |
|  [ delivery_role ]  --> Granted to --> 'gk_delivery'@'localhost' (Courier)        |
+-----------------------------------------------------------------------------------+
```

---

## 2. Authentication vs. Authorization

Understanding the distinction between Authentication and Authorization is a core requirement of modern database security:

| Dimension | Authentication (AuthN) | Authorization (AuthZ) |
| :--- | :--- | :--- |
| **Fundamental Question** | *"Who are you?"* | *"What are you permitted to do?"* |
| **Verification Asset** | Credentials: Username, Password Hash, Salt, OTP, JWT signature, TLS certificate | Privileges: Permissions granted on schemas, tables, views, columns, and stored routines |
| **Application Layer (FastAPI)** | Verifies email and Bcrypt password hash; issues signed HMAC-SHA256 JWT access tokens | Reads `role` claim in JWT (`CUSTOMER`, `KITCHEN_STAFF`, etc.) to enforce route guards |
| **Database Layer (MySQL 8.0)** | Verifies database user username and `caching_sha2_password` scram during connection handshake | Checks MySQL privilege tables (`mysql.tables_priv`, `mysql.db`, `mysql.role_edges`) before executing each query |
| **Failure State** | `ERROR 1045 (28000): Access denied for user (using password: YES)` | `ERROR 1142 (42000): SELECT command denied to user for table '...'` |

### Why Database-Level Roles are Critical (Defense in Depth)
While modern web frameworks enforce authorization in application code (FastAPI dependencies), **application-level authorization alone is insufficient**:
1. **Direct Database Access:** Database Administrators, reporting microservices, or ETL pipelines connect directly to MySQL bypassing FastAPI.
2. **SQL Injection Mitigation:** If an attacker discovers an application injection flaw, a database account constrained by least privilege cannot execute dropped tables or read administrative audit logs.
3. **Internal Data Confidentiality:** Couriers must never have database read privileges on financial card transaction references or raw ingredient supplier costs.

---

## 3. Principle of Least Privilege (PoLP) Architectural Design

The **Principle of Least Privilege (PoLP)** dictates that every security principal (user, service, or role) must be granted only the minimum set of permissions necessary to execute its legitimate responsibilities, and no more.

In GourmetCloud:
- **No Global Superuser Access:** No custom role is granted `GRANT ALL PRIVILEGES ON *.*` or `SUPER`. All grants are strictly qualified to `cloud_kitchen_db.<table_name>`.
- **Financial Immutability:** Neither customers nor couriers can UPDATE or DELETE historical `payment` or `order_item` records.
- **Trade Secret Protection:** Proprietary Bill of Materials recipes (`menu_item_ingredient`) and ingredient purchase costs (`inventory_movement.unit_cost`) are inaccessible to customers and couriers.
- **Audit Integrity:** The administrative audit trail (`admin_audit_log`) is strictly readable and writable only by authorized administrative roles.

---

## 4. GourmetCloud Database Role Catalog

### 1. `admin_role`
- **Organizational Entity:** General Managers, Operations Directors, System Auditors.
- **Scope:** Full DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) across all 22 domain tables in `cloud_kitchen_db`.
- **Stored Routine Privileges:** Full `EXECUTE` privileges on all 3 stored procedures and 2 stored functions.
- **Security Boundary:** Limited to `cloud_kitchen_db`; cannot shut down the database server or modify global MySQL configurations.

### 2. `customer_role`
- **Organizational Entity:** Registered food ordering consumers.
- **Scope:** 
  - Read-only (`SELECT`) on public catalog entities: `kitchen`, `category`, `cuisine`, `menu_item`, `review`, and active `coupon` vouchers.
  - Full CRUD (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on personal delivery destinations in `address`.
  - Append & Read (`SELECT`, `INSERT`) on orders, line items, payments, coupon redemptions, and reviews.
- **Stored Routine Privileges:** `EXECUTE` on `sp_get_customer_order_summary`, `fn_calculate_order_total`, and `fn_get_customer_loyalty_tier`.
- **Denied Access:** `staff`, `ingredient`, `inventory`, `inventory_movement`, `menu_item_ingredient`, `admin_audit_log`.

### 3. `kitchen_role`
- **Organizational Entity:** Dark kitchen branch managers, head chefs, line cooks, and inventory clerks.
- **Scope:**
  - Catalog browsing and recipe inspection: `kitchen`, `category`, `cuisine`, `ingredient`, `menu_item_ingredient`.
  - Menu item status management: `SELECT, UPDATE` on `menu_item` (can toggle 86'd / unavailable items; cannot delete dishes).
  - Kitchen ticket preparation workflow: `SELECT, UPDATE` on `orders` (advance from `CONFIRMED` $\rightarrow$ `PREPARING` $\rightarrow$ `READY_FOR_PICKUP`).
  - Stock control: `SELECT, INSERT, UPDATE` on `inventory` and `inventory_movement`.
  - Customer review moderation: `SELECT, UPDATE` on `review` (can submit `kitchen_reply`).
- **Stored Routine Privileges:** `EXECUTE` on `sp_get_kitchen_sales_report`, `sp_get_low_stock_inventory`, `fn_calculate_order_total`.
- **Denied Access:** `payment` transaction records, `users` password hashes, `admin_audit_log`.

### 4. `delivery_role`
- **Organizational Entity:** Third-party and in-house courier delivery personnel.
- **Scope:**
  - Delivery task management: `SELECT, UPDATE` on `delivery` (update delivery status, timestamps, OTP verification, driver notes).
  - Courier location tracking: `SELECT, UPDATE` on `delivery_person` (update real-time coordinates and online availability).
  - Order status tracking: `SELECT, UPDATE` on `orders` (advance order status to `OUT_FOR_DELIVERY` and `DELIVERED`).
  - Navigation lookup: `SELECT` on customer `address` and branch `kitchen`.
- **Denied Access:** `payment` ledgers, `inventory`, `ingredient`, `menu_item_ingredient`, `admin_audit_log`, `staff`, `coupon`.

---

## 5. Comprehensive Table-by-Table Privilege Matrix

The matrix below documents the exact database-level privileges granted on every table and stored routine in `cloud_kitchen_db`:

| # | Database Object (Table / Routine) | `admin_role` | `customer_role` | `kitchen_role` | `delivery_role` | Justification & Boundary |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- |
| **1** | `users` | `S, I, U, D` | None | None | None | User accounts & password hashes restricted to administrators |
| **2** | `customer` | `S, I, U, D` | None | None | None | Managed via application-level registration |
| **3** | `kitchen` | `S, I, U, D` | `SELECT` | `SELECT` | `SELECT` | Branch locations, addresses, and operating hours |
| **4** | `staff` | `S, I, U, D` | None | `SELECT` | None | Kitchen staff roster and shift planning |
| **5** | `delivery_person` | `S, I, U, D` | None | None | `SELECT, UPDATE` | Couriers update own telemetry coordinates & status |
| **6** | `category` | `S, I, U, D` | `SELECT` | `SELECT` | None | Menu course grouping taxonomy |
| **7** | `cuisine` | `S, I, U, D` | `SELECT` | `SELECT` | None | Regional culinary origin taxonomy |
| **8** | `menu_item` | `S, I, U, D` | `SELECT` | `SELECT, UPDATE` | None | Chefs toggle availability (`is_available = FALSE`) |
| **9** | `address` | `S, I, U, D` | `S, I, U, D` | None | `SELECT` | Customers manage address book; couriers read destination |
| **10**| `coupon` | `S, I, U, D` | `SELECT` | None | None | Customers read active voucher discount codes |
| **11**| `orders` | `S, I, U, D` | `SELECT, INSERT`| `SELECT, UPDATE`| `SELECT, UPDATE`| Multi-role state machine transitions |
| **12**| `order_item` | `S, I, U, D` | `SELECT, INSERT`| `SELECT` | None | Dish line snapshots; immutable post-order |
| **13**| `payment` | `S, I, U, D` | `SELECT, INSERT`| None | None | Financial transactions hidden from kitchen and drivers |
| **14**| `order_status_history` | `S, I, U, D` | `SELECT` | `SELECT, INSERT`| `SELECT, INSERT`| Status transition journal |
| **15**| `ingredient` | `S, I, U, D` | None | `SELECT` | None | Raw materials master catalog |
| **16**| `inventory` | `S, I, U, D` | None | `S, I, U` | None | On-hand kitchen stock levels |
| **17**| `inventory_movement` | `S, I, U, D` | None | `SELECT, INSERT`| None | Stock consumption and wastage journal |
| **18**| `menu_item_ingredient` | `S, I, U, D` | None | `SELECT` | None | Proprietary recipe Bill of Materials (BOM) |
| **19**| `delivery` | `S, I, U, D` | `SELECT` | `SELECT` | `SELECT, UPDATE`| Courier task status and OTP verification |
| **20**| `coupon_usage` | `S, I, U, D` | `SELECT, INSERT`| None | None | Promo redemption ledger |
| **21**| `review` | `S, I, U, D` | `SELECT, INSERT`| `SELECT, UPDATE`| None | Customers submit ratings; kitchen submits replies |
| **22**| `admin_audit_log` | `S, I, U, D` | None | None | None | Administrative audit trail restricted to admin |
| **R1**| `sp_get_customer_order_summary`| `EXECUTE` | `EXECUTE` | None | None | Lifetime customer ordering summary procedure |
| **R2**| `sp_get_kitchen_sales_report` | `EXECUTE` | None | `EXECUTE` | None | Kitchen branch revenue report procedure |
| **R3**| `sp_get_low_stock_inventory` | `EXECUTE` | None | `EXECUTE` | None | Inventory reorder alert procedure |
| **R4**| `fn_calculate_order_total` | `EXECUTE` | `EXECUTE` | `EXECUTE` | None | Recalculate order billable total function |
| **R5**| `fn_get_customer_loyalty_tier`| `EXECUTE` | `EXECUTE` | None | None | Evaluate loyalty reward tier function |

*Legend:* `S` = SELECT, `I` = INSERT, `U` = UPDATE, `D` = DELETE, `None` = No privileges (Access Denied).

---

## 6. SQL Implementation Walkthrough

The executable SQL commands are maintained in:
[`database/role_privilege_management.sql`](file:///home/murali/Desktop/SEM%205%20/DBMS/PROJECT/database/role_privilege_management.sql)

### 6.1 Creating Roles
```sql
CREATE ROLE IF NOT EXISTS 'admin_role';
CREATE ROLE IF NOT EXISTS 'customer_role';
CREATE ROLE IF NOT EXISTS 'kitchen_role';
CREATE ROLE IF NOT EXISTS 'delivery_role';
```

### 6.2 Granting Privileges to Roles
```sql
-- Granting catalog browsing to customer_role
GRANT SELECT ON cloud_kitchen_db.kitchen TO 'customer_role';
GRANT SELECT ON cloud_kitchen_db.menu_item TO 'customer_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON cloud_kitchen_db.address TO 'customer_role';

-- Granting order fulfillment and inventory control to kitchen_role
GRANT SELECT, UPDATE ON cloud_kitchen_db.orders TO 'kitchen_role';
GRANT SELECT, INSERT, UPDATE ON cloud_kitchen_db.inventory TO 'kitchen_role';
GRANT EXECUTE ON PROCEDURE cloud_kitchen_db.sp_get_low_stock_inventory TO 'kitchen_role';

-- Granting delivery fulfillment to delivery_role
GRANT SELECT, UPDATE ON cloud_kitchen_db.delivery TO 'delivery_role';
GRANT SELECT ON cloud_kitchen_db.address TO 'delivery_role';
```

### 6.3 Creating Users & Binding Roles
```sql
-- Create demonstration users
CREATE USER IF NOT EXISTS 'gk_admin'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'DemoAdminPass!2026#';
CREATE USER IF NOT EXISTS 'gk_customer'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'DemoCustomerPass!2026#';
CREATE USER IF NOT EXISTS 'gk_kitchen'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'DemoKitchenPass!2026#';
CREATE USER IF NOT EXISTS 'gk_delivery'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'DemoDeliveryPass!2026#';

-- Grant roles to users
GRANT 'admin_role' TO 'gk_admin'@'localhost';
GRANT 'customer_role' TO 'gk_customer'@'localhost';
GRANT 'kitchen_role' TO 'gk_kitchen'@'localhost';
GRANT 'delivery_role' TO 'gk_delivery'@'localhost';

-- Activate default roles upon login
SET DEFAULT ROLE 'admin_role' TO 'gk_admin'@'localhost';
SET DEFAULT ROLE 'customer_role' TO 'gk_customer'@'localhost';
SET DEFAULT ROLE 'kitchen_role' TO 'gk_kitchen'@'localhost';
SET DEFAULT ROLE 'delivery_role' TO 'gk_delivery'@'localhost';

FLUSH PRIVILEGES;
```

---

## 7. Privilege Inspection & Revocation Demonstration

### 7.1 Inspecting Active Grants (`SHOW GRANTS`)
To display privileges assigned to a role:
```sql
SHOW GRANTS FOR 'kitchen_role';
```
*Expected Output:*
```text
+------------------------------------------------------------------------------------------------------------------+
| Grants for kitchen_role@%                                                                                        |
+------------------------------------------------------------------------------------------------------------------+
| GRANT USAGE ON *.* TO `kitchen_role`@`%`                                                                         |
| GRANT SELECT, UPDATE ON `cloud_kitchen_db`.`orders` TO `kitchen_role`@`%`                                        |
| GRANT SELECT, INSERT, UPDATE ON `cloud_kitchen_db`.`inventory` TO `kitchen_role`@`%`                             |
| GRANT EXECUTE ON PROCEDURE `cloud_kitchen_db`.`sp_get_low_stock_inventory` TO `kitchen_role`@`%`                 |
| ...                                                                                                              |
+------------------------------------------------------------------------------------------------------------------+
```

To display effective privileges for a user operating under their active role:
```sql
SHOW GRANTS FOR 'gk_kitchen'@'localhost' USING 'kitchen_role';
```

### 7.2 Demonstrating Dynamic Revocation (`REVOKE`)
To remove a dangerous privilege from a role dynamically:
```sql
-- Revoke DELETE privilege on orders from admin_role to enforce immutability
REVOKE DELETE ON cloud_kitchen_db.orders FROM 'admin_role';

-- Verify that DELETE is no longer present in admin_role grants
SHOW GRANTS FOR 'admin_role';

-- Re-grant when necessary
GRANT DELETE ON cloud_kitchen_db.orders TO 'admin_role';
```

To revoke a role assignment from a specific user:
```sql
-- Detach delivery_role from gk_delivery
REVOKE 'delivery_role' FROM 'gk_delivery'@'localhost';

-- Confirm user now has zero database access
SHOW GRANTS FOR 'gk_delivery'@'localhost';

-- Re-attach role
GRANT 'delivery_role' TO 'gk_delivery'@'localhost';
SET DEFAULT ROLE 'delivery_role' TO 'gk_delivery'@'localhost';
```

---

## 8. Access Restriction & Negative Testing Proofs

The test queries below prove that MySQL engine-level security blocks unauthorized access with exact error codes:

### Test Suite A: Connected as `gk_customer`@`localhost`
```sql
-- 1. Authorized: Querying menu items succeeds
SELECT menu_item_id, name, base_price FROM cloud_kitchen_db.menu_item WHERE is_available = TRUE;
-- Result: 18 rows returned (SUCCESS)

-- 2. Unauthorized: Customer attempts to read employee staff rosters
SELECT * FROM cloud_kitchen_db.staff;
-- Expected Engine Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_customer'@'localhost' for table 'staff'

-- 3. Unauthorized: Customer attempts to read administrative audit logs
SELECT * FROM cloud_kitchen_db.admin_audit_log;
-- Expected Engine Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_customer'@'localhost' for table 'admin_audit_log'

-- 4. Unauthorized: Customer attempts to update a dish price
UPDATE cloud_kitchen_db.menu_item SET base_price = 1.00 WHERE menu_item_id = 1;
-- Expected Engine Result:
-- ERROR 1142 (42000): UPDATE command denied to user 'gk_customer'@'localhost' for table 'menu_item'
```

### Test Suite B: Connected as `gk_kitchen`@`localhost`
```sql
-- 1. Authorized: Kitchen queries active preparation tickets
SELECT order_id, order_number, order_status FROM cloud_kitchen_db.orders WHERE order_status = 'CONFIRMED';
-- Result: Rows returned (SUCCESS)

-- 2. Authorized: Kitchen staff updates ticket status to PREPARING
UPDATE cloud_kitchen_db.orders SET order_status = 'PREPARING' WHERE order_id = 1;
-- Result: 1 row affected (SUCCESS)

-- 3. Unauthorized: Kitchen chef attempts to view customer credit card/payment ledger
SELECT * FROM cloud_kitchen_db.payment;
-- Expected Engine Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_kitchen'@'localhost' for table 'payment'

-- 4. Unauthorized: Kitchen staff attempts to create a discount coupon
INSERT INTO cloud_kitchen_db.coupon (code, discount_type, discount_value, valid_from, valid_to) 
VALUES ('FREEFOOD', 'PERCENTAGE', 100.00, NOW(), NOW());
-- Expected Engine Result:
-- ERROR 1142 (42000): INSERT command denied to user 'gk_kitchen'@'localhost' for table 'coupon'
```

### Test Suite C: Connected as `gk_delivery`@`localhost`
```sql
-- 1. Authorized: Courier reads delivery destination details
SELECT recipient_name, recipient_phone, address_line1, city FROM cloud_kitchen_db.address WHERE address_id = 1;
-- Result: Destination returned (SUCCESS)

-- 2. Unauthorized: Courier attempts to view kitchen ingredient stock
SELECT * FROM cloud_kitchen_db.inventory;
-- Expected Engine Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_delivery'@'localhost' for table 'inventory'

-- 3. Unauthorized: Courier attempts to read customer account password hashes
SELECT password_hash FROM cloud_kitchen_db.users;
-- Expected Engine Result:
-- ERROR 1142 (42000): SELECT command denied to user 'gk_delivery'@'localhost' for table 'users'
```

---

## 9. Application Preservation & Coexistence

### Coexistence Architecture
The existing application service account `'cloud_kitchen_app'@'localhost'` continues to operate as the dedicated application backend pool account:
- **FastAPI Backend:** Connects via connection pooling (`SQLAlchemy 2.0`) using `cloud_kitchen_app`.
- **JWT & App RBAC:** FastAPI validates incoming customer and staff HTTP requests, mapping user roles to internal API endpoints.
- **Demonstration Accounts:** `gk_admin`, `gk_customer`, `gk_kitchen`, and `gk_delivery` exist side-by-side to provide formal academic demonstration of engine-level privilege enforcement for DBMS examiners.

---

## 10. Step-by-Step Viva & Terminal Demonstration Guide

During your viva voce or lab examination, execute the following steps:

### Step 1: Connect as Root or Administrator
```bash
mysql -u root -p cloud_kitchen_db
```

### Step 2: Source the Role & Privilege Script
```sql
SOURCE database/role_privilege_management.sql;
```

### Step 3: Demonstrate Grants for Roles and Users
```sql
-- Show kitchen role grants
SHOW GRANTS FOR 'kitchen_role';

-- Show effective grants for kitchen user
SHOW GRANTS FOR 'gk_kitchen'@'localhost' USING 'kitchen_role';
```

### Step 4: Demonstrate Positive (Authorized) vs Negative (Denied) Queries
Open a new terminal and connect as the kitchen user:
```bash
mysql -u gk_kitchen -p'DemoKitchenPass!2026#' cloud_kitchen_db
```
Execute an authorized query:
```sql
SELECT order_id, order_number, order_status FROM orders LIMIT 3;
-- SUCCESS
```
Execute an unauthorized query:
```sql
SELECT * FROM payment;
-- ERROR 1142 (42000): SELECT command denied to user 'gk_kitchen'@'localhost' for table 'payment'
```

### Step 5: Demonstrate Dynamic Revocation
Return to the root terminal and revoke a privilege:
```sql
REVOKE UPDATE ON cloud_kitchen_db.orders FROM 'kitchen_role';
```
Return to the `gk_kitchen` terminal and attempt the update:
```sql
UPDATE orders SET order_status = 'PREPARING' WHERE order_id = 1;
-- ERROR 1142 (42000): UPDATE command denied to user 'gk_kitchen'@'localhost' for table 'orders'
```
Re-grant to restore operational state:
```sql
GRANT UPDATE ON cloud_kitchen_db.orders TO 'kitchen_role';
```

---

## 11. Viva Voce Questions & Answers (MySQL RBAC Focus)

### Q1: What is the difference between a User and a Role in MySQL 8.0?
**A:** A user represents an authenticated identity that connects with credentials (`caching_sha2_password`). A role is an authorization abstraction—a named collection of privileges that cannot authenticate or log in directly. Roles are granted to users, simplifying privilege administration.

### Q2: Why is `SET DEFAULT ROLE` required when assigning roles to users in MySQL 8?
**A:** By default, when a role is granted to a user, the role remains inactive upon initial login. The user would have to explicitly run `SET ROLE 'role_name';` during every session. Running `SET DEFAULT ROLE ALL TO 'user'@'host'` ensures that all assigned roles activate automatically upon successful login.

### Q3: What is the Principle of Least Privilege, and how does GourmetCloud adhere to it?
**A:** The Principle of Least Privilege states that a user or process must be granted only the minimum permissions necessary to complete their assigned function. In GourmetCloud:
- Couriers (`delivery_role`) can only read destination addresses and update delivery status; they cannot inspect kitchen ingredient inventories or customer payment cards.
- Kitchen staff (`kitchen_role`) can update order preparation states and inventory stocks, but cannot delete customer records or alter promotional coupons.

### Q4: What happens if a user has multiple roles granted with overlapping privileges?
**A:** In MySQL 8, permissions granted across multiple active roles are additive (union of privileges). If Role A grants `SELECT` and Role B grants `INSERT` on the same table, a user with both roles active can both select and insert.

### Q5: How does database-level authorization differ from application-level (JWT) authorization?
**A:** Application-level authorization (e.g. FastAPI reading JWT claims) guards HTTP endpoints. However, if a developer makes a coding error, or an internal administrator connects via MySQL Workbench, application guards are bypassed. Database-level authorization operates at the MySQL InnoDB engine level, blocking unauthorized SQL queries regardless of the client tool used.

### Q6: Can a role be granted to another role in MySQL 8?
**A:** Yes. MySQL 8 supports **Hierarchical Roles**. For example, a `super_kitchen_role` could inherit all privileges of `kitchen_role` plus additional inventory supplier management privileges.

### Q7: Explain the syntax and purpose of `REVOKE ... FROM ...`.
**A:** The `REVOKE` DCL statement removes previously granted privileges or roles from a principal. For example, `REVOKE DELETE ON cloud_kitchen_db.orders FROM 'admin_role';` removes the deletion permission from the role, dynamically taking effect for all users holding that role.

### Q8: What table stores role assignments in MySQL?
**A:** The `mysql.role_edges` data dictionary table records role-to-user and role-to-role inheritance mappings (`FROM_HOST`, `FROM_USER`, `TO_HOST`, `TO_USER`). Table-level privileges reside in `mysql.tables_priv`.

### Q9: Why is granting `ALL PRIVILEGES ON *.*` considered an anti-pattern in database engineering?
**A:** Global administrative grants bypass schema boundaries, allow dropping arbitrary databases, creating rogue accounts, modifying system tables, and reading files from the underlying operating system (`LOAD_FILE`). Least privilege requires qualifying grants to specific databases (`cloud_kitchen_db.*`) or specific tables.

### Q10: How do you verify whether a privilege revocation took effect immediately?
**A:** Privileges assigned to roles take effect dynamically for active sessions. Running `SHOW GRANTS FOR 'user'@'host' USING 'role_name'` immediately shows the updated privilege set.
