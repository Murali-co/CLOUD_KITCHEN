-- =====================================================================
-- CLOUD KITCHEN MANAGEMENT & FOOD ORDERING SYSTEM
-- Database Schema Definition (DDL)
-- Target RDBMS: MySQL 8.0+
-- Storage Engine: InnoDB
-- Character Set: utf8mb4 / Collation: utf8mb4_unicode_ci
-- Total Tables: 20
-- =====================================================================

-- Note: In accordance with project instructions, this script defines
-- the complete DDL structure. It is designed to be executed inside a designated
-- database (e.g. `cloud_kitchen_db`) upon user authorization.

SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------
-- 1. Table: users
-- Core authentication and identity entity for all system actors.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role ENUM('CUSTOMER', 'ADMIN', 'KITCHEN_STAFF', 'DELIVERY_PERSON') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_users_email UNIQUE (email),
    CONSTRAINT uk_users_phone UNIQUE (phone_number),
    CONSTRAINT chk_users_email CHECK (email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_users_phone CHECK (phone_number REGEXP '^[0-9+ -]{8,20}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Master account entity storing credentials, phone, and role classification';

-- ---------------------------------------------------------------------
-- 2. Table: customer
-- Customer profile extension table holding loyalty rewards and preferences.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer (
    customer_id BIGINT UNSIGNED PRIMARY KEY,
    loyalty_points INT UNSIGNED NOT NULL DEFAULT 0,
    dietary_preference ENUM('ALL', 'VEGETARIAN', 'VEGAN', 'HALAL', 'GLUTEN_FREE') NOT NULL DEFAULT 'ALL',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_customer_users FOREIGN KEY (customer_id) 
        REFERENCES users (user_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Customer domain extension storing loyalty points and dietary preference';

-- ---------------------------------------------------------------------
-- 3. Table: kitchen
-- Physical cloud kitchen facility outlets / branches.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kitchen (
    kitchen_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    branch_code VARCHAR(50) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255) NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    latitude DECIMAL(10, 8) NULL,
    longitude DECIMAL(11, 8) NULL,
    operating_status ENUM('ACTIVE', 'INACTIVE', 'MAINTENANCE') NOT NULL DEFAULT 'ACTIVE',
    opening_time TIME NOT NULL DEFAULT '08:00:00',
    closing_time TIME NOT NULL DEFAULT '23:00:00',
    max_active_orders INT UNSIGNED NOT NULL DEFAULT 50,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_kitchen_branch_code UNIQUE (branch_code),
    CONSTRAINT chk_kitchen_max_orders CHECK (max_active_orders > 0),
    CONSTRAINT chk_kitchen_lat CHECK (latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)),
    CONSTRAINT chk_kitchen_lng CHECK (longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cloud kitchen branch facilities handling meal prep and regional dispatch';

-- ---------------------------------------------------------------------
-- 4. Table: staff
-- Kitchen internal personnel and managers tied to a specific kitchen branch.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staff (
    staff_id BIGINT UNSIGNED PRIMARY KEY,
    kitchen_id BIGINT UNSIGNED NOT NULL,
    staff_role ENUM('KITCHEN_MANAGER', 'HEAD_CHEF', 'LINE_COOK', 'PACKER', 'INVENTORY_CONTROLLER') NOT NULL,
    shift_timing ENUM('MORNING', 'EVENING', 'NIGHT', 'ROTATING') NOT NULL DEFAULT 'MORNING',
    hired_date DATE NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_staff_users FOREIGN KEY (staff_id) 
        REFERENCES users (user_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_staff_kitchen FOREIGN KEY (kitchen_id) 
        REFERENCES kitchen (kitchen_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Kitchen internal staff and management linked to specific kitchen branch';

-- ---------------------------------------------------------------------
-- 5. Table: delivery_person
-- Fleet drivers and delivery personnel details.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS delivery_person (
    delivery_person_id BIGINT UNSIGNED PRIMARY KEY,
    vehicle_type ENUM('MOTORCYCLE', 'SCOOTER', 'BICYCLE', 'ELECTRIC_VEHICLE') NOT NULL,
    vehicle_number VARCHAR(50) NOT NULL,
    driving_license_number VARCHAR(50) NOT NULL,
    current_status ENUM('AVAILABLE', 'ON_DELIVERY', 'OFF_DUTY') NOT NULL DEFAULT 'AVAILABLE',
    current_latitude DECIMAL(10, 8) NULL,
    current_longitude DECIMAL(11, 8) NULL,
    rating DECIMAL(3, 2) NOT NULL DEFAULT 5.00,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_delivery_vehicle UNIQUE (vehicle_number),
    CONSTRAINT uk_delivery_license UNIQUE (driving_license_number),
    CONSTRAINT chk_delivery_rating CHECK (rating >= 1.00 AND rating <= 5.00),
    CONSTRAINT chk_delivery_lat CHECK (current_latitude IS NULL OR (current_latitude >= -90.0 AND current_latitude <= 90.0)),
    CONSTRAINT chk_delivery_lng CHECK (current_longitude IS NULL OR (current_longitude >= -180.0 AND current_longitude <= 180.0)),
    CONSTRAINT fk_delivery_person_users FOREIGN KEY (delivery_person_id) 
        REFERENCES users (user_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Courier driver profiles, vehicle registrations, and dispatch status';

-- ---------------------------------------------------------------------
-- 6. Table: category
-- Food categorization taxonomy (e.g. Burgers, Artisan Pizzas, Beverages).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS category (
    category_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    description TEXT NULL,
    display_order INT UNSIGNED NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_category_name UNIQUE (name),
    CONSTRAINT uk_category_slug UNIQUE (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Menu classification categories for food items';

-- ---------------------------------------------------------------------
-- 6b. Table: cuisine
-- Culinary origin and regional style taxonomy (e.g. South Indian, Italian).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cuisine (
    cuisine_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    cuisine_name VARCHAR(100) NOT NULL,
    cuisine_slug VARCHAR(120) NOT NULL,
    cuisine_description TEXT NULL,
    cuisine_image_url VARCHAR(500) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_cuisine_name UNIQUE (cuisine_name),
    CONSTRAINT uk_cuisine_slug UNIQUE (cuisine_slug),
    INDEX idx_cuisine_is_active_display (is_active, display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Culinary traditions and regional cuisine styles';

-- ---------------------------------------------------------------------
-- 7. Table: menu_item
-- Prepared food offerings prepared by kitchen branches.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_item (
    menu_item_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kitchen_id BIGINT UNSIGNED NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    cuisine_id BIGINT UNSIGNED NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    is_vegetarian BOOLEAN NOT NULL DEFAULT FALSE,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    preparation_time_minutes SMALLINT UNSIGNED NOT NULL DEFAULT 15,
    calories INT UNSIGNED NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_kitchen_menu_item UNIQUE (kitchen_id, name),
    CONSTRAINT chk_menu_item_price CHECK (base_price >= 0.00),
    CONSTRAINT chk_menu_item_prep CHECK (preparation_time_minutes > 0),
    CONSTRAINT fk_menu_item_kitchen FOREIGN KEY (kitchen_id) 
        REFERENCES kitchen (kitchen_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_menu_item_category FOREIGN KEY (category_id) 
        REFERENCES category (category_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_menu_item_cuisine FOREIGN KEY (cuisine_id) 
        REFERENCES cuisine (cuisine_id) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_menu_item_cuisine_id (cuisine_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Food and beverage items offered by kitchen branches';

-- ---------------------------------------------------------------------
-- 8. Table: address
-- Customer delivery addresses.
-- Includes composite key (address_id, customer_id) for relational compound FK.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS address (
    address_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT UNSIGNED NOT NULL,
    address_label VARCHAR(50) NOT NULL DEFAULT 'Home',
    recipient_name VARCHAR(150) NOT NULL,
    recipient_phone VARCHAR(20) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255) NULL,
    landmark VARCHAR(150) NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    latitude DECIMAL(10, 8) NULL,
    longitude DECIMAL(11, 8) NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_address_customer UNIQUE (address_id, customer_id),
    CONSTRAINT chk_address_lat CHECK (latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)),
    CONSTRAINT chk_address_lng CHECK (longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)),
    CONSTRAINT fk_address_customer FOREIGN KEY (customer_id) 
        REFERENCES customer (customer_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Saved delivery destinations associated with specific customers';

-- ---------------------------------------------------------------------
-- 9. Table: coupon
-- Promotional discount codes and campaign parameters.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coupon (
    coupon_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    description VARCHAR(255) NULL,
    discount_type ENUM('PERCENTAGE', 'FIXED_AMOUNT') NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    min_order_value DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    max_discount_amount DECIMAL(10, 2) NULL,
    valid_from DATETIME NOT NULL,
    valid_to DATETIME NOT NULL,
    usage_limit_per_user INT UNSIGNED NOT NULL DEFAULT 1,
    total_usage_limit INT UNSIGNED NOT NULL DEFAULT 1000,
    current_usage_count INT UNSIGNED NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_coupon_code UNIQUE (code),
    CONSTRAINT chk_coupon_value CHECK (discount_value > 0.00),
    CONSTRAINT chk_coupon_min_val CHECK (min_order_value >= 0.00),
    CONSTRAINT chk_coupon_max_disc CHECK (max_discount_amount IS NULL OR max_discount_amount > 0.00),
    CONSTRAINT chk_coupon_dates CHECK (valid_to >= valid_from),
    CONSTRAINT chk_coupon_usage_limit CHECK (current_usage_count <= total_usage_limit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Marketing discount coupons and redemption constraints';

-- ---------------------------------------------------------------------
-- 10. Table: orders
-- Central order transactional record.
-- Uses Compound Foreign Key (delivery_address_id, customer_id) to guarantee
-- that an order delivery address strictly belongs to the purchasing customer.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(64) NOT NULL,
    customer_id BIGINT UNSIGNED NOT NULL,
    kitchen_id BIGINT UNSIGNED NOT NULL,
    delivery_address_id BIGINT UNSIGNED NOT NULL,
    order_status ENUM('PENDING', 'CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    subtotal_amount DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    tax_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    delivery_fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    applied_coupon_id BIGINT UNSIGNED NULL,
    special_instructions TEXT NULL,
    estimated_delivery_time DATETIME NULL,
    placed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_orders_number UNIQUE (order_number),
    CONSTRAINT uk_orders_order_kitchen UNIQUE (order_id, kitchen_id),
    CONSTRAINT chk_orders_subtotal CHECK (subtotal_amount >= 0.00),
    CONSTRAINT chk_orders_discount CHECK (discount_amount >= 0.00),
    CONSTRAINT chk_orders_tax CHECK (tax_amount >= 0.00),
    CONSTRAINT chk_orders_delivery_fee CHECK (delivery_fee >= 0.00),
    CONSTRAINT chk_orders_total CHECK (total_amount >= 0.00),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) 
        REFERENCES customer (customer_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_orders_kitchen FOREIGN KEY (kitchen_id) 
        REFERENCES kitchen (kitchen_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_orders_customer_address FOREIGN KEY (delivery_address_id, customer_id) 
        REFERENCES address (address_id, customer_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_orders_coupon FOREIGN KEY (applied_coupon_id) 
        REFERENCES coupon (coupon_id) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Master customer food orders ledger';

-- ---------------------------------------------------------------------
-- 11. Table: order_item
-- Detailed line items in an order.
-- Stores item_name_snapshot and unit_price_snapshot for temporal auditing.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_item (
    order_item_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    menu_item_id BIGINT UNSIGNED NOT NULL,
    item_name_snapshot VARCHAR(150) NOT NULL,
    unit_price_snapshot DECIMAL(10, 2) NOT NULL,
    quantity SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    subtotal_price DECIMAL(10, 2) NOT NULL,
    customization_notes VARCHAR(255) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT chk_order_item_qty CHECK (quantity > 0),
    CONSTRAINT chk_order_item_price CHECK (unit_price_snapshot >= 0.00),
    CONSTRAINT chk_order_item_subtotal CHECK (subtotal_price >= 0.00),
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) 
        REFERENCES orders (order_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_order_item_menu FOREIGN KEY (menu_item_id) 
        REFERENCES menu_item (menu_item_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Invoiced order line items with historical price snapshots';

-- ---------------------------------------------------------------------
-- 12. Table: payment
-- Financial transaction records. Supports multiple attempts per order.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment (
    payment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    payment_method ENUM('UPI', 'CREDIT_CARD', 'DEBIT_CARD', 'NET_BANKING', 'WALLET', 'CASH_ON_DELIVERY') NOT NULL,
    payment_status ENUM('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED') NOT NULL DEFAULT 'PENDING',
    transaction_reference VARCHAR(100) NULL,
    gateway_name VARCHAR(50) NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    error_message TEXT NULL,
    initiated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    completed_at DATETIME(6) NULL,
    CONSTRAINT uk_payment_ref UNIQUE (transaction_reference),
    CONSTRAINT chk_payment_amount CHECK (amount > 0.00),
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id) 
        REFERENCES orders (order_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Payment transactions ledger enabling multiple payment attempts per order';

-- ---------------------------------------------------------------------
-- 13. Table: order_status_history
-- Append-only audit trail of state transitions for each order.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_status_history (
    history_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    previous_status ENUM('PENDING', 'CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED') NULL,
    new_status ENUM('PENDING', 'CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED') NOT NULL,
    changed_by_user_id BIGINT UNSIGNED NULL,
    notes TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_history_order FOREIGN KEY (order_id) 
        REFERENCES orders (order_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_history_user FOREIGN KEY (changed_by_user_id) 
        REFERENCES users (user_id) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Append-only order workflow state transition history';

-- ---------------------------------------------------------------------
-- 14. Table: ingredient
-- Master catalog of raw cooking ingredients.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingredient (
    ingredient_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NULL,
    unit_of_measure ENUM('KG', 'GRAM', 'LITER', 'MILLILITER', 'PIECE', 'PACKET') NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_ingredient_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Master catalog of raw culinary ingredients and measurement units';

-- ---------------------------------------------------------------------
-- 15. Table: inventory
-- Real-time stock levels maintained by each kitchen branch per ingredient.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kitchen_id BIGINT UNSIGNED NOT NULL,
    ingredient_id BIGINT UNSIGNED NOT NULL,
    current_stock DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    reorder_level DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    last_restocked_at DATETIME NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_kitchen_ingredient UNIQUE (kitchen_id, ingredient_id),
    CONSTRAINT chk_inventory_stock CHECK (current_stock >= 0.000),
    CONSTRAINT chk_inventory_reorder CHECK (reorder_level >= 0.000),
    CONSTRAINT fk_inventory_kitchen FOREIGN KEY (kitchen_id) 
        REFERENCES kitchen (kitchen_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_inventory_ingredient FOREIGN KEY (ingredient_id) 
        REFERENCES ingredient (ingredient_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Physical on-hand inventory balances per kitchen branch';

-- ---------------------------------------------------------------------
-- 16. Table: inventory_movement
-- Immutable audit log of all stock increases and decreases.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_movement (
    movement_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kitchen_id BIGINT UNSIGNED NOT NULL,
    ingredient_id BIGINT UNSIGNED NOT NULL,
    movement_type ENUM('RESTOCK', 'CONSUMPTION', 'SPOILAGE', 'AUDIT_ADJUSTMENT', 'RETURN') NOT NULL,
    quantity_delta DECIMAL(10, 3) NOT NULL,
    unit_cost DECIMAL(10, 2) NULL,
    reference_order_id BIGINT UNSIGNED NULL,
    notes TEXT NULL,
    recorded_by_user_id BIGINT UNSIGNED NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT chk_movement_delta CHECK (quantity_delta <> 0.000),
    CONSTRAINT chk_movement_cost CHECK (unit_cost IS NULL OR unit_cost >= 0.00),
    CONSTRAINT fk_movement_kitchen FOREIGN KEY (kitchen_id) 
        REFERENCES kitchen (kitchen_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_movement_ingredient FOREIGN KEY (ingredient_id) 
        REFERENCES ingredient (ingredient_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_movement_order FOREIGN KEY (reference_order_id) 
        REFERENCES orders (order_id) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_movement_user FOREIGN KEY (recorded_by_user_id) 
        REFERENCES users (user_id) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Immutable journal of inventory stock additions and deductions';

-- ---------------------------------------------------------------------
-- 17. Table: menu_item_ingredient
-- Recipe Bill of Materials (BOM) junction mapping dishes to ingredients.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_item_ingredient (
    menu_item_id BIGINT UNSIGNED NOT NULL,
    ingredient_id BIGINT UNSIGNED NOT NULL,
    quantity_required DECIMAL(10, 3) NOT NULL,
    unit_of_measure ENUM('KG', 'GRAM', 'LITER', 'MILLILITER', 'PIECE', 'PACKET') NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (menu_item_id, ingredient_id),
    CONSTRAINT chk_recipe_qty CHECK (quantity_required > 0.000),
    CONSTRAINT fk_recipe_menu FOREIGN KEY (menu_item_id) 
        REFERENCES menu_item (menu_item_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_recipe_ingredient FOREIGN KEY (ingredient_id) 
        REFERENCES ingredient (ingredient_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Recipe Bill of Materials junction table between dishes and ingredients';

-- ---------------------------------------------------------------------
-- 18. Table: delivery
-- Physical courier dispatch, OTP verification, and transit tracking.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS delivery (
    delivery_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    delivery_person_id BIGINT UNSIGNED NOT NULL,
    delivery_status ENUM('ASSIGNED', 'PICKED_UP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED') NOT NULL DEFAULT 'ASSIGNED',
    assigned_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    picked_up_at DATETIME(6) NULL,
    delivered_at DATETIME(6) NULL,
    delivery_otp VARCHAR(6) NULL,
    delivery_notes TEXT NULL,
    customer_signature_url VARCHAR(255) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_delivery_order UNIQUE (order_id),
    CONSTRAINT fk_delivery_order FOREIGN KEY (order_id) 
        REFERENCES orders (order_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_delivery_person FOREIGN KEY (delivery_person_id) 
        REFERENCES delivery_person (delivery_person_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Courier delivery assignments, OTP handoffs, and fulfillment log';

-- ---------------------------------------------------------------------
-- 19. Table: coupon_usage
-- Audit record of promo code redemptions enforcing per-user usage limits.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coupon_usage (
    usage_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    coupon_id BIGINT UNSIGNED NOT NULL,
    customer_id BIGINT UNSIGNED NOT NULL,
    order_id BIGINT UNSIGNED NOT NULL,
    discount_applied DECIMAL(10, 2) NOT NULL,
    used_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_coupon_usage_order UNIQUE (order_id),
    CONSTRAINT chk_coupon_usage_discount CHECK (discount_applied >= 0.00),
    CONSTRAINT fk_coupon_usage_coupon FOREIGN KEY (coupon_id) 
        REFERENCES coupon (coupon_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_coupon_usage_customer FOREIGN KEY (customer_id) 
        REFERENCES customer (customer_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_coupon_usage_order FOREIGN KEY (order_id) 
        REFERENCES orders (order_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Audit record of coupon redemptions preventing duplicate usage';

-- ---------------------------------------------------------------------
-- 20. Table: review
-- Verified customer evaluations and ratings per completed order.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review (
    review_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    customer_id BIGINT UNSIGNED NOT NULL,
    kitchen_id BIGINT UNSIGNED NOT NULL,
    rating TINYINT UNSIGNED NOT NULL,
    review_text TEXT NULL,
    kitchen_reply TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT uk_review_order UNIQUE (order_id),
    CONSTRAINT chk_review_rating CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT fk_review_order FOREIGN KEY (order_id) 
        REFERENCES orders (order_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_review_customer FOREIGN KEY (customer_id) 
        REFERENCES customer (customer_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_review_kitchen FOREIGN KEY (kitchen_id) 
        REFERENCES kitchen (kitchen_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Customer ratings and feedback bound to verified completed orders';

-- ---------------------------------------------------------------------
-- 21. Table: admin_audit_log
-- Administrative action audit trail capturing user, kitchen, menu, coupon, and order updates.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_audit_log (
    audit_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_user_id BIGINT UNSIGNED NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT UNSIGNED NULL,
    details JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_user_id) 
        REFERENCES users (user_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_audit_actor (actor_user_id),
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Administrative action audit trail capturing user, kitchen, menu, coupon, and order updates';

-- ---------------------------------------------------------------------
-- Business Rule Integrity Trigger:
-- Ensures that an ordered menu item belongs to the same kitchen as the order.
-- ---------------------------------------------------------------------
DELIMITER $$

DROP TRIGGER IF EXISTS trg_order_item_kitchen_match$$

CREATE TRIGGER trg_order_item_kitchen_match
BEFORE INSERT ON order_item
FOR EACH ROW
BEGIN
    DECLARE v_order_kitchen_id BIGINT UNSIGNED;
    DECLARE v_item_kitchen_id BIGINT UNSIGNED;

    -- Retrieve kitchen assigned to the order
    SELECT kitchen_id INTO v_order_kitchen_id 
    FROM orders 
    WHERE order_id = NEW.order_id;

    -- Retrieve kitchen that produces the menu item
    SELECT kitchen_id INTO v_item_kitchen_id 
    FROM menu_item 
    WHERE menu_item_id = NEW.menu_item_id;

    -- Validate equality
    IF v_order_kitchen_id IS NOT NULL AND v_item_kitchen_id IS NOT NULL THEN
        IF v_order_kitchen_id <> v_item_kitchen_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Integrity Violation: Menu item does not belong to the kitchen fulfilling this order.';
        END IF;
    END IF;
END$$

DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;
