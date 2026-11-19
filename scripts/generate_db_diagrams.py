#!/usr/bin/env python3
"""
GourmetCloud Database Diagram Generation & Verification Suite
Principal Database Architect & Data Visualization Tooling

Generates:
1. assets/diagrams/er_model.dot & er_model.png (Conceptual/Logical Crow's Foot ER Diagram)
2. assets/diagrams/relational_schema.dot & relational_schema.png (Physical Relational Schema Diagram)
3. assets/diagrams/er_model.mmd (Mermaid.js source)
4. assets/diagrams/relational_schema.mmd (Mermaid.js source)

Renders high-resolution 300 DPI publication-grade diagrams using Graphviz dot,
with automatic fallback to Node.js / @viz-js/viz + Puppeteer headless browser rasterization.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = WORKSPACE_ROOT / "assets" / "diagrams"
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"
RENDERER_JS = SCRIPTS_DIR / "render_diagrams.js"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 1. METADATA CATALOG: All 22 Normalized Tables & Relationships
# ----------------------------------------------------------------------

TABLES = {
    "users": {
        "category": "strong",
        "header_color": "#1E3A8A",
        "cluster": "cluster_identity",
        "columns": [
            ("user_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("email", "VARCHAR(255)", "UK", False, None),
            ("phone_number", "VARCHAR(20)", "UK", False, None),
            ("password_hash", "VARCHAR(255)", "", False, None),
            ("first_name", "VARCHAR(100)", "", False, None),
            ("last_name", "VARCHAR(100)", "", False, None),
            ("role", "ENUM('CUSTOMER','ADMIN','KITCHEN_STAFF','DELIVERY_PERSON')", "IDX", False, None),
            ("is_active", "BOOLEAN", "IDX", False, "TRUE"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "customer": {
        "category": "subtype",
        "header_color": "#2563EB",
        "cluster": "cluster_identity",
        "columns": [
            ("customer_id", "BIGINT UNSIGNED", "PK_FK", False, None),
            ("loyalty_points", "INT UNSIGNED", "IDX", False, "0"),
            ("dietary_preference", "ENUM('ALL','VEGETARIAN','VEGAN','HALAL','GLUTEN_FREE')", "", False, "'ALL'"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "staff": {
        "category": "subtype",
        "header_color": "#2563EB",
        "cluster": "cluster_identity",
        "columns": [
            ("staff_id", "BIGINT UNSIGNED", "PK_FK", False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("staff_role", "ENUM('KITCHEN_MANAGER','HEAD_CHEF','LINE_COOK','PACKER','INVENTORY_CONTROLLER')", "IDX", False, None),
            ("shift_timing", "ENUM('MORNING','EVENING','NIGHT','ROTATING')", "", False, "'MORNING'"),
            ("hired_date", "DATE", "", False, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "delivery_person": {
        "category": "subtype",
        "header_color": "#2563EB",
        "cluster": "cluster_identity",
        "columns": [
            ("delivery_person_id", "BIGINT UNSIGNED", "PK_FK", False, None),
            ("vehicle_type", "ENUM('MOTORCYCLE','SCOOTER','BICYCLE','ELECTRIC_VEHICLE')", "", False, None),
            ("vehicle_number", "VARCHAR(50)", "UK", False, None),
            ("driving_license_number", "VARCHAR(50)", "UK", False, None),
            ("current_status", "ENUM('AVAILABLE','ON_DELIVERY','OFF_DUTY')", "IDX", False, "'AVAILABLE'"),
            ("current_latitude", "DECIMAL(10,8)", "IDX", True, None),
            ("current_longitude", "DECIMAL(11,8)", "IDX", True, None),
            ("rating", "DECIMAL(3,2)", "", False, "5.00"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "address": {
        "category": "weak",
        "header_color": "#7C2D12",
        "cluster": "cluster_identity",
        "columns": [
            ("address_id", "BIGINT UNSIGNED", "PK_UK", False, "AUTO_INCREMENT"),
            ("customer_id", "BIGINT UNSIGNED", "FK_UK_IDX", False, None),
            ("address_label", "VARCHAR(50)", "", False, "'Home'"),
            ("recipient_name", "VARCHAR(150)", "", False, None),
            ("recipient_phone", "VARCHAR(20)", "", False, None),
            ("address_line1", "VARCHAR(255)", "", False, None),
            ("address_line2", "VARCHAR(255)", "", True, None),
            ("landmark", "VARCHAR(150)", "", True, None),
            ("city", "VARCHAR(100)", "", False, None),
            ("state", "VARCHAR(100)", "", False, None),
            ("postal_code", "VARCHAR(20)", "", False, None),
            ("latitude", "DECIMAL(10,8)", "", True, None),
            ("longitude", "DECIMAL(11,8)", "", True, None),
            ("is_default", "BOOLEAN", "IDX", False, "FALSE"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "admin_audit_log": {
        "category": "audit",
        "header_color": "#7C2D12",
        "cluster": "cluster_identity",
        "columns": [
            ("audit_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("actor_user_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("action", "VARCHAR(100)", "IDX", False, None),
            ("entity_type", "VARCHAR(50)", "IDX", False, None),
            ("entity_id", "BIGINT UNSIGNED", "IDX", True, None),
            ("details", "JSON", "", True, None),
            ("created_at", "DATETIME(6)", "IDX", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "kitchen": {
        "category": "strong",
        "header_color": "#1E3A8A",
        "cluster": "cluster_catalog",
        "columns": [
            ("kitchen_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("name", "VARCHAR(150)", "", False, None),
            ("branch_code", "VARCHAR(50)", "UK", False, None),
            ("contact_phone", "VARCHAR(20)", "", False, None),
            ("email", "VARCHAR(255)", "", False, None),
            ("address_line1", "VARCHAR(255)", "", False, None),
            ("address_line2", "VARCHAR(255)", "", True, None),
            ("city", "VARCHAR(100)", "IDX", False, None),
            ("state", "VARCHAR(100)", "", False, None),
            ("postal_code", "VARCHAR(20)", "", False, None),
            ("latitude", "DECIMAL(10,8)", "", True, None),
            ("longitude", "DECIMAL(11,8)", "", True, None),
            ("operating_status", "ENUM('ACTIVE','INACTIVE','MAINTENANCE')", "IDX", False, "'ACTIVE'"),
            ("opening_time", "TIME", "", False, "'08:00:00'"),
            ("closing_time", "TIME", "", False, "'23:00:00'"),
            ("max_active_orders", "INT UNSIGNED", "", False, "50"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "category": {
        "category": "strong",
        "header_color": "#1E3A8A",
        "cluster": "cluster_catalog",
        "columns": [
            ("category_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("name", "VARCHAR(100)", "UK", False, None),
            ("slug", "VARCHAR(120)", "UK", False, None),
            ("description", "TEXT", "", True, None),
            ("display_order", "INT UNSIGNED", "IDX", False, "0"),
            ("is_active", "BOOLEAN", "IDX", False, "TRUE"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "cuisine": {
        "category": "strong",
        "header_color": "#1E3A8A",
        "cluster": "cluster_catalog",
        "columns": [
            ("cuisine_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("cuisine_name", "VARCHAR(100)", "UK", False, None),
            ("cuisine_slug", "VARCHAR(120)", "UK", False, None),
            ("cuisine_description", "TEXT", "", True, None),
            ("cuisine_image_url", "VARCHAR(500)", "", True, None),
            ("is_active", "BOOLEAN", "IDX", False, "TRUE"),
            ("display_order", "INT UNSIGNED", "IDX", False, "0"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "menu_item": {
        "category": "subtype",
        "header_color": "#2563EB",
        "cluster": "cluster_catalog",
        "columns": [
            ("menu_item_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("kitchen_id", "BIGINT UNSIGNED", "FK_UK_IDX", False, None),
            ("category_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("cuisine_id", "BIGINT UNSIGNED", "FK_IDX", True, None),
            ("name", "VARCHAR(150)", "UK", False, None),
            ("description", "TEXT", "", True, None),
            ("base_price", "DECIMAL(10,2)", "IDX", False, None),
            ("is_vegetarian", "BOOLEAN", "IDX", False, "FALSE"),
            ("is_available", "BOOLEAN", "IDX", False, "TRUE"),
            ("preparation_time_minutes", "SMALLINT UNSIGNED", "", False, "15"),
            ("calories", "INT UNSIGNED", "", True, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "ingredient": {
        "category": "strong",
        "header_color": "#1E3A8A",
        "cluster": "cluster_inventory",
        "columns": [
            ("ingredient_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("name", "VARCHAR(150)", "UK", False, None),
            ("category", "VARCHAR(100)", "IDX", True, None),
            ("unit_of_measure", "ENUM('KG','GRAM','LITER','MILLILITER','PIECE','PACKET')", "", False, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "inventory": {
        "category": "associative",
        "header_color": "#0F766E",
        "cluster": "cluster_inventory",
        "columns": [
            ("inventory_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("kitchen_id", "BIGINT UNSIGNED", "FK_UK_IDX", False, None),
            ("ingredient_id", "BIGINT UNSIGNED", "FK_UK_IDX", False, None),
            ("current_stock", "DECIMAL(10,3)", "IDX", False, "0.000"),
            ("reorder_level", "DECIMAL(10,3)", "IDX", False, "0.000"),
            ("last_restocked_at", "DATETIME", "", True, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "inventory_movement": {
        "category": "audit",
        "header_color": "#7C2D12",
        "cluster": "cluster_inventory",
        "columns": [
            ("movement_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("kitchen_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("ingredient_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("movement_type", "ENUM('RESTOCK','CONSUMPTION','SPOILAGE','AUDIT_ADJUSTMENT','RETURN')", "", False, None),
            ("quantity_delta", "DECIMAL(10,3)", "", False, None),
            ("unit_cost", "DECIMAL(10,2)", "", True, None),
            ("reference_order_id", "BIGINT UNSIGNED", "FK_IDX", True, None),
            ("notes", "TEXT", "", True, None),
            ("recorded_by_user_id", "BIGINT UNSIGNED", "FK", True, None),
            ("created_at", "DATETIME(6)", "IDX", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "menu_item_ingredient": {
        "category": "associative",
        "header_color": "#0F766E",
        "cluster": "cluster_inventory",
        "columns": [
            ("menu_item_id", "BIGINT UNSIGNED", "PK_FK", False, None),
            ("ingredient_id", "BIGINT UNSIGNED", "PK_FK_IDX", False, None),
            ("quantity_required", "DECIMAL(10,3)", "", False, None),
            ("unit_of_measure", "ENUM('KG','GRAM','LITER','MILLILITER','PIECE','PACKET')", "", False, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "coupon": {
        "category": "strong",
        "header_color": "#1E3A8A",
        "cluster": "cluster_orders",
        "columns": [
            ("coupon_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("code", "VARCHAR(50)", "UK", False, None),
            ("description", "VARCHAR(255)", "", True, None),
            ("discount_type", "ENUM('PERCENTAGE','FIXED_AMOUNT')", "", False, None),
            ("discount_value", "DECIMAL(10,2)", "", False, None),
            ("min_order_value", "DECIMAL(10,2)", "", False, "0.00"),
            ("max_discount_amount", "DECIMAL(10,2)", "", True, None),
            ("valid_from", "DATETIME", "IDX", False, None),
            ("valid_to", "DATETIME", "IDX", False, None),
            ("usage_limit_per_user", "INT UNSIGNED", "", False, "1"),
            ("total_usage_limit", "INT UNSIGNED", "", False, "1000"),
            ("current_usage_count", "INT UNSIGNED", "", False, "0"),
            ("is_active", "BOOLEAN", "IDX", False, "TRUE"),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "orders": {
        "category": "strong",
        "header_color": "#1E3A8A",
        "cluster": "cluster_orders",
        "columns": [
            ("order_id", "BIGINT UNSIGNED", "PK_UK", False, "AUTO_INCREMENT"),
            ("order_number", "VARCHAR(64)", "UK", False, None),
            ("customer_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK_UK_IDX", False, None),
            ("delivery_address_id", "BIGINT UNSIGNED", "FK", False, None),
            ("order_status", "ENUM('PENDING','CONFIRMED','PREPARING','READY_FOR_PICKUP','OUT_FOR_DELIVERY','DELIVERED','CANCELLED')", "IDX", False, "'PENDING'"),
            ("subtotal_amount", "DECIMAL(10,2)", "", False, None),
            ("discount_amount", "DECIMAL(10,2)", "", False, "0.00"),
            ("tax_amount", "DECIMAL(10,2)", "", False, "0.00"),
            ("delivery_fee", "DECIMAL(10,2)", "", False, "0.00"),
            ("total_amount", "DECIMAL(10,2)", "", False, None),
            ("applied_coupon_id", "BIGINT UNSIGNED", "FK_IDX", True, None),
            ("special_instructions", "TEXT", "", True, None),
            ("estimated_delivery_time", "DATETIME", "", True, None),
            ("placed_at", "DATETIME(6)", "IDX", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "order_item": {
        "category": "weak",
        "header_color": "#7C2D12",
        "cluster": "cluster_orders",
        "columns": [
            ("order_item_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("order_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("menu_item_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("item_name_snapshot", "VARCHAR(150)", "", False, None),
            ("unit_price_snapshot", "DECIMAL(10,2)", "", False, None),
            ("quantity", "SMALLINT UNSIGNED", "", False, "1"),
            ("subtotal_price", "DECIMAL(10,2)", "", False, None),
            ("customization_notes", "VARCHAR(255)", "", True, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "payment": {
        "category": "audit",
        "header_color": "#7C2D12",
        "cluster": "cluster_orders",
        "columns": [
            ("payment_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("order_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("payment_method", "ENUM('UPI','CREDIT_CARD','DEBIT_CARD','NET_BANKING','WALLET','CASH_ON_DELIVERY')", "", False, None),
            ("payment_status", "ENUM('PENDING','SUCCESS','FAILED','REFUNDED')", "IDX", False, "'PENDING'"),
            ("transaction_reference", "VARCHAR(100)", "UK", True, None),
            ("gateway_name", "VARCHAR(50)", "", True, None),
            ("amount", "DECIMAL(10,2)", "", False, None),
            ("currency", "CHAR(3)", "", False, "'INR'"),
            ("error_message", "TEXT", "", True, None),
            ("initiated_at", "DATETIME(6)", "IDX", False, "CURRENT_TIMESTAMP(6)"),
            ("completed_at", "DATETIME(6)", "", True, None),
        ],
    },
    "order_status_history": {
        "category": "audit",
        "header_color": "#7C2D12",
        "cluster": "cluster_orders",
        "columns": [
            ("history_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("order_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("previous_status", "ENUM('PENDING','CONFIRMED','PREPARING','READY_FOR_PICKUP','OUT_FOR_DELIVERY','DELIVERED','CANCELLED')", "", True, None),
            ("new_status", "ENUM('PENDING','CONFIRMED','PREPARING','READY_FOR_PICKUP','OUT_FOR_DELIVERY','DELIVERED','CANCELLED')", "", False, None),
            ("changed_by_user_id", "BIGINT UNSIGNED", "FK_IDX", True, None),
            ("notes", "TEXT", "", True, None),
            ("created_at", "DATETIME(6)", "IDX", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "delivery": {
        "category": "associative",
        "header_color": "#0F766E",
        "cluster": "cluster_orders",
        "columns": [
            ("delivery_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("order_id", "BIGINT UNSIGNED", "FK_UK", False, None),
            ("delivery_person_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("delivery_status", "ENUM('ASSIGNED','PICKED_UP','OUT_FOR_DELIVERY','DELIVERED','FAILED')", "IDX", False, "'ASSIGNED'"),
            ("assigned_at", "DATETIME(6)", "IDX", False, "CURRENT_TIMESTAMP(6)"),
            ("picked_up_at", "DATETIME(6)", "", True, None),
            ("delivered_at", "DATETIME(6)", "", True, None),
            ("delivery_otp", "VARCHAR(6)", "", True, None),
            ("delivery_notes", "TEXT", "", True, None),
            ("customer_signature_url", "VARCHAR(255)", "", True, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "coupon_usage": {
        "category": "associative",
        "header_color": "#0F766E",
        "cluster": "cluster_orders",
        "columns": [
            ("usage_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("coupon_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("customer_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("order_id", "BIGINT UNSIGNED", "FK_UK", False, None),
            ("discount_applied", "DECIMAL(10,2)", "", False, None),
            ("used_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
    "review": {
        "category": "associative",
        "header_color": "#0F766E",
        "cluster": "cluster_orders",
        "columns": [
            ("review_id", "BIGINT UNSIGNED", "PK", False, "AUTO_INCREMENT"),
            ("order_id", "BIGINT UNSIGNED", "FK_UK", False, None),
            ("customer_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("kitchen_id", "BIGINT UNSIGNED", "FK_IDX", False, None),
            ("rating", "TINYINT UNSIGNED", "IDX", False, None),
            ("review_text", "TEXT", "", True, None),
            ("kitchen_reply", "TEXT", "", True, None),
            ("created_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
            ("updated_at", "DATETIME(6)", "", False, "CURRENT_TIMESTAMP(6)"),
        ],
    },
}

# Referential integrity foreign key relationships (Child -> Parent)
# Format: (child_tbl, child_col, parent_tbl, parent_col, on_delete, on_update)
FOREIGN_KEYS = [
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

# Conceptual/Logical ER relationships (Parent -> Child)
# Format: (parent_entity, child_entity, verb_phrase, arrowtail, arrowhead)
ER_RELATIONSHIPS = [
    ("users", "customer", "specializes to", "teetee", "teetee"),
    ("users", "staff", "specializes to", "teetee", "teetee"),
    ("users", "delivery_person", "specializes to", "teetee", "teetee"),
    ("users", "admin_audit_log", "performs", "teetee", "crowodot"),
    ("users", "order_status_history", "triggers", "odot", "crowodot"),
    ("users", "inventory_movement", "authorizes", "odot", "crowodot"),
    ("kitchen", "staff", "employs", "teetee", "crowodot"),
    ("kitchen", "menu_item", "prepares", "teetee", "crowodot"),
    ("kitchen", "orders", "fulfills", "teetee", "crowodot"),
    ("kitchen", "inventory", "maintains", "teetee", "crowodot"),
    ("kitchen", "inventory_movement", "logs", "teetee", "crowodot"),
    ("kitchen", "review", "receives", "teetee", "crowodot"),
    ("category", "menu_item", "classifies", "teetee", "crowodot"),
    ("cuisine", "menu_item", "styles", "odot", "crowodot"),
    ("customer", "address", "saves", "teetee", "crowodot"),
    ("customer", "orders", "places", "teetee", "crowodot"),
    ("customer", "coupon_usage", "redeems", "teetee", "crowodot"),
    ("customer", "review", "writes", "teetee", "crowodot"),
    ("address", "orders", "ships to", "teetee", "crowodot"),
    ("coupon", "orders", "discounts", "odot", "crowodot"),
    ("coupon", "coupon_usage", "tracks", "teetee", "crowodot"),
    ("orders", "order_item", "contains", "teetee", "crowtee"),
    ("orders", "payment", "settles via", "teetee", "crowtee"),
    ("orders", "order_status_history", "tracks", "teetee", "crowtee"),
    ("orders", "delivery", "dispatches", "teetee", "teetee"),
    ("orders", "coupon_usage", "claims", "teetee", "teetee"),
    ("orders", "review", "evaluates", "teetee", "teetee"),
    ("orders", "inventory_movement", "consumes", "odot", "crowodot"),
    ("menu_item", "order_item", "ordered in", "teetee", "crowodot"),
    ("menu_item", "menu_item_ingredient", "formulated with", "teetee", "crowtee"),
    ("ingredient", "menu_item_ingredient", "used in", "teetee", "crowodot"),
    ("ingredient", "inventory", "stocked as", "teetee", "crowodot"),
    ("ingredient", "inventory_movement", "adjusts", "teetee", "crowodot"),
    ("delivery_person", "delivery", "assigned to", "teetee", "crowodot"),
]


# ----------------------------------------------------------------------
# 2. GENERATE GRAPHVIZ ER MODEL (.dot)
# ----------------------------------------------------------------------
def generate_er_dot() -> str:
    lines = [
        "digraph ER_Model {",
        '    graph [rankdir=LR, dpi=300, bgcolor="#FFFFFF", nodesep=0.5, ranksep=1.0, splines=true, fontname="Helvetica, Arial, sans-serif"];',
        '    node [shape=none, fontname="Helvetica, Arial, sans-serif", fontsize=10];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=9, color="#475569", fontcolor="#1E293B", penwidth=1.2];',
        "",
    ]

    # Logical Domain Subgraphs
    domains = [
        ("cluster_identity", "1. IDENTITY & ACTOR DOMAIN", ["users", "customer", "staff", "delivery_person", "address", "admin_audit_log"]),
        ("cluster_catalog", "2. KITCHEN FACILITIES & MENU CATALOG", ["kitchen", "category", "cuisine", "menu_item"]),
        ("cluster_inventory", "3. INVENTORY & RECIPE BOM", ["ingredient", "inventory", "inventory_movement", "menu_item_ingredient"]),
        ("cluster_orders", "4. ORDERS, FULFILLMENT & SETTLEMENT", ["coupon", "orders", "order_item", "payment", "order_status_history", "delivery", "coupon_usage", "review"]),
    ]

    for cluster_id, cluster_title, table_names in domains:
        lines.append(f"    subgraph {cluster_id} {{")
        lines.append(f'        label="{cluster_title}";')
        lines.append('        style="dashed,rounded";')
        lines.append('        color="#CBD5E1";')
        lines.append('        bgcolor="#F8FAFC";')
        lines.append('        fontname="Helvetica, Arial, sans-serif";')
        lines.append('        fontsize=12;')
        lines.append('        fontcolor="#334155";')
        lines.append('        margin=16;')
        lines.append("")

        for tname in table_names:
            tinfo = TABLES[tname]
            hcolor = tinfo["header_color"]
            entity_label = tname.upper()

            lines.append(f"        {tname} [label=<")
            lines.append('          <table border="0" cellborder="1" cellspacing="0" cellpadding="4" bgcolor="#FFFFFF" style="rounded">')
            lines.append(f'            <tr><td bgcolor="{hcolor}" colspan="2" align="center"><font color="#FFFFFF" face="Helvetica-Bold, Arial-Bold"><b>{entity_label}</b></font></td></tr>')

            for col_name, _, key_type, _, _ in tinfo["columns"]:
                badge = ""
                if "PK" in key_type and "FK" in key_type:
                    badge = '<font color="#D97706"><b>PK</b></font> <font color="#2563EB"><i>FK</i></font>'
                elif "PK" in key_type:
                    badge = '<font color="#D97706"><b>PK</b></font>'
                elif "FK" in key_type:
                    badge = '<font color="#2563EB"><i>FK</i></font>'
                elif "UK" in key_type:
                    badge = '<font color="#059669"><b>UK</b></font>'

                lines.append(f'            <tr><td align="center" width="40">{badge}</td><td align="left" port="{col_name}">{col_name}</td></tr>')

            lines.append("          </table>")
            lines.append("        >];")
            lines.append("")

        lines.append("    }")
        lines.append("")

    # Relationships with Crow's Foot arrowheads
    lines.append("    // Conceptual & Logical Crow's Foot Entity Relationships")
    for parent, child, verb, tail, head in ER_RELATIONSHIPS:
        parent_pk = [c[0] for c in TABLES[parent]["columns"] if "PK" in c[2]][0]
        child_fk = [c[0] for c in TABLES[child]["columns"] if "FK" in c[2]]
        cport = child_fk[0] if child_fk else "id"
        lines.append(f'    {parent}:{parent_pk} -> {child}:{cport} [dir=both, arrowtail={tail}, arrowhead={head}, label="{verb}"];')

    lines.append("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# 3. GENERATE GRAPHVIZ RELATIONAL SCHEMA (.dot)
# ----------------------------------------------------------------------
def generate_relational_schema_dot() -> str:
    lines = [
        "digraph Relational_Schema {",
        '    graph [rankdir=LR, dpi=300, bgcolor="#FFFFFF", nodesep=0.6, ranksep=1.2, splines=true, fontname="Helvetica, Arial, sans-serif"];',
        '    node [shape=none, fontname="Helvetica, Arial, sans-serif", fontsize=9];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=8, color="#2563EB", fontcolor="#0F172A", penwidth=1.2];',
        "",
    ]

    domains = [
        ("cluster_identity", "1. IDENTITY & ACTOR RELATIONS", ["users", "customer", "staff", "delivery_person", "address", "admin_audit_log"]),
        ("cluster_catalog", "2. KITCHEN FACILITIES & MENU CATALOG", ["kitchen", "category", "cuisine", "menu_item"]),
        ("cluster_inventory", "3. INVENTORY & RECIPE BOM", ["ingredient", "inventory", "inventory_movement", "menu_item_ingredient"]),
        ("cluster_orders", "4. ORDERS, FULFILLMENT & SETTLEMENT", ["coupon", "orders", "order_item", "payment", "order_status_history", "delivery", "coupon_usage", "review"]),
    ]

    for cluster_id, cluster_title, table_names in domains:
        lines.append(f"    subgraph {cluster_id} {{")
        lines.append(f'        label="{cluster_title}";')
        lines.append('        style="dashed,rounded";')
        lines.append('        color="#94A3B8";')
        lines.append('        bgcolor="#F8FAFC";')
        lines.append('        fontname="Helvetica, Arial, sans-serif";')
        lines.append('        fontsize=12;')
        lines.append('        fontcolor="#1E293B";')
        lines.append('        margin=16;')
        lines.append("")

        for tname in table_names:
            tinfo = TABLES[tname]
            hcolor = "#1E293B"

            lines.append(f"        {tname} [label=<")
            lines.append('          <table border="0" cellborder="1" cellspacing="0" cellpadding="4" bgcolor="#FFFFFF" style="rounded">')
            lines.append(f'            <tr><td bgcolor="{hcolor}" colspan="4" align="center"><font color="#FFFFFF" face="Helvetica-Bold, Arial-Bold"><b>{tname}</b></font></td></tr>')
            lines.append('            <tr bgcolor="#F1F5F9">')
            lines.append('              <td align="center"><b>Key</b></td>')
            lines.append('              <td align="left"><b>Column</b></td>')
            lines.append('              <td align="left"><b>Type</b></td>')
            lines.append('              <td align="center"><b>Null</b></td>')
            lines.append('            </tr>')

            for col_name, col_type, key_type, is_null, _ in tinfo["columns"]:
                badges = []
                if "PK" in key_type:
                    badges.append('<font color="#D97706"><b>PK</b></font>')
                if "FK" in key_type:
                    badges.append('<font color="#2563EB"><i>FK</i></font>')
                if "UK" in key_type:
                    badges.append('<font color="#059669"><b>UK</b></font>')
                if "IDX" in key_type and "PK" not in key_type and "FK" not in key_type and "UK" not in key_type:
                    badges.append('<font color="#7C3AED"><b>IDX</b></font>')

                badge_str = " ".join(badges)
                null_str = '<font color="#94A3B8">NULL</font>' if is_null else '<font color="#0F172A"><b>NN</b></font>'
                clean_type = col_type
                if clean_type.startswith("ENUM("):
                    clean_type = "ENUM"

                lines.append(f'            <tr><td align="center">{badge_str}</td><td align="left" port="{col_name}">{col_name}</td><td align="left"><font color="#475569">{clean_type}</font></td><td align="center">{null_str}</td></tr>')

            lines.append("          </table>")
            lines.append("        >];")
            lines.append("")

        lines.append("    }")
        lines.append("")

    # Referential Integrity Edges: Child FK port -> Parent PK port
    lines.append("    // Referential Integrity Directed Edges (Child FK port -> Parent PK port)")
    for child, c_col, parent, p_col, on_del, on_upd in FOREIGN_KEYS:
        rule_label = f"{on_del} / {on_upd}"
        lines.append(f'    {child}:{c_col}:e -> {parent}:{p_col}:w [label="{rule_label}", arrowhead=vee];')

    lines.append("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# 4. GENERATE MERMAID.JS ER DIAGRAM (.mmd)
# ----------------------------------------------------------------------
def generate_mermaid_er() -> str:
    lines = ["erDiagram", ""]

    # Entities
    for tname, tinfo in TABLES.items():
        lines.append(f"    {tname} {{")
        for col_name, col_type, key_type, _, _ in tinfo["columns"]:
            mtype = col_type.split("(")[0].lower()
            if mtype.startswith("enum"):
                mtype = "enum"
            badge = ""
            if "PK" in key_type and "FK" in key_type:
                badge = "PK,FK"
            elif "PK" in key_type:
                badge = "PK"
            elif "FK" in key_type:
                badge = "FK"
            elif "UK" in key_type:
                badge = "UK"
            
            lines.append(f"        {mtype} {col_name} {badge}".rstrip())
        lines.append("    }")
        lines.append("")

    # Relationships in Mermaid notation
    mmd_rel_map = {
        ("teetee", "crowodot"): "||--o{",
        ("teetee", "crowtee"): "||--|{",
        ("teetee", "teetee"): "||--||",
        ("teetee", "teeodot"): "||--o|",
        ("odot", "crowodot"): "|o--o{",
        ("odot", "teetee"): "|o--||",
    }

    for parent, child, verb, tail, head in ER_RELATIONSHIPS:
        symbol = mmd_rel_map.get((tail, head), "||--o{")
        clean_verb = verb.replace(" ", "_")
        lines.append(f"    {parent} {symbol} {child} : {clean_verb}")

    return "\n".join(lines)


# ----------------------------------------------------------------------
# 4. GENERATE STANDARDIZED MARKDOWN DESIGN REPORT
# ----------------------------------------------------------------------
def generate_design_report() -> str:
    repo_url = "https://github.com/Murali-co/CLOUD_KITCHEN"
    lines = [
        "# Entity-Relationship and Normalized Relational Schema",
        "",
        "**Project Repository:** [Murali-co/CLOUD_KITCHEN](https://github.com/Murali-co/CLOUD_KITCHEN)",
        "",
        "![Crow's Foot ER Model](../assets/diagrams/er_model.png)",
        "",
        "![Physical Relational Schema](../assets/diagrams/relational_schema.png)",
        "",
        "## 1. Entity-Relationship Model (Standard Crow's Foot Notation)",
        "",
        "The following Mermaid.js source is the complete logical ER model. It uses strict Crow's Foot symbols and verb phrases.",
        "",
        "```mermaid",
    ]
    mmd_path = ASSETS_DIR / "er_model.mmd"
    if mmd_path.exists():
        lines.append(mmd_path.read_text(encoding="utf-8").strip())
    lines += ["```", "", "### ER Source and Rendering", "", "- Mermaid source: [`assets/diagrams/er_model.mmd`](../assets/diagrams/er_model.mmd)", "- Graphviz DOT source: [`assets/diagrams/er_model.dot`](../assets/diagrams/er_model.dot)", "", "## 2. Chen Notation Entity and Relationship Specification", "", "### Entity Classification", "", "| Entity | Classification | Primary / Identifying Attributes | Attribute Classification |", "|---|---|---|---|"]
    for name, info in TABLES.items():
        pks = [c[0] for c in info["columns"] if "PK" in c[2]]
        if info["category"] in ("subtype", "weak"):
            cls = "Weak / extension entity (identification is inherited or owner-bound)" if info["category"] == "weak" else "Weak specialization entity"
        elif info["category"] in ("audit",):
            cls = "Strong weakly identifying audit entity"
        elif name in ("inventory", "menu_item_ingredient", "coupon_usage"):
            cls = "Associative / junction entity"
        else:
            cls = "Strong entity"
        derived = "Derived values may be calculated, but all persisted attributes are atomic and directly stored"
        multivalued = "None; ownership and M:N memberships are represented by junction or owner-key relations"
        lines.append(f"| `{name}` | {cls} | {', '.join(f'`{x}`' for x in pks)} | Composite/derived/multivalued: composite PK may apply to junctions; {derived.lower()}; {multivalued.lower()} |")

    lines += ["", "### Relationship Specification", "", "| Relationship | Degree | Cardinality Ratio | Total / Partial Participation |", "|---|---|---|---|"]
    seen = set()
    for parent, child, verb, tail, head in ER_RELATIONSHIPS:
        key = (parent, child)
        if key in seen:
            continue
        seen.add(key)
        if (parent, child) in (("users","customer"),("users","staff"),("users","delivery_person"),("orders","delivery"),("orders","review"),("orders","coupon_usage")):
            ratio = "1:1"
        elif child in ("menu_item_ingredient","coupon_usage","inventory"):
            ratio = "M:N (resolved associatively)"
        else:
            ratio = "1:N"
        participation = "Both sides partial" if (child in ("cuisine","coupon") or parent in ("cuisine","coupon")) else ("Total on child; partial on parent" if ratio != "1:1" else "Total on both sides")
        lines.append(f"| {parent} — {child} (`{verb}`) | Binary | {ratio} | {participation} |")

    lines += ["", "## 3. Normalized Relational Schema (Textbook Notation)", "", "Foreign keys are italicized and primary keys are underlined; each foreign key references the named primary key.", ""]
    for name, info in TABLES.items():
        refs = {}
        for child, ccol, parent, pcol, _, _ in FOREIGN_KEYS:
            if child == name:
                refs[ccol] = (parent, pcol)
        attrs = []
        for col, _, key, _, _ in info["columns"]:
            if "PK" in key:
                attrs.append(f"<u>{col}</u>")
            elif col in refs:
                parent, pcol = refs[col]
                attrs.append(f"*{col}* → {parent}(<u>{pcol}</u>)")
            else:
                attrs.append(col)
        lines.append(f"`{name}` ({', '.join(attrs)})")

    lines += ["", "## 4. Data Dictionary / Schema Specification", ""]
    for name, info in TABLES.items():
        lines += [f"### `{name}`", "", "| Column Name | Data Type & Size | Key Type | Nullability | Default Value | CHECK / Referential Constraint |", "|---|---|---|---|---|---|"]
        fk_map = {}
        for child, ccol, parent, pcol, od, ou in FOREIGN_KEYS:
            if child == name:
                fk_map[ccol] = f"FK → `{parent}.{pcol}`; ON DELETE {od}; ON UPDATE {ou}"
        for col, dtype, key, nullable, default in info["columns"]:
            keys = []
            if "PK" in key: keys.append("PK")
            if "FK" in key: keys.append("FK")
            if "UK" in key: keys.append("UK")
            if "IDX" in key: keys.append("IDX")
            constraint = fk_map.get(col, "—")
            if name == "users" and col in ("email","phone_number"):
                constraint = "UNIQUE; domain CHECK pattern" + ("; " + constraint if constraint != "—" else "")
            if name == "kitchen" and col in ("latitude","longitude","max_active_orders"):
                constraint = "Domain/range CHECK"
            if name in ("delivery_person",) and col in ("rating","current_latitude","current_longitude"):
                constraint = "Domain/range CHECK"
            if name == "menu_item" and col in ("base_price","preparation_time_minutes"):
                constraint = "Domain/range CHECK"
            if name == "orders" and col in ("subtotal_amount","discount_amount","tax_amount","delivery_fee","total_amount"):
                constraint = "CHECK(value >= 0)"
            lines.append(f"| `{col}` | `{dtype}` | {' / '.join(keys) or '—'} | {'NULL' if nullable else 'NOT NULL'} | `{default if default is not None else '—'}` | {constraint} |")

    lines += [
        "", "## 5. Normalization Verification", "",
        "### 1NF", "- Every column is atomic; SQL `ENUM`, `TEXT`, `JSON`, and timestamp values are scalar domain values rather than repeating groups.", "- M:N relationships are separated into `menu_item_ingredient`, `inventory`, and `coupon_usage` rather than stored as repeating lists.", "",
        "### 2NF", "- All non-key attributes depend on the full table key. In `menu_item_ingredient`, `quantity_required` and `unit_of_measure` depend on the composite key `(menu_item_id, ingredient_id)`; neither can depend on only one component.", "- Single-column primary-key tables have no proper subset key from which any non-key attribute is derived.", "",
        "### 3NF", "- Non-key attributes do not determine other non-key attributes. For example, `orders.order_id` is the key determinant for order status and totals; customer, kitchen, and coupon facts remain in their parent relations.", "- Role-specific fields are separated into `customer`, `staff`, and `delivery_person`, avoiding transitive role and profile dependencies in `users`.", "",
        "### BCNF", "- Every explicit determinant is a candidate/superkey: table primary keys and unique candidate keys such as `users.email`, `users.phone_number`, `kitchen.branch_code`, `coupon.code`, `orders.order_number`, and `payment.transaction_reference`.", "- Composite associative keys `(menu_item_id, ingredient_id)`, `(kitchen_id, ingredient_id)`, and lifecycle unique keys are determinants only for their own complete rows.", "",
        "### M:N Resolution", "- `menu_item` M:N `ingredient`: `menu_item_ingredient(menu_item_id, ingredient_id, quantity_required, unit_of_measure)`.", "- `kitchen` M:N `ingredient`: `inventory(kitchen_id, ingredient_id, current_stock, reorder_level)`, with unique `(kitchen_id, ingredient_id)`.", "- `customer` M:N `coupon`: `coupon_usage(coupon_id, customer_id, order_id, discount_applied, used_at)`; `order_id` is also unique in the junction use case.", "",
        "## 6. Referential Actions and Integrity", "",
        "- `CASCADE` is used for dependent lifecycle data, including order items, status history, coupon usage, and recipe membership.", "- `RESTRICT` protects core kitchens, customers, menu items, and financial/operational parent records.", "- `SET NULL` preserves optional audit links and optional foreign references such as cuisine, coupon, movement order, changed-by user, and recorded-by user.", "",
        "## 7. Project Repository", "", f"- {repo_url}", ""
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------
# 5. EXECUTION & COMPILATION
# ----------------------------------------------------------------------
def main():
    print("=" * 70)
    print("GOURMETCLOUD DATABASE DIAGRAM GENERATION SUITE")
    print("=" * 70)

    # 1. Write Source Files
    er_dot_path = ASSETS_DIR / "er_model.dot"
    rel_dot_path = ASSETS_DIR / "relational_schema.dot"
    er_mmd_path = ASSETS_DIR / "er_model.mmd"
    rel_mmd_path = ASSETS_DIR / "relational_schema.mmd"

    er_png_path = ASSETS_DIR / "er_model.png"
    rel_png_path = ASSETS_DIR / "relational_schema.png"

    print(f"[*] Generating {er_dot_path.name}...")
    er_dot = generate_er_dot()
    er_dot_path.write_text(er_dot, encoding="utf-8")

    print(f"[*] Generating {rel_dot_path.name}...")
    rel_dot = generate_relational_schema_dot()
    rel_dot_path.write_text(rel_dot, encoding="utf-8")

    print(f"[*] Generating {er_mmd_path.name}...")
    er_mmd = generate_mermaid_er()
    er_mmd_path.write_text(er_mmd, encoding="utf-8")
    rel_mmd_path.write_text(er_mmd, encoding="utf-8")

    # 2. Check for Graphviz dot
    dot_bin = shutil.which("dot")
    if dot_bin:
        print(f"[+] Found system Graphviz dot at: {dot_bin}")
        print(f"[*] Compiling {er_png_path.name} via Graphviz (dpi=300)...")
        subprocess.run([dot_bin, "-Tpng", "-Gdpi=300", str(er_dot_path), "-o", str(er_png_path)], check=True)
        print(f"[*] Compiling {rel_png_path.name} via Graphviz (dpi=300)...")
        subprocess.run([dot_bin, "-Tpng", "-Gdpi=300", str(rel_dot_path), "-o", str(rel_png_path)], check=True)
    else:
        print("[-] System 'dot' binary not detected in PATH.")
        print("[*] Falling back to Node.js @viz-js/viz + Puppeteer high-resolution rasterizer...")
        
        node_bin = shutil.which("node")
        if not node_bin:
            raise RuntimeError("Neither 'dot' nor 'node' executable found on system!")

        print(f"[*] Compiling {er_png_path.name} using render_diagrams.js...")
        subprocess.run([node_bin, str(RENDERER_JS), str(er_dot_path), str(er_png_path), "12000"], check=True)

        print(f"[*] Compiling {rel_png_path.name} using render_diagrams.js...")
        subprocess.run([node_bin, str(RENDERER_JS), str(rel_dot_path), str(rel_png_path), "12000"], check=True)

    report_path = WORKSPACE_ROOT / "docs" / "ER_AND_RELATIONAL_SCHEMA.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(generate_design_report(), encoding="utf-8")
    print(f"[*] Wrote standardized design report: {report_path}")

    # 3. Verification
    print("\n" + "=" * 70)
    print("VERIFICATION & ARTIFACT SUMMARY")
    print("=" * 70)

    for p in [er_dot_path, rel_dot_path, er_mmd_path, er_png_path, rel_png_path]:
        if p.exists() and p.stat().st_size > 0:
            size_kb = p.stat().st_size / 1024
            print(f"[PASS] {p.name:25} ({size_kb:8.1f} KB) -> {p}")
        else:
            print(f"[FAIL] Missing or empty artifact: {p}")
            sys.exit(1)

    print("\n[SUCCESS] All database design diagrams generated and verified.")


if __name__ == "__main__":
    main()
