#!/usr/bin/env python3
"""
GourmetCloud - Academic Chen ER Model & Relational Schema Diagram Generator
Principal Database Architect & Academic Visual Engineer

Produces:
1. ER_Model_Cloud_Kitchen.drawio  (Standard Chen Notation XML for diagrams.net / draw.io)
2. ER_Model_Cloud_Kitchen.svg     (Standard Chen Notation Vector SVG)
3. ER_Model_Cloud_Kitchen.png     (High-resolution rasterization >= 4500px)

4. Relational_Schema_Cloud_Kitchen.drawio (Tabular Relational Schema XML for diagrams.net / draw.io)
5. Relational_Schema_Cloud_Kitchen.svg    (Tabular Relational Schema Vector SVG)
6. Relational_Schema_Cloud_Kitchen.png    (High-resolution rasterization >= 4500px)
"""

import os
import sys
import math
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = WORKSPACE_ROOT / "assets" / "diagrams"
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"
RENDERER_SVG_JS = SCRIPTS_DIR / "render_svg_to_png.js"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. COMPREHENSIVE METADATA: 22 Tables, Columns, Key Types, Constraints
# -----------------------------------------------------------------------------

# Table metadata
# col format: (col_name, data_type, key_tag, is_nullable, is_derived, is_multivalued, composite_parent)
SCHEMA_TABLES = {
    "users": {
        "title": "USERS",
        "category": "Strong",
        "domain": "Customer & Authentication",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#1E3A8A",
        "columns": [
            ("user_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("email", "VARCHAR(255)", "UK", False, False, False, None),
            ("phone_number", "VARCHAR(20)", "UK", False, False, False, None),
            ("password_hash", "VARCHAR(255)", "", False, False, False, None),
            ("first_name", "VARCHAR(100)", "", False, False, False, "Name"),
            ("last_name", "VARCHAR(100)", "", False, False, False, "Name"),
            ("role", "ENUM", "IDX", False, False, False, None),
            ("is_active", "BOOLEAN", "IDX", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "customer": {
        "title": "CUSTOMER",
        "category": "Weak",
        "domain": "Customer & Authentication",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#4338CA",
        "columns": [
            ("customer_id", "BIGINT UNSIGNED", "PK, FK", False, False, False, None),
            ("loyalty_points", "INT UNSIGNED", "IDX", False, False, False, None),
            ("dietary_preference", "ENUM", "", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
            ("lifetime_spent", "DECIMAL(10,2)", "", True, True, False, None), # Derived attribute in Chen
        ]
    },
    "staff": {
        "title": "STAFF",
        "category": "Weak",
        "domain": "Kitchen & Restaurant",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#4338CA",
        "columns": [
            ("staff_id", "BIGINT UNSIGNED", "PK, FK1", False, False, False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK2, IDX", False, False, False, None),
            ("staff_role", "ENUM", "IDX", False, False, False, None),
            ("shift_timing", "ENUM", "", False, False, False, None),
            ("hired_date", "DATE", "", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "delivery_person": {
        "title": "DELIVERY_PERSON",
        "category": "Weak",
        "domain": "Payment & Delivery",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#4338CA",
        "columns": [
            ("delivery_person_id", "BIGINT UNSIGNED", "PK, FK", False, False, False, None),
            ("vehicle_type", "ENUM", "", False, False, False, None),
            ("vehicle_number", "VARCHAR(50)", "UK", False, False, False, None),
            ("driving_license_number", "VARCHAR(50)", "UK", False, False, False, None),
            ("current_status", "ENUM", "IDX", False, False, False, None),
            ("current_latitude", "DECIMAL(10,8)", "IDX", True, False, False, "Coordinates"),
            ("current_longitude", "DECIMAL(11,8)", "IDX", True, False, False, "Coordinates"),
            ("rating", "DECIMAL(3,2)", "", False, True, False, None), # Derived rolling average
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "kitchen": {
        "title": "KITCHEN",
        "category": "Strong",
        "domain": "Kitchen & Restaurant",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#0F766E",
        "columns": [
            ("kitchen_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("name", "VARCHAR(150)", "", False, False, False, None),
            ("branch_code", "VARCHAR(50)", "UK", False, False, False, None),
            ("contact_phone", "VARCHAR(20)", "", False, False, False, None),
            ("email", "VARCHAR(255)", "", False, False, False, None),
            ("address_line1", "VARCHAR(255)", "", False, False, False, "Address"),
            ("address_line2", "VARCHAR(255)", "", True, False, False, "Address"),
            ("city", "VARCHAR(100)", "IDX", False, False, False, "Address"),
            ("state", "VARCHAR(100)", "", False, False, False, "Address"),
            ("postal_code", "VARCHAR(20)", "", False, False, False, "Address"),
            ("latitude", "DECIMAL(10,8)", "", True, False, False, "Location"),
            ("longitude", "DECIMAL(11,8)", "", True, False, False, "Location"),
            ("operating_status", "ENUM", "IDX", False, False, False, None),
            ("opening_time", "TIME", "", False, False, False, "Schedule"),
            ("closing_time", "TIME", "", False, False, False, "Schedule"),
            ("max_active_orders", "INT UNSIGNED", "", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "category": {
        "title": "CATEGORY",
        "category": "Strong",
        "domain": "Kitchen & Restaurant",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#0F766E",
        "columns": [
            ("category_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("name", "VARCHAR(100)", "UK", False, False, False, None),
            ("slug", "VARCHAR(120)", "UK", False, False, False, None),
            ("description", "TEXT", "", True, False, False, None),
            ("display_order", "INT UNSIGNED", "IDX", False, False, False, None),
            ("is_active", "BOOLEAN", "IDX", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "cuisine": {
        "title": "CUISINE",
        "category": "Strong",
        "domain": "Kitchen & Restaurant",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#0F766E",
        "columns": [
            ("cuisine_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("cuisine_name", "VARCHAR(100)", "UK", False, False, False, None),
            ("cuisine_slug", "VARCHAR(120)", "UK", False, False, False, None),
            ("cuisine_description", "TEXT", "", True, False, False, None),
            ("cuisine_image_url", "VARCHAR(500)", "", True, False, False, None),
            ("is_active", "BOOLEAN", "IDX", False, False, False, None),
            ("display_order", "INT UNSIGNED", "IDX", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "menu_item": {
        "title": "MENU_ITEM",
        "category": "Strong",
        "domain": "Menu & Recipe BOM",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#0F766E",
        "columns": [
            ("menu_item_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK1, UK, IDX", False, False, False, None),
            ("category_id", "BIGINT UNSIGNED", "FK2, IDX", False, False, False, None),
            ("cuisine_id", "BIGINT UNSIGNED", "FK3, IDX", True, False, False, None),
            ("name", "VARCHAR(150)", "UK", False, False, False, None),
            ("description", "TEXT", "", True, False, False, None),
            ("base_price", "DECIMAL(10,2)", "IDX", False, False, False, None),
            ("is_vegetarian", "BOOLEAN", "IDX", False, False, False, None),
            ("is_available", "BOOLEAN", "IDX", False, False, False, None),
            ("preparation_time_minutes", "SMALLINT UNSIGNED", "", False, False, False, None),
            ("calories", "INT UNSIGNED", "", True, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "address": {
        "title": "ADDRESS",
        "category": "Weak",
        "domain": "Customer & Authentication",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#4338CA",
        "columns": [
            ("address_id", "BIGINT UNSIGNED", "PK, UK", False, False, False, None),
            ("customer_id", "BIGINT UNSIGNED", "FK, UK, IDX", False, False, False, None),
            ("address_label", "VARCHAR(50)", "", False, False, False, None),
            ("recipient_name", "VARCHAR(150)", "", False, False, False, None),
            ("recipient_phone", "VARCHAR(20)", "", False, False, False, None),
            ("address_line1", "VARCHAR(255)", "", False, False, False, "Address"),
            ("address_line2", "VARCHAR(255)", "", True, False, False, "Address"),
            ("landmark", "VARCHAR(150)", "", True, False, False, "Address"),
            ("city", "VARCHAR(100)", "", False, False, False, "Address"),
            ("state", "VARCHAR(100)", "", False, False, False, "Address"),
            ("postal_code", "VARCHAR(20)", "", False, False, False, "Address"),
            ("latitude", "DECIMAL(10,8)", "", True, False, False, "Location"),
            ("longitude", "DECIMAL(11,8)", "", True, False, False, "Location"),
            ("is_default", "BOOLEAN", "IDX", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "coupon": {
        "title": "COUPON",
        "category": "Strong",
        "domain": "Cart & Ordering",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#1E3A8A",
        "columns": [
            ("coupon_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("code", "VARCHAR(50)", "UK", False, False, False, None),
            ("description", "VARCHAR(255)", "", True, False, False, None),
            ("discount_type", "ENUM", "", False, False, False, None),
            ("discount_value", "DECIMAL(10,2)", "", False, False, False, None),
            ("min_order_value", "DECIMAL(10,2)", "", False, False, False, None),
            ("max_discount_amount", "DECIMAL(10,2)", "", True, False, False, None),
            ("valid_from", "DATETIME", "IDX", False, False, False, "Validity"),
            ("valid_to", "DATETIME", "IDX", False, False, False, "Validity"),
            ("usage_limit_per_user", "INT UNSIGNED", "", False, False, False, None),
            ("total_usage_limit", "INT UNSIGNED", "", False, False, False, None),
            ("current_usage_count", "INT UNSIGNED", "", False, True, False, None), # Derived count
            ("is_active", "BOOLEAN", "IDX", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "orders": {
        "title": "ORDERS",
        "category": "Strong",
        "domain": "Cart & Ordering",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#1E3A8A",
        "columns": [
            ("order_id", "BIGINT UNSIGNED", "PK, UK", False, False, False, None),
            ("order_number", "VARCHAR(64)", "UK", False, False, False, None),
            ("customer_id", "BIGINT UNSIGNED", "FK1, IDX", False, False, False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK2, UK, IDX", False, False, False, None),
            ("delivery_address_id", "BIGINT UNSIGNED", "FK3", False, False, False, None),
            ("order_status", "ENUM", "IDX", False, False, False, None),
            ("subtotal_amount", "DECIMAL(10,2)", "", False, False, False, None),
            ("discount_amount", "DECIMAL(10,2)", "", False, False, False, None),
            ("tax_amount", "DECIMAL(10,2)", "", False, False, False, None),
            ("delivery_fee", "DECIMAL(10,2)", "", False, False, False, None),
            ("total_amount", "DECIMAL(10,2)", "", False, True, False, None), # Derived
            ("applied_coupon_id", "BIGINT UNSIGNED", "FK4, IDX", True, False, False, None),
            ("special_instructions", "TEXT", "", True, False, False, None),
            ("estimated_delivery_time", "DATETIME", "", True, False, False, None),
            ("placed_at", "DATETIME(6)", "IDX", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "order_item": {
        "title": "ORDER_ITEM",
        "category": "Weak",
        "domain": "Cart & Ordering",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#4338CA",
        "columns": [
            ("order_item_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("order_id", "BIGINT UNSIGNED", "FK1, IDX", False, False, False, None),
            ("menu_item_id", "BIGINT UNSIGNED", "FK2, IDX", False, False, False, None),
            ("item_name_snapshot", "VARCHAR(150)", "", False, False, False, None),
            ("unit_price_snapshot", "DECIMAL(10,2)", "", False, False, False, None),
            ("quantity", "SMALLINT UNSIGNED", "", False, False, False, None),
            ("subtotal_price", "DECIMAL(10,2)", "", False, True, False, None), # Derived
            ("customization_notes", "VARCHAR(255)", "", True, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "payment": {
        "title": "PAYMENT",
        "category": "Weak",
        "domain": "Payment & Delivery",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#065F46",
        "columns": [
            ("payment_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("order_id", "BIGINT UNSIGNED", "FK, IDX", False, False, False, None),
            ("payment_method", "ENUM", "", False, False, False, None),
            ("payment_status", "ENUM", "IDX", False, False, False, None),
            ("transaction_reference", "VARCHAR(100)", "UK", True, False, False, None),
            ("gateway_name", "VARCHAR(50)", "", True, False, False, None),
            ("amount", "DECIMAL(10,2)", "", False, False, False, None),
            ("currency", "CHAR(3)", "", False, False, False, None),
            ("error_message", "TEXT", "", True, False, False, None),
            ("initiated_at", "DATETIME(6)", "IDX", False, False, False, None),
            ("completed_at", "DATETIME(6)", "", True, False, False, None),
        ]
    },
    "order_status_history": {
        "title": "ORDER_STATUS_HISTORY",
        "category": "Weak",
        "domain": "Cart & Ordering",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#4338CA",
        "columns": [
            ("history_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("order_id", "BIGINT UNSIGNED", "FK1, IDX", False, False, False, None),
            ("previous_status", "ENUM", "", True, False, False, None),
            ("new_status", "ENUM", "", False, False, False, None),
            ("changed_by_user_id", "BIGINT UNSIGNED", "FK2, IDX", True, False, False, None),
            ("notes", "TEXT", "", True, False, False, None),
            ("created_at", "DATETIME(6)", "IDX", False, False, False, None),
        ]
    },
    "ingredient": {
        "title": "INGREDIENT",
        "category": "Strong",
        "domain": "Menu & Recipe BOM",
        "fill": "#E0F2FE",
        "stroke": "#0284C7",
        "header_bg": "#9A3412",
        "columns": [
            ("ingredient_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("name", "VARCHAR(150)", "UK", False, False, False, None),
            ("category", "VARCHAR(100)", "IDX", True, False, False, None),
            ("unit_of_measure", "ENUM", "", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "inventory": {
        "title": "INVENTORY",
        "category": "Associative",
        "domain": "Menu & Recipe BOM",
        "fill": "#CCFBF1",
        "stroke": "#0D9488",
        "header_bg": "#9A3412",
        "columns": [
            ("inventory_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK1, UK, IDX", False, False, False, None),
            ("ingredient_id", "BIGINT UNSIGNED", "FK2, UK, IDX", False, False, False, None),
            ("current_stock", "DECIMAL(10,3)", "IDX", False, False, False, None),
            ("reorder_level", "DECIMAL(10,3)", "IDX", False, False, False, None),
            ("last_restocked_at", "DATETIME", "", True, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
            ("reorder_deficit", "DECIMAL(10,3)", "", True, True, False, None), # Derived
        ]
    },
    "inventory_movement": {
        "title": "INVENTORY_MOVEMENT",
        "category": "Weak",
        "domain": "Menu & Recipe BOM",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#9A3412",
        "columns": [
            ("movement_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK1, IDX", False, False, False, None),
            ("ingredient_id", "BIGINT UNSIGNED", "FK2, IDX", False, False, False, None),
            ("movement_type", "ENUM", "", False, False, False, None),
            ("quantity_delta", "DECIMAL(10,3)", "", False, False, False, None),
            ("unit_cost", "DECIMAL(10,2)", "", True, False, False, None),
            ("reference_order_id", "BIGINT UNSIGNED", "FK3, IDX", True, False, False, None),
            ("notes", "TEXT", "", True, False, False, None),
            ("recorded_by_user_id", "BIGINT UNSIGNED", "FK4", True, False, False, None),
            ("created_at", "DATETIME(6)", "IDX", False, False, False, None),
            ("total_movement_cost", "DECIMAL(10,2)", "", True, True, False, None), # Derived
        ]
    },
    "menu_item_ingredient": {
        "title": "MENU_ITEM_INGREDIENT",
        "category": "Associative",
        "domain": "Menu & Recipe BOM",
        "fill": "#CCFBF1",
        "stroke": "#0D9488",
        "header_bg": "#9A3412",
        "columns": [
            ("menu_item_id", "BIGINT UNSIGNED", "PK, FK1", False, False, False, None),
            ("ingredient_id", "BIGINT UNSIGNED", "PK, FK2, IDX", False, False, False, None),
            ("quantity_required", "DECIMAL(10,3)", "", False, False, False, None),
            ("unit_of_measure", "ENUM", "", False, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "delivery": {
        "title": "DELIVERY",
        "category": "Associative",
        "domain": "Payment & Delivery",
        "fill": "#CCFBF1",
        "stroke": "#0D9488",
        "header_bg": "#065F46",
        "columns": [
            ("delivery_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("order_id", "BIGINT UNSIGNED", "FK1, UK", False, False, False, None),
            ("delivery_person_id", "BIGINT UNSIGNED", "FK2, IDX", False, False, False, None),
            ("delivery_status", "ENUM", "IDX", False, False, False, None),
            ("assigned_at", "DATETIME(6)", "IDX", False, False, False, "Timestamps"),
            ("picked_up_at", "DATETIME(6)", "", True, False, False, "Timestamps"),
            ("delivered_at", "DATETIME(6)", "", True, False, False, "Timestamps"),
            ("delivery_otp", "VARCHAR(6)", "", True, False, False, None),
            ("delivery_notes", "TEXT", "", True, False, False, None),
            ("customer_signature_url", "VARCHAR(255)", "", True, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "coupon_usage": {
        "title": "COUPON_USAGE",
        "category": "Associative",
        "domain": "Cart & Ordering",
        "fill": "#CCFBF1",
        "stroke": "#0D9488",
        "header_bg": "#1E3A8A",
        "columns": [
            ("usage_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("coupon_id", "BIGINT UNSIGNED", "FK1, IDX", False, False, False, None),
            ("customer_id", "BIGINT UNSIGNED", "FK2, IDX", False, False, False, None),
            ("order_id", "BIGINT UNSIGNED", "FK3, UK", False, False, False, None),
            ("discount_applied", "DECIMAL(10,2)", "", False, False, False, None),
            ("used_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "review": {
        "title": "REVIEW",
        "category": "Associative",
        "domain": "Reviews & Feedback",
        "fill": "#CCFBF1",
        "stroke": "#0D9488",
        "header_bg": "#9F1239",
        "columns": [
            ("review_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("order_id", "BIGINT UNSIGNED", "FK1, UK", False, False, False, None),
            ("customer_id", "BIGINT UNSIGNED", "FK2, IDX", False, False, False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK3, IDX", False, False, False, None),
            ("rating", "TINYINT UNSIGNED", "IDX", False, False, False, None),
            ("review_text", "TEXT", "", True, False, False, None),
            ("kitchen_reply", "TEXT", "", True, False, False, None),
            ("created_at", "DATETIME(6)", "", False, False, False, None),
            ("updated_at", "DATETIME(6)", "", False, False, False, None),
        ]
    },
    "admin_audit_log": {
        "title": "ADMIN_AUDIT_LOG",
        "category": "Weak",
        "domain": "Customer & Authentication",
        "fill": "#EDE9FE",
        "stroke": "#7C3AED",
        "header_bg": "#1E3A8A",
        "columns": [
            ("audit_id", "BIGINT UNSIGNED", "PK", False, False, False, None),
            ("actor_user_id", "BIGINT UNSIGNED", "FK, IDX", False, False, False, None),
            ("action", "VARCHAR(100)", "IDX", False, False, False, None),
            ("entity_type", "VARCHAR(50)", "IDX", False, False, False, None),
            ("entity_id", "BIGINT UNSIGNED", "IDX", True, False, False, None),
            ("details", "JSON", "", True, False, False, None),
            ("created_at", "DATETIME(6)", "IDX", False, False, False, None),
        ]
    },
}

# Foreign key referential paths (Child -> Parent)
# (child_tbl, child_col, parent_tbl, parent_col, on_delete, on_update)
SCHEMA_FOREIGN_KEYS = [
    ("customer", "customer_id", "users", "user_id", "RESTRICT", "CASCADE"),
    ("staff", "staff_id", "users", "user_id", "RESTRICT", "CASCADE"),
    ("staff", "kitchen_id", "kitchen", "kitchen_id", "RESTRICT", "CASCADE"),
    ("delivery_person", "delivery_person_id", "users", "user_id", "RESTRICT", "CASCADE"),
    ("address", "customer_id", "customer", "customer_id", "RESTRICT", "CASCADE"),
    ("menu_item", "kitchen_id", "kitchen", "kitchen_id", "RESTRICT", "CASCADE"),
    ("menu_item", "category_id", "category", "category_id", "RESTRICT", "CASCADE"),
    ("menu_item", "cuisine_id", "cuisine", "cuisine_id", "SET NULL", "CASCADE"),
    ("orders", "customer_id", "customer", "customer_id", "RESTRICT", "CASCADE"),
    ("orders", "kitchen_id", "kitchen", "kitchen_id", "RESTRICT", "CASCADE"),
    ("orders", "delivery_address_id", "address", "address_id", "RESTRICT", "CASCADE"),
    ("orders", "applied_coupon_id", "coupon", "coupon_id", "SET NULL", "CASCADE"),
    ("order_item", "order_id", "orders", "order_id", "CASCADE", "CASCADE"),
    ("order_item", "menu_item_id", "menu_item", "menu_item_id", "RESTRICT", "CASCADE"),
    ("payment", "order_id", "orders", "order_id", "RESTRICT", "CASCADE"),
    ("order_status_history", "order_id", "orders", "order_id", "CASCADE", "CASCADE"),
    ("order_status_history", "changed_by_user_id", "users", "user_id", "SET NULL", "CASCADE"),
    ("inventory", "kitchen_id", "kitchen", "kitchen_id", "RESTRICT", "CASCADE"),
    ("inventory", "ingredient_id", "ingredient", "ingredient_id", "RESTRICT", "CASCADE"),
    ("inventory_movement", "kitchen_id", "kitchen", "kitchen_id", "RESTRICT", "CASCADE"),
    ("inventory_movement", "ingredient_id", "ingredient", "ingredient_id", "RESTRICT", "CASCADE"),
    ("inventory_movement", "reference_order_id", "orders", "order_id", "SET NULL", "CASCADE"),
    ("inventory_movement", "recorded_by_user_id", "users", "user_id", "SET NULL", "CASCADE"),
    ("menu_item_ingredient", "menu_item_id", "menu_item", "menu_item_id", "CASCADE", "CASCADE"),
    ("menu_item_ingredient", "ingredient_id", "ingredient", "ingredient_id", "RESTRICT", "CASCADE"),
    ("delivery", "order_id", "orders", "order_id", "RESTRICT", "CASCADE"),
    ("delivery", "delivery_person_id", "delivery_person", "delivery_person_id", "RESTRICT", "CASCADE"),
    ("coupon_usage", "coupon_id", "coupon", "coupon_id", "RESTRICT", "CASCADE"),
    ("coupon_usage", "customer_id", "customer", "customer_id", "RESTRICT", "CASCADE"),
    ("coupon_usage", "order_id", "orders", "order_id", "CASCADE", "CASCADE"),
    ("review", "order_id", "orders", "order_id", "RESTRICT", "CASCADE"),
    ("review", "customer_id", "customer", "customer_id", "RESTRICT", "CASCADE"),
    ("review", "kitchen_id", "kitchen", "kitchen_id", "RESTRICT", "CASCADE"),
    ("admin_audit_log", "actor_user_id", "users", "user_id", "RESTRICT", "CASCADE"),
]

# Chen Relationships: (name, is_identifying, e1, card1, part1, e2, card2, part2, optional_e3_info)
# part: True for total (double line), False for partial (single line)
CHEN_RELATIONSHIPS = [
    ("Is_Customer", True, "users", "1", False, "customer", "1", True, None),
    ("Is_Staff", True, "users", "1", False, "staff", "1", True, None),
    ("Is_Delivery_Person", True, "users", "1", False, "delivery_person", "1", True, None),
    ("Performs_Admin_Action", True, "users", "1", False, "admin_audit_log", "N", True, None),
    ("Employs", False, "kitchen", "1", False, "staff", "N", True, None),
    ("Has_Address", True, "customer", "1", False, "address", "N", True, None),
    ("Prepares", False, "kitchen", "1", False, "menu_item", "N", True, None),
    ("Classifies", False, "category", "1", False, "menu_item", "N", True, None),
    ("Styles", False, "cuisine", "1", False, "menu_item", "N", False, None),
    ("Places", False, "customer", "1", False, "orders", "N", True, None),
    ("Fulfills", False, "kitchen", "1", False, "orders", "N", True, None),
    ("Ships_To", False, "address", "1", False, "orders", "N", True, None),
    ("Discounts", False, "coupon", "1", False, "orders", "N", False, None),
    ("Contains", True, "orders", "1", True, "order_item", "N", True, None),
    ("Includes_Dish", False, "menu_item", "1", False, "order_item", "N", True, None),
    ("Settles_Via", True, "orders", "1", False, "payment", "N", True, None),
    ("Tracks_State", True, "orders", "1", True, "order_status_history", "N", True, None),
    ("Changed_By", False, "users", "1", False, "order_status_history", "N", False, None),
    ("BOM_Formulation", False, "menu_item", "1", True, "menu_item_ingredient", "N", True, ("ingredient", "1", False)),
    ("Stocks", False, "kitchen", "1", False, "inventory", "N", True, ("ingredient", "1", False)),
    ("Audits_Stock", True, "kitchen", "1", False, "inventory_movement", "N", True, ("ingredient", "1", False)),
    ("Consumes_For", False, "orders", "1", False, "inventory_movement", "N", False, None),
    ("Authorized_By", False, "users", "1", False, "inventory_movement", "N", False, None),
    ("Dispatches", False, "orders", "1", False, "delivery", "1", True, None),
    ("Assigned_To", False, "delivery_person", "1", False, "delivery", "N", True, None),
    ("Redeems", False, "coupon", "1", False, "coupon_usage", "N", True, ("customer", "1", False, "orders", "1", True)),
    ("Evaluates", False, "orders", "1", False, "review", "1", True, ("customer", "1", False, "kitchen", "1", False)),
]


# -----------------------------------------------------------------------------
# 2. CHEN ER MODEL SVG & DRAW.IO BUILDER
# -----------------------------------------------------------------------------

def build_chen_er_model():
    """Builds ER_Model_Cloud_Kitchen.svg and ER_Model_Cloud_Kitchen.drawio."""
    print("[-] Constructing Standard Chen ER Model geometry & graph...")

    # Canvas dimensions
    CANVAS_WIDTH = 6400
    CANVAS_HEIGHT = 5200

    # Entity center coordinates layout (organized by 6 functional domains)
    ENTITY_POS = {
        # 1. Customer & Authentication (Top-Left)
        "users": (750, 480),
        "customer": (1850, 480),
        "address": (1850, 1150),
        "admin_audit_log": (750, 1150),

        # 2. Kitchen & Restaurant (Top-Right)
        "kitchen": (3900, 480),
        "staff": (2850, 480),
        "category": (4950, 480),
        "cuisine": (5850, 480),

        # 3. Menu & Recipe BOM & Inventory (Right / Center-Right)
        "menu_item": (4400, 1550),
        "menu_item_ingredient": (4400, 2400),
        "ingredient": (5550, 2400),
        "inventory": (3900, 3250),
        "inventory_movement": (5200, 3250),

        # 4. Cart, Ordering & Promotions (Center / Center-Left)
        "coupon": (750, 2050),
        "coupon_usage": (1850, 2050),
        "orders": (2850, 2050),
        "order_item": (2850, 2900),
        "order_status_history": (1850, 2900),

        # 5. Payment & Delivery Logistics (Bottom-Left / Bottom-Center)
        "payment": (1850, 3950),
        "delivery": (3150, 3950),
        "delivery_person": (4400, 3950),

        # 6. Reviews & Feedback (Bottom-Center-Right)
        "review": (3150, 4750),
    }

    # Generate Attribute Offsets around each entity
    # To prevent attribute collisions, we compute clean radial or staggered fan offsets
    ATTR_OFFSETS = {}
    for ent, tinfo in SCHEMA_TABLES.items():
        cols = tinfo["columns"]
        n = len(cols)
        offsets = []
        # Distribute ovals in two concentric rings or top/bottom/left/right wings
        for i, col in enumerate(cols):
            angle = (2 * math.pi * i) / n - (math.pi / 2)
            # Distance from center
            dist = 220 if (i % 2 == 0) else 310
            dx = math.cos(angle) * dist
            dy = math.sin(angle) * dist
            offsets.append((col, dx, dy))
        ATTR_OFFSETS[ent] = offsets

    # Relationship diamond positions (midpoint between primary entities)
    REL_POS = {}
    for rel in CHEN_RELATIONSHIPS:
        name, is_id, e1, c1, p1, e2, c2, p2 = rel[0], rel[1], rel[2], rel[3], rel[4], rel[5], rel[6], rel[7]
        p1_pt = ENTITY_POS[e1]
        p2_pt = ENTITY_POS[e2]
        mid_x = (p1_pt[0] + p2_pt[0]) / 2
        mid_y = (p1_pt[1] + p2_pt[1]) / 2

        # Small vertical or horizontal jitter for parallel relationships
        if name == "Contains":
            mid_y -= 20
        elif name == "Includes_Dish":
            mid_x += 30
        elif name == "Ships_To":
            mid_y -= 40

        REL_POS[name] = (mid_x, mid_y)

    # -------------------------------------------------------------
    # BUILD SVG
    # -------------------------------------------------------------
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}">',
        '  <defs>',
        '    <filter id="shadow" x="-5%" y="-5%" width="115%" height="115%">',
        '      <feDropShadow dx="2" dy="3" stdDeviation="3" flood-opacity="0.12"/>',
        '    </filter>',
        '  </defs>',
        f'  <rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="#FFFFFF"/>',
        "",
        '  <!-- ================= MASTER HEADER & TITLE ================= -->',
        '  <rect x="120" y="60" width="6160" height="90" rx="10" fill="#0F172A"/>',
        '  <text x="3200" y="115" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="34" font-weight="bold" fill="#FFFFFF">GOURMETCLOUD CLOUD KITCHEN MANAGEMENT PLATFORM — STANDARD CHEN ER MODEL</text>',
        '  <text x="3200" y="135" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="16" fill="#94A3B8">Academic Peter Chen Notation | 22 Entities | 217 Attributes | 27 Academic Relationships | Multi-Domain Normalization</text>',
        "",
        '  <!-- ================= DOMAIN SECTION BOUNDARIES ================= -->',
    ]

    domains_rects = [
        ("1. CUSTOMER & AUTHENTICATION", 120, 180, 2050, 1600, "#F8FAFC", "#E2E8F0"),
        ("2. KITCHEN FACILITIES & RESTAURANTS", 2250, 180, 4030, 850, "#F8FAFC", "#E2E8F0"),
        ("3. MENU CATALOG, RECIPE BOM & INVENTORY", 3650, 1080, 2630, 2550, "#F8FAFC", "#E2E8F0"),
        ("4. CART, ORDERS & PROMOTIONS", 120, 1830, 3450, 1800, "#F8FAFC", "#E2E8F0"),
        ("5. PAYMENT, DISPATCH & FLEET COURIERS", 120, 3680, 4800, 850, "#F8FAFC", "#E2E8F0"),
        ("6. REVIEWS & CUSTOMER FEEDBACK", 2250, 4580, 1800, 520, "#F8FAFC", "#E2E8F0"),
    ]

    for dtitle, dx, dy, dw, dh, dbg, dstr in domains_rects:
        svg_lines.append(f'  <rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" rx="14" fill="{dbg}" stroke="{dstr}" stroke-width="2" stroke-dasharray="8,8"/>')
        svg_lines.append(f'  <text x="{dx+24}" y="{dy+38}" font-family="Helvetica, Arial, sans-serif" font-size="20" font-weight="bold" fill="#475569">{dtitle}</text>')

    # 1. Draw Attribute Connectors & Attribute Ovals
    svg_lines.append("\n  <!-- ================= ATTRIBUTES (OVALS) ================= -->")
    for ent, offsets in ATTR_OFFSETS.items():
        ex, ey = ENTITY_POS[ent]
        for col_tuple, dx, dy in offsets:
            col_name, data_type, key_tag, is_nullable, is_derived, is_multivalued, comp_parent = col_tuple
            ax = ex + dx
            ay = ey + dy

            # Connector line from entity center to attribute center
            svg_lines.append(f'  <line x1="{ex}" y1="{ey}" x2="{ax}" y2="{ay}" stroke="#94A3B8" stroke-width="1.4"/>')

            # Oval styling based on Chen notation rules
            is_pk = "PK" in key_tag
            oval_w = 136
            oval_h = 44
            rx = oval_w / 2
            ry = oval_h / 2

            fill_c = "#FEF3C7" if is_pk else ("#F1F5F9" if is_derived else "#FFFFFF")
            stroke_c = "#D97706" if is_pk else ("#64748B" if is_derived else "#64748B")
            dash_attr = ' stroke-dasharray="5,4"' if is_derived else ''
            stroke_w = "2" if is_pk else "1.5"

            # Draw oval
            svg_lines.append(f'  <ellipse cx="{ax}" cy="{ay}" rx="{rx}" ry="{ry}" fill="{fill_c}" stroke="{stroke_c}" stroke-width="{stroke_w}"{dash_attr} filter="url(#shadow)"/>')

            # Multivalued double oval
            if is_multivalued:
                svg_lines.append(f'  <ellipse cx="{ax}" cy="{ay}" rx="{rx-4}" ry="{ry-4}" fill="none" stroke="{stroke_c}" stroke-width="1.5"/>')

            # Text
            text_decor = ' text-decoration="underline"' if is_pk else ''
            font_wt = ' font-weight="bold"' if is_pk else ''
            font_st = ' font-style="italic"' if is_derived else ''
            label = col_name
            svg_lines.append(f'  <text x="{ax}" y="{ay+4}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="11"{font_wt}{font_st}{text_decor} fill="#0F172A">{label}</text>')

    # 2. Draw Relationship Connectors & Cardinalities
    svg_lines.append("\n  <!-- ================= RELATIONSHIP CONNECTORS & CARDINALITIES ================= -->")
    for rel in CHEN_RELATIONSHIPS:
        name, is_id, e1, c1, p1, e2, c2, p2 = rel[0], rel[1], rel[2], rel[3], rel[4], rel[5], rel[6], rel[7]
        rx, ry = REL_POS[name]
        e1_x, e1_y = ENTITY_POS[e1]
        e2_x, e2_y = ENTITY_POS[e2]

        # Participation 1 (e1 -> rel)
        if p1: # Total participation = double line
            svg_lines.append(f'  <line x1="{e1_x-2}" y1="{e1_y-2}" x2="{rx-2}" y2="{ry-2}" stroke="#0F172A" stroke-width="1.8"/>')
            svg_lines.append(f'  <line x1="{e1_x+2}" y1="{e1_y+2}" x2="{rx+2}" y2="{ry+2}" stroke="#0F172A" stroke-width="1.8"/>')
        else: # Partial = single line
            svg_lines.append(f'  <line x1="{e1_x}" y1="{e1_y}" x2="{rx}" y2="{ry}" stroke="#0F172A" stroke-width="1.8"/>')

        # Participation 2 (e2 -> rel)
        if p2: # Total participation = double line
            svg_lines.append(f'  <line x1="{e2_x-2}" y1="{e2_y-2}" x2="{rx-2}" y2="{ry-2}" stroke="#0F172A" stroke-width="1.8"/>')
            svg_lines.append(f'  <line x1="{e2_x+2}" y1="{e2_y+2}" x2="{rx+2}" y2="{ry+2}" stroke="#0F172A" stroke-width="1.8"/>')
        else: # Partial = single line
            svg_lines.append(f'  <line x1="{e2_x}" y1="{e2_y}" x2="{rx}" y2="{ry}" stroke="#0F172A" stroke-width="1.8"/>')

        # Cardinality text tags
        c1_x = e1_x + (rx - e1_x) * 0.35
        c1_y = e1_y + (ry - e1_y) * 0.35 - 10
        c2_x = e2_x + (rx - e2_x) * 0.35
        c2_y = e2_y + (ry - e2_y) * 0.35 - 10

        svg_lines.append(f'  <circle cx="{c1_x}" cy="{c1_y}" r="11" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.2"/>')
        svg_lines.append(f'  <text x="{c1_x}" y="{c1_y+4}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="bold" fill="#0F172A">{c1}</text>')

        svg_lines.append(f'  <circle cx="{c2_x}" cy="{c2_y}" r="11" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.2"/>')
        svg_lines.append(f'  <text x="{c2_x}" y="{c2_y+4}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="bold" fill="#0F172A">{c2}</text>')

        # Tertiary entity connection if present
        if len(rel) > 8 and rel[8]:
            e3_info = rel[8]
            e3 = e3_info[0]
            c3 = e3_info[1]
            p3 = e3_info[2]
            e3_x, e3_y = ENTITY_POS[e3]
            if p3:
                svg_lines.append(f'  <line x1="{e3_x-2}" y1="{e3_y-2}" x2="{rx-2}" y2="{ry-2}" stroke="#0F172A" stroke-width="1.8"/>')
                svg_lines.append(f'  <line x1="{e3_x+2}" y1="{e3_y+2}" x2="{rx+2}" y2="{ry+2}" stroke="#0F172A" stroke-width="1.8"/>')
            else:
                svg_lines.append(f'  <line x1="{e3_x}" y1="{e3_y}" x2="{rx}" y2="{ry}" stroke="#0F172A" stroke-width="1.8"/>')
            c3_x = e3_x + (rx - e3_x) * 0.35
            c3_y = e3_y + (ry - e3_y) * 0.35 - 10
            svg_lines.append(f'  <circle cx="{c3_x}" cy="{c3_y}" r="11" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.2"/>')
            svg_lines.append(f'  <text x="{c3_x}" y="{c3_y+4}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="bold" fill="#0F172A">{c3}</text>')

    # 3. Draw Relationship Diamonds
    svg_lines.append("\n  <!-- ================= RELATIONSHIPS (DIAMONDS) ================= -->")
    for rel in CHEN_RELATIONSHIPS:
        name, is_id = rel[0], rel[1]
        rx, ry = REL_POS[name]
        rw, rh = 130, 64
        hw = rw / 2
        hh = rh / 2

        poly_pts = f"{rx},{ry-hh} {rx+hw},{ry} {rx},{ry+hh} {rx-hw},{ry}"
        fill_col = "#FED7AA" if is_id else "#FEF08A"
        stroke_col = "#EA580C" if is_id else "#CA8A04"

        svg_lines.append(f'  <polygon points="{poly_pts}" fill="{fill_col}" stroke="{stroke_col}" stroke-width="2" filter="url(#shadow)"/>')
        if is_id: # Double diamond for identifying relationship
            ihw = hw * 0.8
            ihh = hh * 0.8
            inner_pts = f"{rx},{ry-ihh} {rx+ihw},{ry} {rx},{ry+ihh} {rx-ihw},{ry}"
            svg_lines.append(f'  <polygon points="{inner_pts}" fill="none" stroke="{stroke_col}" stroke-width="1.6"/>')

        clean_label = name.replace("_", " ")
        svg_lines.append(f'  <text x="{rx}" y="{ry+4}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="bold" fill="#0F172A">{clean_label}</text>')

    # 4. Draw Entity Rectangles
    svg_lines.append("\n  <!-- ================= ENTITIES (RECTANGLES) ================= -->")
    for ent, tinfo in SCHEMA_TABLES.items():
        ex, ey = ENTITY_POS[ent]
        ew, eh = 170, 60
        hx = ex - ew / 2
        hy = ey - eh / 2

        is_weak = (tinfo["category"] == "Weak")
        fill_c = tinfo["fill"]
        stroke_c = tinfo["stroke"]

        # Outer Rectangle
        svg_lines.append(f'  <rect x="{hx}" y="{hy}" width="{ew}" height="{eh}" rx="2" fill="{fill_c}" stroke="{stroke_c}" stroke-width="2.5" filter="url(#shadow)"/>')

        # Double Rectangle for Weak Entity
        if is_weak:
            svg_lines.append(f'  <rect x="{hx+5}" y="{hy+5}" width="{ew-10}" height="{eh-10}" rx="1" fill="none" stroke="{stroke_c}" stroke-width="1.8"/>')

        # Entity Name
        svg_lines.append(f'  <text x="{ex}" y="{ey+6}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="bold" fill="#0F172A">{tinfo["title"]}</text>')

    # 5. Legend
    svg_lines.append("\n  <!-- ================= CHEN NOTATION LEGEND ================= -->")
    lx, ly = 4900, 4700
    svg_lines.append(f'  <rect x="{lx}" y="{ly}" width="1380" height="380" rx="10" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.8" filter="url(#shadow)"/>')
    svg_lines.append(f'  <text x="{lx+24}" y="{ly+34}" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="bold" fill="#0F172A">STANDARD CHEN ER NOTATION SPECIFICATION KEY</text>')

    # Legend items
    items = [
        ("Strong Entity", "rect", False, "#E0F2FE", "#0284C7"),
        ("Weak Entity", "rect", True, "#EDE9FE", "#7C3AED"),
        ("Simple Attribute", "oval", False, "#FFFFFF", "#64748B"),
        ("Primary Key", "oval_pk", False, "#FEF3C7", "#D97706"),
        ("Multivalued Attribute", "oval_multi", False, "#FFFFFF", "#64748B"),
        ("Derived Attribute", "oval_dash", False, "#F1F5F9", "#64748B"),
        ("Relationship", "diamond", False, "#FEF08A", "#CA8A04"),
        ("Identifying Relationship", "diamond_id", True, "#FED7AA", "#EA580C"),
        ("Total Participation", "line_double", False, "", "#0F172A"),
        ("Partial Participation", "line_single", False, "", "#0F172A"),
    ]

    for idx, (lbl, shape_t, is_dbl, fcol, scol) in enumerate(items):
        col_idx = idx // 5
        row_idx = idx % 5
        ix = lx + 40 + col_idx * 680
        iy = ly + 70 + row_idx * 60

        if shape_t == "rect":
            svg_lines.append(f'  <rect x="{ix}" y="{iy}" width="70" height="34" fill="{fcol}" stroke="{scol}" stroke-width="2"/>')
            if is_dbl:
                svg_lines.append(f'  <rect x="{ix+3}" y="{iy+3}" width="64" height="28" fill="none" stroke="{scol}" stroke-width="1.5"/>')
        elif shape_t == "oval":
            svg_lines.append(f'  <ellipse cx="{ix+35}" cy="{iy+17}" rx="35" ry="17" fill="{fcol}" stroke="{scol}" stroke-width="1.5"/>')
        elif shape_t == "oval_pk":
            svg_lines.append(f'  <ellipse cx="{ix+35}" cy="{iy+17}" rx="35" ry="17" fill="{fcol}" stroke="{scol}" stroke-width="2"/>')
            svg_lines.append(f'  <text x="{ix+35}" y="{iy+21}" text-anchor="middle" font-family="Helvetica" font-size="9" font-weight="bold" text-decoration="underline" fill="#0F172A">PK_attr</text>')
        elif shape_t == "oval_multi":
            svg_lines.append(f'  <ellipse cx="{ix+35}" cy="{iy+17}" rx="35" ry="17" fill="{fcol}" stroke="{scol}" stroke-width="1.5"/>')
            svg_lines.append(f'  <ellipse cx="{ix+35}" cy="{iy+17}" rx="30" ry="13" fill="none" stroke="{scol}" stroke-width="1.5"/>')
        elif shape_t == "oval_dash":
            svg_lines.append(f'  <ellipse cx="{ix+35}" cy="{iy+17}" rx="35" ry="17" fill="{fcol}" stroke="{scol}" stroke-width="1.5" stroke-dasharray="4,4"/>')
        elif shape_t == "diamond":
            svg_lines.append(f'  <polygon points="{ix+35},{iy} {ix+70},{iy+17} {ix+35},{iy+34} {ix},{iy+17}" fill="{fcol}" stroke="{scol}" stroke-width="2"/>')
        elif shape_t == "diamond_id":
            svg_lines.append(f'  <polygon points="{ix+35},{iy} {ix+70},{iy+17} {ix+35},{iy+34} {ix},{iy+17}" fill="{fcol}" stroke="{scol}" stroke-width="2"/>')
            svg_lines.append(f'  <polygon points="{ix+35},{iy+4} {ix+62},{iy+17} {ix+35},{iy+30} {ix+8},{iy+17}" fill="none" stroke="{scol}" stroke-width="1.5"/>')
        elif shape_t == "line_double":
            svg_lines.append(f'  <line x1="{ix}" y1="{iy+15}" x2="{ix+70}" y2="{iy+15}" stroke="{scol}" stroke-width="2"/>')
            svg_lines.append(f'  <line x1="{ix}" y1="{iy+19}" x2="{ix+70}" y2="{iy+19}" stroke="{scol}" stroke-width="2"/>')
        elif shape_t == "line_single":
            svg_lines.append(f'  <line x1="{ix}" y1="{iy+17}" x2="{ix+70}" y2="{iy+17}" stroke="{scol}" stroke-width="2"/>')

        svg_lines.append(f'  <text x="{ix+90}" y="{iy+23}" font-family="Helvetica, Arial, sans-serif" font-size="15" fill="#1E293B">{lbl}</text>')

    svg_lines.append("</svg>")
    svg_content = "\n".join(svg_lines)

    # Write SVG
    er_svg_path = WORKSPACE_ROOT / "ER_Model_Cloud_Kitchen.svg"
    er_svg_path.write_text(svg_content, encoding="utf-8")
    (ASSETS_DIR / "ER_Model_Cloud_Kitchen.svg").write_text(svg_content, encoding="utf-8")
    print(f"[+] Wrote {er_svg_path.name} ({len(svg_content)} bytes)")

    # -------------------------------------------------------------
    # BUILD DRAW.IO XML
    # -------------------------------------------------------------
    mxfile = ET.Element("mxfile", host="Electron", modified="2026-11-19T21:30:00.000Z", agent="DBMS Architect", version="24.0.0", type="device")
    diagram = ET.SubElement(mxfile, "diagram", id="er_model", name="ER Model - Cloud Kitchen")
    model = ET.SubElement(diagram, "mxGraphModel", dx="2000", dy="2000", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=str(CANVAS_WIDTH), pageHeight=str(CANVAS_HEIGHT), math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    elem_id = 2

    # Draw Entities in drawio
    ent_mx_ids = {}
    for ent, tinfo in SCHEMA_TABLES.items():
        ex, ey = ENTITY_POS[ent]
        ew, eh = 170, 60
        hx = ex - ew / 2
        hy = ey - eh / 2

        is_weak = (tinfo["category"] == "Weak")
        if is_weak:
            style = "shape=ext;double=1;rounded=0;whiteSpace=wrap;html=1;fillColor=#EDE9FE;strokeColor=#7C3AED;fontStyle=1;fontSize=13;fontFamily=Helvetica;strokeWidth=2;"
        else:
            style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#E0F2FE;strokeColor=#0284C7;fontStyle=1;fontSize=13;fontFamily=Helvetica;strokeWidth=2;"

        e_cell = ET.SubElement(root, "mxCell", id=f"ent_{ent}", value=tinfo["title"], style=style, vertex="1", parent="1")
        ET.SubElement(e_cell, "mxGeometry", x=str(hx), y=str(hy), width=str(ew), height=str(eh), as_="geometry")
        ent_mx_ids[ent] = f"ent_{ent}"

    # Draw Attributes in drawio
    for ent, offsets in ATTR_OFFSETS.items():
        ex, ey = ENTITY_POS[ent]
        for col_tuple, dx, dy in offsets:
            col_name, data_type, key_tag, is_nullable, is_derived, is_multivalued, _ = col_tuple
            ax = ex + dx
            ay = ey + dy
            ow, oh = 136, 44
            ox = ax - ow / 2
            oy = ay - oh / 2

            is_pk = "PK" in key_tag
            if is_pk:
                style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;fontStyle=1;fontSize=11;fontFamily=Helvetica;strokeWidth=2;"
                val = f"&lt;u&gt;{col_name}&lt;/u&gt;"
            elif is_derived:
                style = "ellipse;dashed=1;dashPattern=4 4;whiteSpace=wrap;html=1;fillColor=#F1F5F9;strokeColor=#64748B;fontStyle=2;fontSize=11;fontFamily=Helvetica;strokeWidth=1.5;"
                val = col_name
            elif is_multivalued:
                style = "shape=ext;double=1;ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#64748B;fontSize=11;fontFamily=Helvetica;strokeWidth=1.5;"
                val = col_name
            else:
                style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#64748B;fontSize=11;fontFamily=Helvetica;strokeWidth=1.5;"
                val = col_name

            attr_id = f"attr_{ent}_{col_name}"
            a_cell = ET.SubElement(root, "mxCell", id=attr_id, value=val, style=style, vertex="1", parent="1")
            ET.SubElement(a_cell, "mxGeometry", x=str(ox), y=str(oy), width=str(ow), height=str(oh), as_="geometry")

            # Connector edge from entity to attribute
            edge_style = "endArrow=none;html=1;strokeColor=#94A3B8;strokeWidth=1.5;"
            ed = ET.SubElement(root, "mxCell", id=f"edge_{attr_id}", style=edge_style, edge="1", parent="1", source=ent_mx_ids[ent], target=attr_id)
            ET.SubElement(ed, "mxGeometry", relative="1", as_="geometry")

    # Draw Relationships in drawio
    for rel in CHEN_RELATIONSHIPS:
        name, is_id, e1, c1, p1, e2, c2, p2 = rel[0], rel[1], rel[2], rel[3], rel[4], rel[5], rel[6], rel[7]
        rx, ry = REL_POS[name]
        rw, rh = 130, 64
        rx_box = rx - rw / 2
        ry_box = ry - rh / 2

        if is_id:
            rstyle = "shape=ext;double=1;rhombus;whiteSpace=wrap;html=1;fillColor=#FED7AA;strokeColor=#EA580C;fontStyle=1;fontSize=11;fontFamily=Helvetica;strokeWidth=2;"
        else:
            rstyle = "rhombus;whiteSpace=wrap;html=1;fillColor=#FEF08A;strokeColor=#CA8A04;fontStyle=1;fontSize=11;fontFamily=Helvetica;strokeWidth=2;"

        rel_cell_id = f"rel_{name}"
        clean_name = name.replace("_", " ")
        rc = ET.SubElement(root, "mxCell", id=rel_cell_id, value=clean_name, style=rstyle, vertex="1", parent="1")
        ET.SubElement(rc, "mxGeometry", x=str(rx_box), y=str(ry_box), width=str(rw), height=str(rh), as_="geometry")

        # Edge from e1 to rel
        edge_style1 = "endArrow=none;html=1;strokeColor=#0F172A;strokeWidth=3;" if p1 else "endArrow=none;html=1;strokeColor=#0F172A;strokeWidth=1.8;"
        ed1 = ET.SubElement(root, "mxCell", id=f"edge_{rel_cell_id}_{e1}", value=c1, style=edge_style1, edge="1", parent="1", source=ent_mx_ids[e1], target=rel_cell_id)
        ET.SubElement(ed1, "mxGeometry", relative="1", as_="geometry")

        # Edge from rel to e2
        edge_style2 = "endArrow=none;html=1;strokeColor=#0F172A;strokeWidth=3;" if p2 else "endArrow=none;html=1;strokeColor=#0F172A;strokeWidth=1.8;"
        ed2 = ET.SubElement(root, "mxCell", id=f"edge_{rel_cell_id}_{e2}", value=c2, style=edge_style2, edge="1", parent="1", source=rel_cell_id, target=ent_mx_ids[e2])
        ET.SubElement(ed2, "mxGeometry", relative="1", as_="geometry")

    er_drawio_path = WORKSPACE_ROOT / "ER_Model_Cloud_Kitchen.drawio"
    ET.ElementTree(mxfile).write(er_drawio_path, encoding="utf-8", xml_declaration=True)
    ET.ElementTree(mxfile).write(ASSETS_DIR / "ER_Model_Cloud_Kitchen.drawio", encoding="utf-8", xml_declaration=True)
    print(f"[+] Wrote {er_drawio_path.name}")


# -----------------------------------------------------------------------------
# 3. RELATIONAL SCHEMA DIAGRAM SVG & DRAW.IO BUILDER
# -----------------------------------------------------------------------------

def build_relational_schema():
    """Builds Relational_Schema_Cloud_Kitchen.svg and Relational_Schema_Cloud_Kitchen.drawio."""
    print("[-] Constructing Physical Relational Schema geometry & table boxes...")

    CANVAS_WIDTH = 5800
    CANVAS_HEIGHT = 4400

    # Layout tables in 5 balanced columns
    # Col 1: users, customer, address, admin_audit_log
    # Col 2: kitchen, staff, category, cuisine, delivery_person
    # Col 3: menu_item, menu_item_ingredient, ingredient, inventory, inventory_movement
    # Col 4: orders, order_item, coupon, coupon_usage
    # Col 5: payment, order_status_history, delivery, review

    COL_X = {
        1: 220,
        2: 1350,
        3: 2480,
        4: 3610,
        5: 4740,
    }

    TABLE_PLACEMENT = {
        # Col 1: Users & Auth
        "users": (1, 240),
        "customer": (1, 980),
        "address": (1, 1540),
        "admin_audit_log": (1, 2680),

        # Col 2: Kitchen Facilities & Classifications
        "kitchen": (2, 240),
        "staff": (2, 1340),
        "category": (2, 1920),
        "cuisine": (2, 2520),
        "delivery_person": (2, 3160),

        # Col 3: Menu & Recipe BOM & Inventory
        "menu_item": (3, 240),
        "menu_item_ingredient": (3, 1020),
        "ingredient": (3, 1520),
        "inventory": (3, 2060),
        "inventory_movement": (3, 2740),

        # Col 4: Orders & Cart & Promotions
        "orders": (4, 240),
        "order_item": (4, 1220),
        "coupon": (4, 1860),
        "coupon_usage": (4, 2760),

        # Col 5: Fulfillment, Payments & Feedback
        "payment": (5, 240),
        "order_status_history": (5, 960),
        "delivery": (5, 1540),
        "review": (5, 2340),
    }

    TABLE_WIDTH = 340
    ROW_HEIGHT = 28
    HEADER_HEIGHT = 42

    # Calculate exact (x, y) coordinates for tables and column rows
    TABLE_COORDS = {}
    ROW_PORTS = {} # key: (table, col_name) -> (x, y, width)

    for tname, (col_idx, y_pos) in TABLE_PLACEMENT.items():
        x_pos = COL_X[col_idx]
        cols = SCHEMA_TABLES[tname]["columns"]
        height = HEADER_HEIGHT + len(cols) * ROW_HEIGHT
        TABLE_COORDS[tname] = (x_pos, y_pos, TABLE_WIDTH, height)

        for r_idx, col_tuple in enumerate(cols):
            col_name = col_tuple[0]
            row_y = y_pos + HEADER_HEIGHT + r_idx * ROW_HEIGHT + ROW_HEIGHT / 2
            ROW_PORTS[(tname, col_name)] = (x_pos, row_y, TABLE_WIDTH)

    # -------------------------------------------------------------
    # BUILD RELATIONAL SVG
    # -------------------------------------------------------------
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}">',
        '  <defs>',
        '    <filter id="tbl_shadow" x="-5%" y="-5%" width="112%" height="112%">',
        '      <feDropShadow dx="3" dy="4" stdDeviation="4" flood-opacity="0.14"/>',
        '    </filter>',
        '    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#2563EB"/>',
        '    </marker>',
        '    <marker id="arrow_accent" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#7C3AED"/>',
        '    </marker>',
        '    <marker id="arrow_green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#0D9488"/>',
        '    </marker>',
        '  </defs>',
        f'  <rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="#FFFFFF"/>',
        "",
        '  <!-- ================= MASTER HEADER & BANNER ================= -->',
        '  <rect x="120" y="50" width="5560" height="100" rx="10" fill="#0F172A"/>',
        '  <text x="2900" y="105" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="34" font-weight="bold" fill="#FFFFFF">GOURMETCLOUD RELATIONAL DATABASE SCHEMA SPECIFICATION</text>',
        '  <text x="2900" y="132" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="16" fill="#94A3B8">Physical Relational Schema | 22 Normalized Tables | 217 Columns | 34 Foreign Key Constraints | 1NF, 2NF, 3NF & BCNF Verified</text>',
        "",
        '  <!-- ================= FOREIGN KEY DIRECTIONAL CONNECTORS ================= -->',
    ]

    # Draw Directed Foreign Key Connectors
    # Route orthogonally from child FK row to parent PK row
    edge_colors = ["#2563EB", "#7C3AED", "#0D9488", "#C026D3", "#D97706", "#2563EB", "#0284C7"]

    for idx, (child, c_col, parent, p_col, on_del, on_upd) in enumerate(SCHEMA_FOREIGN_KEYS):
        c_x, c_y, c_w = ROW_PORTS[(child, c_col)]
        p_x, p_y, p_w = ROW_PORTS[(parent, p_col)]

        color = edge_colors[idx % len(edge_colors)]
        marker = "url(#arrow)" if color == "#2563EB" else ("url(#arrow_accent)" if color == "#7C3AED" else "url(#arrow_green)")

        # Decide whether to exit left or right
        if c_x < p_x:
            # Child is to the left of parent: exit child right, enter parent left
            x_start = c_x + c_w
            x_end = p_x
            mid_x = x_start + (x_end - x_start) / 2 + ((idx % 5) - 2) * 15
            path_d = f"M {x_start} {c_y} L {mid_x} {c_y} L {mid_x} {p_y} L {x_end} {p_y}"
        elif c_x > p_x:
            # Child is to the right of parent: exit child left, enter parent right
            x_start = c_x
            x_end = p_x + p_w
            mid_x = x_start - (x_start - x_end) / 2 + ((idx % 5) - 2) * 15
            path_d = f"M {x_start} {c_y} L {mid_x} {c_y} L {mid_x} {p_y} L {x_end} {p_y}"
        else:
            # In same column: loop out to the left or right
            loop_x = c_x - 40 - (idx % 4) * 20
            path_d = f"M {c_x} {c_y} L {loop_x} {c_y} L {loop_x} {p_y} L {p_x} {p_y}"

        svg_lines.append(f'  <path d="{path_d}" fill="none" stroke="{color}" stroke-width="2" marker-end="{marker}" stroke-linejoin="round" opacity="0.85"/>')

    # Draw Table Boxes
    svg_lines.append("\n  <!-- ================= RELATIONAL TABLE BOXES ================= -->")
    for tname, (tx, ty, tw, th) in TABLE_COORDS.items():
        tinfo = SCHEMA_TABLES[tname]
        hbg = tinfo["header_bg"]
        cols = tinfo["columns"]

        # Outer Table Container
        svg_lines.append(f'  <g filter="url(#tbl_shadow)">')
        svg_lines.append(f'    <rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.8"/>')

        # Shaded Header
        svg_lines.append(f'    <path d="M {tx} {ty+6} Q {tx} {ty} {tx+6} {ty} L {tx+tw-6} {ty} Q {tx+tw} {ty} {tx+tw} {ty+6} L {tx+tw} {ty+HEADER_HEIGHT} L {tx} {ty+HEADER_HEIGHT} Z" fill="{hbg}"/>')
        svg_lines.append(f'    <text x="{tx+tw/2}" y="{ty+27}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="bold" fill="#FFFFFF">{tinfo["title"]}</text>')

        # Divider between Key column and Attribute column
        key_col_w = 75
        attr_col_x = tx + key_col_w
        svg_lines.append(f'    <line x1="{attr_col_x}" y1="{ty+HEADER_HEIGHT}" x2="{attr_col_x}" y2="{ty+th}" stroke="#E2E8F0" stroke-width="1.2"/>')

        # Rows
        for r_idx, col_tuple in enumerate(cols):
            col_name, data_type, key_tag, is_nullable, is_derived, is_multivalued, _ = col_tuple
            ry = ty + HEADER_HEIGHT + r_idx * ROW_HEIGHT

            # Alternating subtle row striping
            if r_idx % 2 == 1:
                svg_lines.append(f'    <rect x="{tx+1}" y="{ry}" width="{tw-2}" height="{ROW_HEIGHT}" fill="#F8FAFC"/>')

            # Row bottom divider
            svg_lines.append(f'    <line x1="{tx}" y1="{ry+ROW_HEIGHT}" x2="{tx+tw}" y2="{ry+ROW_HEIGHT}" stroke="#E2E8F0" stroke-width="1"/>')

            # Key Tag styling
            key_fill = "#D97706" if "PK" in key_tag else ("#2563EB" if "FK" in key_tag else "#64748B")
            key_weight = "bold" if ("PK" in key_tag or "FK" in key_tag) else "normal"
            svg_lines.append(f'    <text x="{tx+36}" y="{ry+18}" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="{key_weight}" fill="{key_fill}">{key_tag}</text>')

            # Attribute Name
            attr_weight = "bold" if "PK" in key_tag else "normal"
            svg_lines.append(f'    <text x="{attr_col_x+10}" y="{ry+18}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="{attr_weight}" fill="#0F172A">{col_name}</text>')

        svg_lines.append("  </g>")

    # Relational Legend
    svg_lines.append("\n  <!-- ================= RELATIONAL SCHEMA LEGEND ================= -->")
    rlx, rly = 3610, 3450
    svg_lines.append(f'  <g filter="url(#tbl_shadow)">')
    svg_lines.append(f'    <rect x="{rlx}" y="{rly}" width="2000" height="260" rx="8" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.8"/>')
    svg_lines.append(f'    <rect x="{rlx}" y="{rly}" width="2000" height="40" rx="8" fill="#0F172A"/>')
    svg_lines.append(f'    <text x="{rlx+1000}" y="{rly+26}" text-anchor="middle" font-family="Helvetica" font-size="16" font-weight="bold" fill="#FFFFFF">RELATIONAL SCHEMA NOTATION & FOREIGN KEY MAPPING KEY</text>')

    r_items = [
        ("PK", "Primary Key (Unique Record Identifier)"),
        ("FK", "Foreign Key (Referential Integrity Constraint)"),
        ("PK, FK", "Primary Key and Foreign Key Simultaneously (Subtype & Junction Tables)"),
        ("UK", "Candidate Unique Key (Alternate Identifier)"),
        ("IDX", "Performance Secondary B-Tree Index"),
        ("-->", "Referential Integrity Directed Pointer (Child FK -> Parent PK)"),
    ]

    for idx, (code, desc) in enumerate(r_items):
        rx_i = rlx + 60 + (idx // 3) * 980
        ry_i = rly + 75 + (idx % 3) * 60
        svg_lines.append(f'    <rect x="{rx_i}" y="{ry_i}" width="100" height="30" rx="4" fill="#F1F5F9" stroke="#94A3B8" stroke-width="1.2"/>')
        svg_lines.append(f'    <text x="{rx_i+50}" y="{ry_i+20}" text-anchor="middle" font-family="Helvetica" font-size="11" font-weight="bold" fill="#0F172A">{code}</text>')
        svg_lines.append(f'    <text x="{rx_i+120}" y="{ry_i+20}" font-family="Helvetica" font-size="13" fill="#334155">{desc}</text>')

    svg_lines.append("  </g>")

    svg_lines.append("</svg>")
    rel_svg_content = "\n".join(svg_lines)

    # Write Relational SVG
    rel_svg_path = WORKSPACE_ROOT / "Relational_Schema_Cloud_Kitchen.svg"
    rel_svg_path.write_text(rel_svg_content, encoding="utf-8")
    (ASSETS_DIR / "Relational_Schema_Cloud_Kitchen.svg").write_text(rel_svg_content, encoding="utf-8")
    print(f"[+] Wrote {rel_svg_path.name} ({len(rel_svg_content)} bytes)")

    # -------------------------------------------------------------
    # BUILD RELATIONAL DRAW.IO XML
    # -------------------------------------------------------------
    mxfile = ET.Element("mxfile", host="Electron", modified="2026-11-19T21:30:00.000Z", agent="DBMS Architect", version="24.0.0", type="device")
    diagram = ET.SubElement(mxfile, "diagram", id="relational_schema", name="Relational Schema - Cloud Kitchen")
    model = ET.SubElement(diagram, "mxGraphModel", dx="2000", dy="2000", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=str(CANVAS_WIDTH), pageHeight=str(CANVAS_HEIGHT), math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    table_cell_ids = {}
    row_cell_ids = {}

    for tname, (tx, ty, tw, th) in TABLE_COORDS.items():
        tinfo = SCHEMA_TABLES[tname]
        cols = tinfo["columns"]
        hbg = tinfo["header_bg"]

        # Table Swimlane Container
        tbl_id = f"tbl_{tname}"
        table_cell_ids[tname] = tbl_id
        t_style = f"swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize={HEADER_HEIGHT};horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;html=1;fillColor={hbg};fontColor=#FFFFFF;strokeColor=#0F172A;fontSize=14;fontFamily=Helvetica;"
        tc = ET.SubElement(root, "mxCell", id=tbl_id, value=tinfo["title"], style=t_style, vertex="1", parent="1")
        ET.SubElement(tc, "mxGeometry", x=str(tx), y=str(ty), width=str(tw), height=str(th), as_="geometry")

        for r_idx, col_tuple in enumerate(cols):
            col_name, data_type, key_tag, _, _, _, _ = col_tuple
            row_id = f"row_{tname}_{col_name}"
            row_cell_ids[(tname, col_name)] = row_id

            row_val = f"&lt;b&gt;{key_tag}&lt;/b&gt; | {col_name}"
            r_style = "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=8;spacingRight=8;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;html=1;fontSize=11;fontFamily=Helvetica;"
            rc = ET.SubElement(root, "mxCell", id=row_id, value=row_val, style=r_style, vertex="1", parent=tbl_id)
            ET.SubElement(rc, "mxGeometry", y=str(HEADER_HEIGHT + r_idx * ROW_HEIGHT), width=str(tw), height=str(ROW_HEIGHT), as_="geometry")

    # Draw foreign key connectors in drawio
    for idx, (child, c_col, parent, p_col, on_del, on_upd) in enumerate(SCHEMA_FOREIGN_KEYS):
        c_cell = row_cell_ids[(child, c_col)]
        p_cell = row_cell_ids[(parent, p_col)]
        e_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2563EB;strokeWidth=1.5;endArrow=block;endFill=1;"
        lbl = f"{on_del}/{on_upd}"
        edge = ET.SubElement(root, "mxCell", id=f"fk_edge_{child}_{c_col}_{parent}", value=lbl, style=e_style, edge="1", parent="1", source=c_cell, target=p_cell)
        ET.SubElement(edge, "mxGeometry", relative="1", as_="geometry")

    rel_drawio_path = WORKSPACE_ROOT / "Relational_Schema_Cloud_Kitchen.drawio"
    ET.ElementTree(mxfile).write(rel_drawio_path, encoding="utf-8", xml_declaration=True)
    ET.ElementTree(mxfile).write(ASSETS_DIR / "Relational_Schema_Cloud_Kitchen.drawio", encoding="utf-8", xml_declaration=True)
    print(f"[+] Wrote {rel_drawio_path.name}")


# -----------------------------------------------------------------------------
# 4. RASTERIZE SVGS TO HIGH-RESOLUTION PNGS VIA PUPPETEER
# -----------------------------------------------------------------------------

def rasterize_diagrams():
    """Compiles SVG files into high-resolution publication PNGs using headless browser."""
    print("[-] Rasterizing diagrams to ultra-high-resolution PNGs (>= 4500px)...")

    node_bin = shutil.which("node")
    if not node_bin:
        raise RuntimeError("Node.js executable is required for headless browser rasterization!")

    # 1. ER Model PNG
    er_svg = WORKSPACE_ROOT / "ER_Model_Cloud_Kitchen.svg"
    er_png = WORKSPACE_ROOT / "ER_Model_Cloud_Kitchen.png"
    er_assets_png = ASSETS_DIR / "ER_Model_Cloud_Kitchen.png"

    print(f"[*] Rasterizing {er_png.name} (target width: 4800px)...")
    subprocess.run([node_bin, str(RENDERER_SVG_JS), str(er_svg), str(er_png), "4800"], check=True)
    shutil.copyfile(er_png, er_assets_png)

    # 2. Relational Schema PNG
    rel_svg = WORKSPACE_ROOT / "Relational_Schema_Cloud_Kitchen.svg"
    rel_png = WORKSPACE_ROOT / "Relational_Schema_Cloud_Kitchen.png"
    rel_assets_png = ASSETS_DIR / "Relational_Schema_Cloud_Kitchen.png"

    print(f"[*] Rasterizing {rel_png.name} (target width: 4800px)...")
    subprocess.run([node_bin, str(RENDERER_SVG_JS), str(rel_svg), str(rel_png), "4800"], check=True)
    shutil.copyfile(rel_png, rel_assets_png)


# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION & VERIFICATION
# -----------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("GOURMETCLOUD CHEN ER & RELATIONAL SCHEMA ARTIFACT SUITE")
    print("=" * 70)

    # 1. Generate Chen ER artifacts
    build_chen_er_model()

    # 2. Generate Relational Schema artifacts
    build_relational_schema()

    # 3. Rasterize to high-res PNG
    rasterize_diagrams()

    # 4. Artifact Verification
    print("\n" + "=" * 70)
    print("GENERATED ARTIFACT VERIFICATION SUMMARY")
    print("=" * 70)

    expected_files = [
        WORKSPACE_ROOT / "ER_Model_Cloud_Kitchen.drawio",
        WORKSPACE_ROOT / "ER_Model_Cloud_Kitchen.svg",
        WORKSPACE_ROOT / "ER_Model_Cloud_Kitchen.png",
        WORKSPACE_ROOT / "Relational_Schema_Cloud_Kitchen.drawio",
        WORKSPACE_ROOT / "Relational_Schema_Cloud_Kitchen.svg",
        WORKSPACE_ROOT / "Relational_Schema_Cloud_Kitchen.png",
        ASSETS_DIR / "ER_Model_Cloud_Kitchen.drawio",
        ASSETS_DIR / "ER_Model_Cloud_Kitchen.svg",
        ASSETS_DIR / "ER_Model_Cloud_Kitchen.png",
        ASSETS_DIR / "Relational_Schema_Cloud_Kitchen.drawio",
        ASSETS_DIR / "Relational_Schema_Cloud_Kitchen.svg",
        ASSETS_DIR / "Relational_Schema_Cloud_Kitchen.png",
    ]

    for p in expected_files:
        if p.exists() and p.stat().st_size > 0:
            kb = p.stat().st_size / 1024
            print(f"[PASS] {p.name:36} ({kb:8.1f} KB) -> {p.relative_to(WORKSPACE_ROOT)}")
        else:
            print(f"[FAIL] Missing or empty: {p}")
            sys.exit(1)

    print("\n[SUCCESS] All academic ER and Relational Schema deliverables generated successfully.")


if __name__ == "__main__":
    main()
