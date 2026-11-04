-- =====================================================================
-- CLOUD KITCHEN MANAGEMENT & FOOD ORDERING SYSTEM
-- Comprehensive Seed & Sample Data Script
-- Target RDBMS: MySQL 8.0+ (InnoDB)
-- =====================================================================

-- Note on Passwords:
-- Passwords in this file are pre-hashed using industry-standard Bcrypt (cost=12).
-- Plaintext passwords are NEVER stored in the database.
-- Credential Reference for Development Testing:
--   - Admin Account (user_id=1):      Admin@123
--   - Customer Accounts (user_id=2,3): Customer@123
--   - Staff Accounts (user_id=4,5,6):  Staff@123
--   - Driver Accounts (user_id=7,8):   Driver@123

SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------
-- 1. Table: users
-- (1 Admin, 2 Customers, 1 Kitchen Manager, 2 Kitchen Staff, 2 Couriers)
-- ---------------------------------------------------------------------
INSERT INTO users (user_id, email, phone_number, password_hash, first_name, last_name, role, is_active)
VALUES
(1, 'admin@cloudkitchen.com', '+919876543210', '$2b$12$ZJDj8J2j5IUcaLu/hpWz4ubcPYr1oUMMbFIlOi5ZC1c0hAJ3bYbq.', 'Rajesh', 'Sharma', 'ADMIN', TRUE),
(2, 'arjun.mehta@gmail.com', '+919811122233', '$2b$12$um6XbFLygUQGHKo0blVs2uY9BJZZPG0lmjwlER5hgwIO8zdXkuLaS', 'Arjun', 'Mehta', 'CUSTOMER', TRUE),
(3, 'priya.nair@gmail.com', '+919822233344', '$2b$12$um6XbFLygUQGHKo0blVs2uY9BJZZPG0lmjwlER5hgwIO8zdXkuLaS', 'Priya', 'Nair', 'CUSTOMER', TRUE),
(4, 'vikram.singh@cloudkitchen.com', '+919833344455', '$2b$12$OCiNqCGnEJ9uF11wRXW96u0yj/jktog6lgbBfCnJ3wqADX9oPRGhC', 'Vikram', 'Singh', 'KITCHEN_STAFF', TRUE),
(5, 'ananya.deshmukh@cloudkitchen.com', '+919844455566', '$2b$12$OCiNqCGnEJ9uF11wRXW96u0yj/jktog6lgbBfCnJ3wqADX9oPRGhC', 'Ananya', 'Deshmukh', 'KITCHEN_STAFF', TRUE),
(6, 'karan.verma@cloudkitchen.com', '+919855566677', '$2b$12$OCiNqCGnEJ9uF11wRXW96u0yj/jktog6lgbBfCnJ3wqADX9oPRGhC', 'Karan', 'Verma', 'KITCHEN_STAFF', TRUE),
(7, 'rohit.kumar@delivery.com', '+919866677788', '$2b$12$b4vHNuNHSrpQvNuXtR9VCO2KYDrzpIkxTNXmMAiHcgwMJpP7SkJzG', 'Rohit', 'Kumar', 'DELIVERY_PERSON', TRUE),
(8, 'suresh.patil@delivery.com', '+919877788899', '$2b$12$b4vHNuNHSrpQvNuXtR9VCO2KYDrzpIkxTNXmMAiHcgwMJpP7SkJzG', 'Suresh', 'Patil', 'DELIVERY_PERSON', TRUE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 2. Table: customer
-- ---------------------------------------------------------------------
INSERT INTO customer (customer_id, loyalty_points, dietary_preference)
VALUES
(2, 250, 'ALL'),
(3, 120, 'VEGETARIAN')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 3. Table: kitchen (2 Cloud Kitchen Facilities in Bengaluru)
-- ---------------------------------------------------------------------
INSERT INTO kitchen (kitchen_id, name, branch_code, contact_phone, email, address_line1, address_line2, city, state, postal_code, latitude, longitude, operating_status, opening_time, closing_time, max_active_orders)
VALUES
(1, 'Cloud Kitchen Indiranagar', 'CK-BLR-01', '+918041234567', 'indiranagar@cloudkitchen.com', '100 Feet Road, HAL 2nd Stage', 'Near Metro Pillar 84', 'Bengaluru', 'Karnataka', '560038', 12.97159870, 77.64115480, 'ACTIVE', '08:00:00', '23:30:00', 60),
(2, 'Cloud Kitchen Koramangala', 'CK-BLR-02', '+918049876543', 'koramangala@cloudkitchen.com', '80 Feet Road, 4th Block', 'Opposite Sony World Signal', 'Bengaluru', 'Karnataka', '560034', 12.93519290, 77.62448070, 'ACTIVE', '09:00:00', '00:00:00', 50)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 4. Table: staff (1 Manager + 2 Kitchen Staff members)
-- ---------------------------------------------------------------------
INSERT INTO staff (staff_id, kitchen_id, staff_role, shift_timing, hired_date)
VALUES
(4, 1, 'KITCHEN_MANAGER', 'MORNING', '2024-01-15'),
(5, 1, 'HEAD_CHEF', 'MORNING', '2024-02-01'),
(6, 2, 'LINE_COOK', 'EVENING', '2024-04-10')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 5. Table: delivery_person (2 Couriers)
-- ---------------------------------------------------------------------
INSERT INTO delivery_person (delivery_person_id, vehicle_type, vehicle_number, driving_license_number, current_status, current_latitude, current_longitude, rating)
VALUES
(7, 'MOTORCYCLE', 'KA-01-EQ-4021', 'DL-KA-2018-002419', 'AVAILABLE', 12.97200000, 77.64200000, 4.90),
(8, 'ELECTRIC_VEHICLE', 'KA-03-EV-8842', 'DL-KA-2020-009183', 'AVAILABLE', 12.93600000, 77.62500000, 4.85)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 6. Table: category (5 Food Categories)
-- ---------------------------------------------------------------------
INSERT INTO category (category_id, name, slug, description, display_order, is_active)
VALUES
(1, 'Appetizers & Starters', 'appetizers-starters', 'Crispy bites, skewers, and starter plates to begin your meal', 1, TRUE),
(2, 'Gourmet Rice Bowls', 'gourmet-rice-bowls', 'Hearty chef-crafted bowls served with spiced basmati rice and fresh toppings', 2, TRUE),
(3, 'Artisan Pizzas', 'artisan-pizzas', 'Hand-stretched sourdough pizzas stone-baked to perfection', 3, TRUE),
(4, 'Pasta & Italian', 'pasta-italian', 'Al dente pastas tossed in slow-cooked sauces and infused oils', 4, TRUE),
(5, 'Desserts & Beverages', 'desserts-beverages', 'Sweet indulgences, cold pressed refreshments, and handcrafted drinks', 5, TRUE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 7. Table: menu_item (16 Dishes across Kitchens & Categories)
-- ---------------------------------------------------------------------
INSERT INTO menu_item (menu_item_id, kitchen_id, category_id, name, description, base_price, is_vegetarian, is_available, preparation_time_minutes, calories)
VALUES
-- Starters (Kitchen 1)
(1, 1, 1, 'Tandoori Paneer Tikka', 'Charcoal-grilled cottage cheese cubes marinated in spiced yogurt and kasuri methi', 260.00, TRUE, TRUE, 15, 380),
(2, 1, 1, 'Crispy Hot Chicken Wings', 'Crunchy twice-fried chicken wings tossed in smoked chili garlic glaze', 310.00, FALSE, TRUE, 18, 520),
-- Rice Bowls (Kitchen 1)
(3, 1, 2, 'Royal Butter Chicken Bowl', 'Tender chicken simmered in rich makhani gravy over fragrant saffron basmati rice', 340.00, FALSE, TRUE, 20, 680),
(4, 1, 2, 'Smoked Dal Makhani Rice Bowl', 'Slow-cooked black lentils simmered overnight with cream served over jeera rice', 280.00, TRUE, TRUE, 15, 540),
-- Pizzas (Kitchen 1)
(5, 1, 3, 'Classic Margherita Pizza', 'San Marzano tomato sauce, fresh buffalo mozzarella, fresh basil, extra virgin olive oil', 380.00, TRUE, TRUE, 20, 720),
(6, 1, 3, 'Spicy Smoked Pepperoni Pizza', 'Artisan crust topped with cured pepperoni slices, mozzarella, and chili honey drizzle', 490.00, FALSE, TRUE, 22, 890),
(7, 1, 3, 'Truffle Wild Mushroom Pizza', 'White sauce base, sautéed cremini and button mushrooms, mozzarella, truffle glaze', 440.00, TRUE, TRUE, 20, 750),
-- Pasta (Kitchen 1)
(8, 1, 4, 'Creamy Truffle Alfredo Penne', 'Penne pasta tossed in rich parmesan garlic cream sauce with garden herbs', 350.00, TRUE, TRUE, 18, 640),
(9, 1, 4, 'Arrabiata Fiery Fusilli', 'Spiral pasta tossed in spicy tomato sauce with crushed chili flakes and fresh basil', 310.00, TRUE, TRUE, 15, 490),
-- Desserts & Drinks (Kitchen 1)
(10, 1, 5, 'Warm Chocolate Lava Cake', 'Gooey decadent molten chocolate center paired with powdered sugar dusting', 190.00, TRUE, TRUE, 12, 410),
(11, 1, 5, 'Kesar Pista Gulab Jamun (2 pcs)', 'Soft golden milk dumplings soaked in saffron and green cardamom sugar syrup', 120.00, TRUE, TRUE, 10, 310),
(12, 1, 5, 'Cold Brew Arabica Coffee (300ml)', 'Single-origin 16-hour steeped black coffee served chilled over ice', 160.00, TRUE, TRUE, 5, 15),
-- Dishes for Kitchen 2 (Koramangala Branch)
(13, 2, 1, 'Tandoori Paneer Tikka', 'Charcoal-grilled cottage cheese cubes marinated in spiced yogurt and herbs', 260.00, TRUE, TRUE, 15, 380),
(14, 2, 2, 'Royal Butter Chicken Bowl', 'Rich makhani gravy over saffron basmati rice with tandoori chicken', 340.00, FALSE, TRUE, 20, 680),
(15, 2, 3, 'Classic Margherita Pizza', 'San Marzano sauce, fresh mozzarella, basil and herb oil', 380.00, TRUE, TRUE, 20, 720),
(16, 2, 5, 'Cold Brew Arabica Coffee (300ml)', 'Steeped chilled artisan black coffee', 160.00, TRUE, TRUE, 5, 15)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 8. Table: address (Customer Saved Addresses)
-- ---------------------------------------------------------------------
INSERT INTO address (address_id, customer_id, address_label, recipient_name, recipient_phone, address_line1, address_line2, landmark, city, state, postal_code, latitude, longitude, is_default)
VALUES
(1, 2, 'Home', 'Arjun Mehta', '+919811122233', 'Flat 402, Sunshine Heights', '12th Main Road, HAL 2nd Stage, Indiranagar', 'Behind BDA Complex', 'Bengaluru', 'Karnataka', '560038', 12.97340000, 77.64320000, TRUE),
(2, 2, 'Work', 'Arjun Mehta', '+919811122233', '7th Floor, Tech Hub Tower B', 'Bagmane Tech Park, CV Raman Nagar', 'Near Gate 2', 'Bengaluru', 'Karnataka', '560093', 12.98120000, 77.65980000, FALSE),
(3, 3, 'Home', 'Priya Nair', '+919822233344', 'Villa 18, Palm Meadows', 'Varthur Main Road, Whitefield', 'Near Forum Mall', 'Bengaluru', 'Karnataka', '560066', 12.96010000, 77.74900000, TRUE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 9. Table: coupon (Promotional Discounts)
-- ---------------------------------------------------------------------
INSERT INTO coupon (coupon_id, code, description, discount_type, discount_value, min_order_value, max_discount_amount, valid_from, valid_to, usage_limit_per_user, total_usage_limit, current_usage_count, is_active)
VALUES
(1, 'WELCOME50', '50% off on your first order up to Rs 150', 'PERCENTAGE', 50.00, 250.00, 150.00, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 1, 1000, 1, TRUE),
(2, 'FEAST100', 'Flat Rs 100 off on gourmet orders above Rs 500', 'FIXED_AMOUNT', 100.00, 500.00, NULL, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 3, 500, 0, TRUE),
(3, 'FREESHIP', 'Free delivery on orders above Rs 300', 'FIXED_AMOUNT', 40.00, 300.00, NULL, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 5, 2000, 0, TRUE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 10. Table: ingredient (Culinary Raw Materials Catalog)
-- ---------------------------------------------------------------------
INSERT INTO ingredient (ingredient_id, name, category, unit_of_measure)
VALUES
(1, 'Aged Basmati Rice', 'Grains', 'KG'),
(2, 'Fresh Malai Paneer', 'Dairy', 'KG'),
(3, 'Boneless Chicken Breast', 'Meat & Poultry', 'KG'),
(4, 'Sourdough Pizza Dough Balls', 'Bakery', 'PIECE'),
(5, 'Fresh Mozzarella Cheese', 'Dairy', 'KG'),
(6, 'San Marzano Tomato Puree', 'Produce', 'LITER'),
(7, 'Heavy Dairy Cream', 'Dairy', 'LITER'),
(8, 'Extra Virgin Olive Oil', 'Oils & Condiments', 'LITER'),
(9, 'Penne Rigate Pasta', 'Dry Goods', 'KG'),
(10, 'Single Origin Arabica Beans', 'Beverage Dry Goods', 'KG'),
(11, 'Dark Belgian Cocoa Powder', 'Baking', 'KG'),
(12, 'Black Lentils (Urad Dal)', 'Pulses', 'KG')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 11. Table: inventory (Stock Balances for Kitchen 1 & Kitchen 2)
-- ---------------------------------------------------------------------
INSERT INTO inventory (inventory_id, kitchen_id, ingredient_id, current_stock, reorder_level, last_restocked_at)
VALUES
-- Kitchen 1 (Indiranagar)
(1, 1, 1, 45.000, 10.000, '2026-10-25 08:00:00'),
(2, 1, 2, 18.500, 5.000, '2026-10-28 07:30:00'),
(3, 1, 3, 28.000, 8.000, '2026-10-29 07:00:00'),
(4, 1, 4, 90.000, 25.000, '2026-10-30 08:30:00'),
(5, 1, 5, 22.000, 6.000, '2026-10-30 08:30:00'),
(6, 1, 6, 35.000, 10.000, '2026-10-25 09:00:00'),
(7, 1, 7, 14.000, 4.000, '2026-10-29 07:30:00'),
(8, 1, 8, 20.000, 5.000, '2026-10-20 10:00:00'),
(9, 1, 9, 30.000, 8.000, '2026-10-22 11:00:00'),
(10, 1, 10, 12.000, 3.000, '2026-10-26 14:00:00'),
(11, 1, 11, 8.000, 2.000, '2026-10-20 12:00:00'),
(12, 1, 12, 25.000, 5.000, '2026-10-22 10:30:00'),
-- Kitchen 2 (Koramangala)
(13, 2, 1, 30.000, 10.000, '2026-10-27 08:00:00'),
(14, 2, 2, 12.000, 4.000, '2026-10-28 08:00:00'),
(15, 2, 3, 20.000, 6.000, '2026-10-29 08:00:00'),
(16, 2, 4, 60.000, 20.000, '2026-10-30 09:00:00'),
(17, 2, 5, 15.000, 5.000, '2026-10-30 09:00:00')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 12. Table: menu_item_ingredient (Recipe BOM)
-- ---------------------------------------------------------------------
INSERT INTO menu_item_ingredient (menu_item_id, ingredient_id, quantity_required, unit_of_measure)
VALUES
-- Paneer Tikka (Item 1)
(1, 2, 0.200, 'KG'),
(1, 8, 0.020, 'LITER'),
-- Butter Chicken Bowl (Item 3)
(3, 1, 0.150, 'KG'),
(3, 3, 0.180, 'KG'),
(3, 7, 0.050, 'LITER'),
-- Classic Margherita (Item 5)
(5, 4, 1.000, 'PIECE'),
(5, 5, 0.150, 'KG'),
(5, 6, 0.080, 'LITER'),
(5, 8, 0.015, 'LITER'),
-- Truffle Alfredo Penne (Item 8)
(8, 9, 0.120, 'KG'),
(8, 7, 0.060, 'LITER'),
(8, 8, 0.010, 'LITER'),
-- Chocolate Lava Cake (Item 10)
(10, 11, 0.040, 'KG'),
(10, 7, 0.030, 'LITER'),
-- Cold Brew Coffee (Item 12)
(12, 10, 0.035, 'KG')
ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 13. Table: orders (Sample Completed & In-Flight Orders)
-- ---------------------------------------------------------------------
INSERT INTO orders (order_id, order_number, customer_id, kitchen_id, delivery_address_id, order_status, subtotal_amount, discount_amount, tax_amount, delivery_fee, total_amount, applied_coupon_id, special_instructions, estimated_delivery_time, placed_at)
VALUES
-- Order 1: Delivered order for Arjun Mehta from Kitchen 1
(1, 'ORD-20261031-1001', 2, 1, 1, 'DELIVERED', 640.00, 150.00, 24.50, 40.00, 554.50, 1, 'Please ring the doorbell and leave at door', '2026-10-31 13:45:00', '2026-10-31 13:05:00'),
-- Order 2: Out for delivery order for Priya Nair from Kitchen 1
(2, 'ORD-20261031-1002', 3, 1, 3, 'OUT_FOR_DELIVERY', 500.00, 0.00, 25.00, 40.00, 565.00, NULL, 'Extra spicy please', '2026-10-31 16:45:00', '2026-10-31 16:05:00')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 14. Table: order_item (Historical Line Item Snapshots)
-- ---------------------------------------------------------------------
INSERT INTO order_item (order_item_id, order_id, menu_item_id, item_name_snapshot, unit_price_snapshot, quantity, subtotal_price, customization_notes)
VALUES
-- Items in Order 1: Butter Chicken Bowl + Tandoori Paneer Tikka
(1, 1, 3, 'Royal Butter Chicken Bowl', 340.00, 1, 340.00, 'Medium spice level'),
(2, 1, 1, 'Tandoori Paneer Tikka', 260.00, 1, 260.00, 'Mint chutney extra'),
(3, 1, 11, 'Kesar Pista Gulab Jamun (2 pcs)', 120.00, 1, 120.00, NULL),
-- Items in Order 2: Margherita Pizza + Cold Brew Coffee
(4, 2, 5, 'Classic Margherita Pizza', 380.00, 1, 380.00, 'Well done crust'),
(5, 2, 12, 'Cold Brew Arabica Coffee (300ml)', 160.00, 1, 160.00, 'No sugar')
ON DUPLICATE KEY UPDATE order_item_id = order_item_id;

-- ---------------------------------------------------------------------
-- 15. Table: payment (Multiple Gateway Attempts Demonstrated)
-- ---------------------------------------------------------------------
INSERT INTO payment (payment_id, order_id, payment_method, payment_status, transaction_reference, gateway_name, amount, currency, error_message, initiated_at, completed_at)
VALUES
-- Order 1: Attempt 1 Failed (Simulated bank timeout), Attempt 2 Succeeded via UPI
(1, 1, 'CREDIT_CARD', 'FAILED', 'TXN-RAZORPAY-884192A', 'Razorpay', 554.50, 'INR', 'Customer card authentication timed out at gateway', '2026-10-31 13:06:00', '2026-10-31 13:07:30'),
(2, 1, 'UPI', 'SUCCESS', 'TXN-RAZORPAY-884192B', 'Razorpay', 554.50, 'INR', NULL, '2026-10-31 13:08:00', '2026-10-31 13:08:45'),
-- Order 2: Single immediate success
(3, 2, 'UPI', 'SUCCESS', 'TXN-PAYTM-9941021', 'PayTM', 565.00, 'INR', NULL, '2026-10-31 16:06:00', '2026-10-31 16:06:40')
ON DUPLICATE KEY UPDATE payment_id = payment_id;

-- ---------------------------------------------------------------------
-- 16. Table: order_status_history
-- ---------------------------------------------------------------------
INSERT INTO order_status_history (history_id, order_id, previous_status, new_status, changed_by_user_id, notes, created_at)
VALUES
-- Lifecycle for Order 1
(1, 1, NULL, 'PENDING', 2, 'Order initiated by customer', '2026-10-31 13:05:00'),
(2, 1, 'PENDING', 'CONFIRMED', 4, 'Payment verified and sent to Indiranagar kitchen', '2026-10-31 13:09:00'),
(3, 1, 'CONFIRMED', 'PREPARING', 5, 'Chef began food assembly and oven cooking', '2026-10-31 13:12:00'),
(4, 1, 'PREPARING', 'READY_FOR_PICKUP', 5, 'Quality check completed; dispatched to packing counter', '2026-10-31 13:28:00'),
(5, 1, 'READY_FOR_PICKUP', 'OUT_FOR_DELIVERY', 7, 'Courier Rohit Kumar picked up the delivery bag', '2026-10-31 13:31:00'),
(6, 1, 'OUT_FOR_DELIVERY', 'DELIVERED', 7, 'OTP verified and handed over to customer', '2026-10-31 13:48:00'),
-- Lifecycle for Order 2
(7, 2, NULL, 'PENDING', 3, 'Order initiated by customer', '2026-10-31 16:05:00'),
(8, 2, 'PENDING', 'CONFIRMED', 4, 'Payment confirmed', '2026-10-31 16:07:00'),
(9, 2, 'CONFIRMED', 'PREPARING', 5, 'Baking Margherita Pizza', '2026-10-31 16:10:00'),
(10, 2, 'PREPARING', 'READY_FOR_PICKUP', 5, 'Packed and sealed with safety tape', '2026-10-31 16:25:00'),
(11, 2, 'READY_FOR_PICKUP', 'OUT_FOR_DELIVERY', 7, 'Driver on route to customer location', '2026-10-31 16:30:00')
ON DUPLICATE KEY UPDATE history_id = history_id;

-- ---------------------------------------------------------------------
-- 17. Table: inventory_movement (Stock Depletion for Order 1)
-- ---------------------------------------------------------------------
INSERT INTO inventory_movement (movement_id, kitchen_id, ingredient_id, movement_type, quantity_delta, unit_cost, reference_order_id, notes, recorded_by_user_id, created_at)
VALUES
(1, 1, 1, 'CONSUMPTION', -0.150, 42.00, 1, 'Consumed in Butter Chicken Bowl for Order #1', 5, '2026-10-31 13:12:00'),
(2, 1, 3, 'CONSUMPTION', -0.180, 210.00, 1, 'Consumed in Butter Chicken Bowl for Order #1', 5, '2026-10-31 13:12:00'),
(3, 1, 2, 'CONSUMPTION', -0.200, 280.00, 1, 'Consumed in Paneer Tikka for Order #1', 5, '2026-10-31 13:12:00')
ON DUPLICATE KEY UPDATE movement_id = movement_id;

-- ---------------------------------------------------------------------
-- 18. Table: delivery (Fulfillment Records)
-- ---------------------------------------------------------------------
INSERT INTO delivery (delivery_id, order_id, delivery_person_id, delivery_status, assigned_at, picked_up_at, delivered_at, delivery_otp, delivery_notes)
VALUES
(1, 1, 7, 'DELIVERED', '2026-10-31 13:28:00', '2026-10-31 13:31:00', '2026-10-31 13:48:00', '4819', 'Handed over at reception gate security check'),
(2, 2, 7, 'OUT_FOR_DELIVERY', '2026-10-31 16:26:00', '2026-10-31 16:30:00', NULL, '9204', 'Customer requested contactless delivery')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

-- ---------------------------------------------------------------------
-- 19. Table: coupon_usage (Audit Log of Voucher Redemptions)
-- ---------------------------------------------------------------------
INSERT INTO coupon_usage (usage_id, coupon_id, customer_id, order_id, discount_applied, used_at)
VALUES
(1, 1, 2, 1, 150.00, '2026-10-31 13:05:00')
ON DUPLICATE KEY UPDATE usage_id = usage_id;

-- ---------------------------------------------------------------------
-- 20. Table: review (Verified Customer Feedback)
-- ---------------------------------------------------------------------
INSERT INTO review (review_id, order_id, customer_id, kitchen_id, rating, review_text, kitchen_reply, created_at)
VALUES
(1, 1, 2, 1, 5, 'The Butter Chicken Bowl was phenomenal! Food arrived piping hot within 35 minutes. Amazing packaging.', 'Thank you Arjun! Glad you enjoyed the saffron rice and butter chicken recipe.', '2026-10-31 14:15:00')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);

SET FOREIGN_KEY_CHECKS = 1;
