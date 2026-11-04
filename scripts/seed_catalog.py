"""
GourmetCloud - Production & Development Catalog Seeder
Idempotent script to seed realistic dummy food catalogue, kitchens, categories,
ingredients, recipes, inventory, coupons, and development accounts.
"""

import os
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from dotenv import dotenv_values

# Ensure backend is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.address import Address
from app.models.fulfillment import Coupon, DiscountType
from app.models.inventory import Ingredient, Inventory, MenuItemIngredient, UnitOfMeasure
from app.models.kitchen import Category, Kitchen, MenuItem, OperatingStatus
from app.models.user import (
    Customer,
    DeliveryPerson,
    DeliveryPersonStatus,
    DietaryPreference,
    ShiftTiming,
    Staff,
    StaffRole,
    User,
    UserRole,
    VehicleType,
)


def get_db_session():
    env_path = os.path.join(BACKEND_DIR, ".env")
    env_vals = dotenv_values(env_path)
    if not env_vals:
        raise RuntimeError(f"Could not load .env from {env_path}")

    db_user = env_vals.get("DB_USER", "cloud_kitchen_app")
    db_pass = env_vals.get("DB_PASSWORD", "")
    db_host = env_vals.get("DB_HOST", "localhost")
    db_port = env_vals.get("DB_PORT", "3306")
    db_name = env_vals.get("DB_NAME", "cloud_kitchen_db")

    url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    engine = create_engine(url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


# ----------------------------------------------------------------------
# 1. Kitchens Data
# ----------------------------------------------------------------------
KITCHENS_DATA = [
    {
        "name": "Cloud Kitchen Indiranagar",
        "branch_code": "CK-BLR-01",
        "contact_phone": "+918041234567",
        "email": "indiranagar@cloudkitchen.com",
        "address_line1": "100 Feet Road, HAL 2nd Stage",
        "address_line2": "Near Metro Pillar 84",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
        "latitude": Decimal("12.97159870"),
        "longitude": Decimal("77.64115480"),
        "operating_status": OperatingStatus.ACTIVE,
        "opening_time": time(8, 0, 0),
        "closing_time": time(23, 30, 0),
        "max_active_orders": 60,
    },
    {
        "name": "Cloud Kitchen Koramangala",
        "branch_code": "CK-BLR-02",
        "contact_phone": "+918049876543",
        "email": "koramangala@cloudkitchen.com",
        "address_line1": "80 Feet Road, 4th Block",
        "address_line2": "Opposite Sony World Signal",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560034",
        "latitude": Decimal("12.93519290"),
        "longitude": Decimal("77.62448070"),
        "operating_status": OperatingStatus.ACTIVE,
        "opening_time": time(9, 0, 0),
        "closing_time": time(23, 59, 59),
        "max_active_orders": 50,
    },
    {
        "name": "Cloud Kitchen Whitefield",
        "branch_code": "CK-BLR-03",
        "contact_phone": "+918048765432",
        "email": "whitefield@cloudkitchen.com",
        "address_line1": "ITPB Main Road, Whitefield",
        "address_line2": "Near Hopefarm Junction",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560066",
        "latitude": Decimal("12.98330000"),
        "longitude": Decimal("77.74900000"),
        "operating_status": OperatingStatus.ACTIVE,
        "opening_time": time(8, 30, 0),
        "closing_time": time(23, 0, 0),
        "max_active_orders": 55,
    },
]

# ----------------------------------------------------------------------
# 2. Categories Data (10 Categories as requested)
# ----------------------------------------------------------------------
CATEGORIES_DATA = [
    {
        "name": "South Indian",
        "slug": "south-indian",
        "description": "Authentic fermented dosas, fluffy idlis, crispy vadas, and traditional filter coffee",
        "display_order": 1,
        "is_active": True,
    },
    {
        "name": "North Indian",
        "slug": "north-indian",
        "description": "Rich buttery curries, slow-cooked gravies, tandoor specials, and hot butter naans",
        "display_order": 2,
        "is_active": True,
    },
    {
        "name": "Chinese",
        "slug": "chinese",
        "description": "Wok-tossed noodles, fried rice, sizzlers, and Indo-Chinese street favorites",
        "display_order": 3,
        "is_active": True,
    },
    {
        "name": "Starters",
        "slug": "starters",
        "description": "Crispy appetisers, grilled paneer tikka, spicy chicken wings, and finger foods",
        "display_order": 4,
        "is_active": True,
    },
    {
        "name": "Biryani and Rice",
        "slug": "biryani-and-rice",
        "description": "Dum cooked fragrant basmati rice dishes infused with royal saffron and whole spices",
        "display_order": 5,
        "is_active": True,
    },
    {
        "name": "Burgers and Sandwiches",
        "slug": "burgers-and-sandwiches",
        "description": "Gourmet brioche burgers, grilled paninis, layered club sandwiches, and crispy fries",
        "display_order": 6,
        "is_active": True,
    },
    {
        "name": "Pizza and Pasta",
        "slug": "pizza-and-pasta",
        "description": "Stone-baked artisan pizzas with mozzarella and handcrafted al dente pastas",
        "display_order": 7,
        "is_active": True,
    },
    {
        "name": "Desserts",
        "slug": "desserts",
        "description": "Warm chocolate brownies, traditional gulab jamun, rasmalai, and sweet treats",
        "display_order": 8,
        "is_active": True,
    },
    {
        "name": "Beverages",
        "slug": "beverages",
        "description": "Freshly brewed coffees, chilled mango lassi, artisanal shakes, and refreshing coolers",
        "display_order": 9,
        "is_active": True,
    },
    {
        "name": "Healthy Food",
        "slug": "healthy-food",
        "description": "Nutritious quinoa bowls, fresh garden salads, protein-rich grain bowls, and cold juices",
        "display_order": 10,
        "is_active": True,
    },
]

# ----------------------------------------------------------------------
# 3. Ingredients Data (16 Core Ingredients)
# ----------------------------------------------------------------------
INGREDIENTS_DATA = [
    {"name": "Aged Basmati Rice", "category": "Grains", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Fresh Malai Paneer", "category": "Dairy", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Boneless Chicken Breast", "category": "Meat & Poultry", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Sourdough Pizza Dough Balls", "category": "Bakery", "unit_of_measure": UnitOfMeasure.PIECE},
    {"name": "Fresh Mozzarella Cheese", "category": "Dairy", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "San Marzano Tomato Puree", "category": "Produce", "unit_of_measure": UnitOfMeasure.LITER},
    {"name": "Heavy Dairy Cream", "category": "Dairy", "unit_of_measure": UnitOfMeasure.LITER},
    {"name": "Extra Virgin Olive Oil", "category": "Oils & Condiments", "unit_of_measure": UnitOfMeasure.LITER},
    {"name": "Penne Rigate Pasta", "category": "Dry Goods", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Single Origin Arabica Beans", "category": "Beverage Dry Goods", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Dark Belgian Cocoa Powder", "category": "Baking", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Black Lentils (Urad Dal)", "category": "Pulses", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Alphonso Mango Pulp", "category": "Fruits", "unit_of_measure": UnitOfMeasure.LITER},
    {"name": "Pure Desi Ghee", "category": "Dairy", "unit_of_measure": UnitOfMeasure.LITER},
    {"name": "Organic Quinoa Seeds", "category": "Grains", "unit_of_measure": UnitOfMeasure.KG},
    {"name": "Russet Baking Potatoes", "category": "Produce", "unit_of_measure": UnitOfMeasure.KG},
]

# ----------------------------------------------------------------------
# 4. Menu Items Data (42 items across 10 categories & 3 kitchens)
# ----------------------------------------------------------------------
MENU_ITEMS_DATA = [
    # --- Category: South Indian ---
    {
        "kitchen": "CK-BLR-01",
        "category": "south-indian",
        "name": "Masala Dosa",
        "description": "Golden crispy rice crepe filled with spiced tempered potato mash, served with fresh coconut chutney and piping hot drumstick sambar.",
        "base_price": Decimal("90.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 12,
        "calories": 320,
        "recipes": [
            ("Russet Baking Potatoes", Decimal("0.120"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "south-indian",
        "name": "Idli Vada Combo",
        "description": "Two steamed fluffy rice cakes and one crispy medu vada served with freshly grated coconut chutney and aromatic sambar.",
        "base_price": Decimal("80.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 10,
        "calories": 290,
        "recipes": [
            ("Black Lentils (Urad Dal)", Decimal("0.080"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.010"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "south-indian",
        "name": "Ghee Mysore Masala Dosa",
        "description": "Classic Bangalore-style crispy dosa smeared with spicy red garlic chutney, filled with potato bhaji and dollops of pure desi ghee.",
        "base_price": Decimal("110.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 15,
        "calories": 380,
        "recipes": [
            ("Russet Baking Potatoes", Decimal("0.120"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.030"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "south-indian",
        "name": "Medu Vada (2 pcs)",
        "description": "Crispy golden fried lentil donuts seasoned with black pepper, curry leaves, and ginger, served with coconut chutney.",
        "base_price": Decimal("70.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 10,
        "calories": 260,
        "recipes": [
            ("Black Lentils (Urad Dal)", Decimal("0.120"), UnitOfMeasure.KG),
        ],
    },

    # --- Category: North Indian ---
    {
        "kitchen": "CK-BLR-01",
        "category": "north-indian",
        "name": "Paneer Butter Masala",
        "description": "Tender cottage cheese cubes simmered in a silky, slow-cooked buttery tomato and cashew nut gravy with fenugreek leaves.",
        "base_price": Decimal("220.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 20,
        "calories": 480,
        "recipes": [
            ("Fresh Malai Paneer", Decimal("0.200"), UnitOfMeasure.KG),
            ("Heavy Dairy Cream", Decimal("0.050"), UnitOfMeasure.LITER),
            ("San Marzano Tomato Puree", Decimal("0.080"), UnitOfMeasure.LITER),
            ("Pure Desi Ghee", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "north-indian",
        "name": "Butter Naan",
        "description": "Traditional leavened clay-oven tandoor flatbread brushed generously with churned salted butter.",
        "base_price": Decimal("45.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 8,
        "calories": 210,
        "recipes": [
            ("Pure Desi Ghee", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "north-indian",
        "name": "Dal Makhani",
        "description": "Overnight slow-simmered whole black urad lentils enriched with white butter, fresh dairy cream, and aromatic kasuri methi.",
        "base_price": Decimal("190.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 18,
        "calories": 420,
        "recipes": [
            ("Black Lentils (Urad Dal)", Decimal("0.150"), UnitOfMeasure.KG),
            ("Heavy Dairy Cream", Decimal("0.040"), UnitOfMeasure.LITER),
            ("Pure Desi Ghee", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "north-indian",
        "name": "Kadai Chicken",
        "description": "Succulent chicken morsels cooked in a robust onion-tomato gravy with freshly roasted ground spices and crunchy bell peppers.",
        "base_price": Decimal("260.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 22,
        "calories": 520,
        "recipes": [
            ("Boneless Chicken Breast", Decimal("0.220"), UnitOfMeasure.KG),
            ("San Marzano Tomato Puree", Decimal("0.060"), UnitOfMeasure.LITER),
            ("Extra Virgin Olive Oil", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "north-indian",
        "name": "Garlic Naan",
        "description": "Soft tandoor-baked flatbread infused with roasted garlic flakes, fresh cilantro, and melted butter.",
        "base_price": Decimal("55.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 8,
        "calories": 220,
        "recipes": [
            ("Pure Desi Ghee", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },

    # --- Category: Chinese ---
    {
        "kitchen": "CK-BLR-01",
        "category": "chinese",
        "name": "Gobi Manchurian",
        "description": "Crispy batter-fried cauliflower florets tossed in a spicy, tangy Indo-Chinese soy-chili garlic sauce with scallions.",
        "base_price": Decimal("150.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 15,
        "calories": 340,
        "recipes": [
            ("Extra Virgin Olive Oil", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "chinese",
        "name": "Veg Hakka Noodles",
        "description": "Wok-tossed thin noodles stir-fried with crunchy julienne vegetables, spring onions, and light oriental sesame soy glaze.",
        "base_price": Decimal("160.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 15,
        "calories": 390,
        "recipes": [
            ("Extra Virgin Olive Oil", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "chinese",
        "name": "Chicken Fried Rice",
        "description": "Fragrant long grain rice wok-tossed with tender diced chicken, farm eggs, scallions, and signature dark soy.",
        "base_price": Decimal("210.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 16,
        "calories": 480,
        "recipes": [
            ("Aged Basmati Rice", Decimal("0.160"), UnitOfMeasure.KG),
            ("Boneless Chicken Breast", Decimal("0.120"), UnitOfMeasure.KG),
            ("Extra Virgin Olive Oil", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "chinese",
        "name": "Chilli Chicken Dry",
        "description": "Wok-seared crispy chicken cubes tossed with pungent green chilies, onions, bell peppers, and savoury Chinese soy glaze.",
        "base_price": Decimal("230.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 18,
        "calories": 450,
        "recipes": [
            ("Boneless Chicken Breast", Decimal("0.200"), UnitOfMeasure.KG),
            ("Extra Virgin Olive Oil", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "chinese",
        "name": "Veg Schezwan Fried Rice",
        "description": "Fiery wok-fried basmati rice blended with house-made Schezwan chili sauce, crisp carrots, and french beans.",
        "base_price": Decimal("170.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 15,
        "calories": 410,
        "recipes": [
            ("Aged Basmati Rice", Decimal("0.160"), UnitOfMeasure.KG),
            ("Extra Virgin Olive Oil", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },

    # --- Category: Starters ---
    {
        "kitchen": "CK-BLR-01",
        "category": "starters",
        "name": "Paneer Tikka",
        "description": "Soft malai paneer cubes marinated in spiced hung yogurt, Kashmiri chili, and roasted gram flour, charred to smoky perfection in clay oven.",
        "base_price": Decimal("190.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 16,
        "calories": 350,
        "recipes": [
            ("Fresh Malai Paneer", Decimal("0.200"), UnitOfMeasure.KG),
            ("Heavy Dairy Cream", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "starters",
        "name": "Crispy Corn Pepper Salt",
        "description": "Tender golden sweetcorn kernels flash-fried until crispy, tossed with freshly cracked black pepper and green scallions.",
        "base_price": Decimal("140.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 12,
        "calories": 280,
        "recipes": [
            ("Extra Virgin Olive Oil", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "starters",
        "name": "Tandoori Chicken Wings (6 pcs)",
        "description": "Succulent chicken wings marinated in hung yogurt and ground spices, roasted over charcoal and glazed with lime butter.",
        "base_price": Decimal("220.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 20,
        "calories": 460,
        "recipes": [
            ("Boneless Chicken Breast", Decimal("0.250"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "starters",
        "name": "Dahi Ke Kebab",
        "description": "Melt-in-mouth pan-seared patties crafted from spiced hung yogurt, roasted gram flour, crushed coriander seeds, and cardamom.",
        "base_price": Decimal("180.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 14,
        "calories": 320,
        "recipes": [
            ("Heavy Dairy Cream", Decimal("0.050"), UnitOfMeasure.LITER),
            ("Pure Desi Ghee", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },

    # --- Category: Biryani and Rice ---
    {
        "kitchen": "CK-BLR-01",
        "category": "biryani-and-rice",
        "name": "Chicken Biryani",
        "description": "Authentic dum-cooked Hyderabadi biryani layered with marinated chicken, saffron-infused long grain basmati rice, caramelized onions, and fresh mint.",
        "base_price": Decimal("240.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 20,
        "calories": 650,
        "recipes": [
            ("Aged Basmati Rice", Decimal("0.180"), UnitOfMeasure.KG),
            ("Boneless Chicken Breast", Decimal("0.180"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.025"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "biryani-and-rice",
        "name": "Veg Biryani",
        "description": "Fragrant long grain basmati rice layered with garden vegetables, paneer cubes, whole royal spices, and brown onions, served with cooling raita.",
        "base_price": Decimal("170.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 18,
        "calories": 490,
        "recipes": [
            ("Aged Basmati Rice", Decimal("0.180"), UnitOfMeasure.KG),
            ("Fresh Malai Paneer", Decimal("0.080"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "biryani-and-rice",
        "name": "Mutton Dum Biryani",
        "description": "Royal slow-cooked tender mutton pieces simmered in rich yakhni stock and sealed under fragrant saffron basmati rice.",
        "base_price": Decimal("340.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 25,
        "calories": 720,
        "recipes": [
            ("Aged Basmati Rice", Decimal("0.200"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.030"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "biryani-and-rice",
        "name": "Jeera Rice with Dal Tadka",
        "description": "Cumin-tempered long grain basmati rice served alongside homestyle yellow lentils tempered with ghee, garlic, and dried red chilies.",
        "base_price": Decimal("160.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 14,
        "calories": 440,
        "recipes": [
            ("Aged Basmati Rice", Decimal("0.160"), UnitOfMeasure.KG),
            ("Pure Desi Ghee", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },

    # --- Category: Burgers and Sandwiches ---
    {
        "kitchen": "CK-BLR-01",
        "category": "burgers-and-sandwiches",
        "name": "Classic Veg Burger",
        "description": "Crispy golden vegetable and potato patty topped with crunchy iceberg lettuce, ripe tomatoes, melted cheddar, and house relish on toasted sesame buns.",
        "base_price": Decimal("130.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 12,
        "calories": 410,
        "recipes": [
            ("Russet Baking Potatoes", Decimal("0.100"), UnitOfMeasure.KG),
            ("Fresh Mozzarella Cheese", Decimal("0.040"), UnitOfMeasure.KG),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "burgers-and-sandwiches",
        "name": "Crispy Chicken Burger",
        "description": "Panko-crusted chicken fillet with tangy honey mustard, dill pickles, crunchy lettuce, and melted cheese on a soft brioche bun.",
        "base_price": Decimal("180.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 15,
        "calories": 540,
        "recipes": [
            ("Boneless Chicken Breast", Decimal("0.160"), UnitOfMeasure.KG),
            ("Fresh Mozzarella Cheese", Decimal("0.040"), UnitOfMeasure.KG),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "burgers-and-sandwiches",
        "name": "Bombay Grilled Sandwich",
        "description": "Triple-decker toasted sandwich packed with spiced potatoes, beetroots, cucumber, cheese, and spicy mint-coriander chutney.",
        "base_price": Decimal("110.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 12,
        "calories": 310,
        "recipes": [
            ("Russet Baking Potatoes", Decimal("0.100"), UnitOfMeasure.KG),
            ("Fresh Mozzarella Cheese", Decimal("0.040"), UnitOfMeasure.KG),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "burgers-and-sandwiches",
        "name": "Paneer Tikka Panini",
        "description": "Pressed ciabatta panini filled with grilled marinated paneer, caramelized onions, crunchy capsicum, and mint mayonnaise.",
        "base_price": Decimal("150.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 14,
        "calories": 430,
        "recipes": [
            ("Fresh Malai Paneer", Decimal("0.120"), UnitOfMeasure.KG),
            ("Fresh Mozzarella Cheese", Decimal("0.030"), UnitOfMeasure.KG),
        ],
    },

    # --- Category: Pizza and Pasta ---
    {
        "kitchen": "CK-BLR-01",
        "category": "pizza-and-pasta",
        "name": "Margherita Pizza",
        "description": "Hand-stretched stone-baked sourdough pizza topped with Italian San Marzano tomato sauce, fresh buffalo mozzarella, and aromatic sweet basil.",
        "base_price": Decimal("199.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 18,
        "calories": 680,
        "recipes": [
            ("Sourdough Pizza Dough Balls", Decimal("1.000"), UnitOfMeasure.PIECE),
            ("Fresh Mozzarella Cheese", Decimal("0.150"), UnitOfMeasure.KG),
            ("San Marzano Tomato Puree", Decimal("0.080"), UnitOfMeasure.LITER),
            ("Extra Virgin Olive Oil", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "pizza-and-pasta",
        "name": "Creamy White Sauce Penne Pasta",
        "description": "Al dente penne pasta tossed in rich parmesan garlic cream sauce with sautéed mushrooms, bell peppers, and fragrant Italian oregano.",
        "base_price": Decimal("210.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 16,
        "calories": 580,
        "recipes": [
            ("Penne Rigate Pasta", Decimal("0.120"), UnitOfMeasure.KG),
            ("Heavy Dairy Cream", Decimal("0.060"), UnitOfMeasure.LITER),
            ("Extra Virgin Olive Oil", Decimal("0.010"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "pizza-and-pasta",
        "name": "Spicy Pepperoni Pizza",
        "description": "Thin crust artisan pizza loaded with spiced cured pepperoni, mozzarella cheese blend, San Marzano tomato base, and red chili drizzle.",
        "base_price": Decimal("299.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 20,
        "calories": 790,
        "recipes": [
            ("Sourdough Pizza Dough Balls", Decimal("1.000"), UnitOfMeasure.PIECE),
            ("Fresh Mozzarella Cheese", Decimal("0.160"), UnitOfMeasure.KG),
            ("San Marzano Tomato Puree", Decimal("0.080"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "pizza-and-pasta",
        "name": "Red Sauce Arrabiata Pasta",
        "description": "Penne pasta tossed in fiery San Marzano tomato sauce infused with garlic, extra virgin olive oil, and crushed red chili flakes.",
        "base_price": Decimal("190.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 15,
        "calories": 460,
        "recipes": [
            ("Penne Rigate Pasta", Decimal("0.120"), UnitOfMeasure.KG),
            ("San Marzano Tomato Puree", Decimal("0.080"), UnitOfMeasure.LITER),
            ("Extra Virgin Olive Oil", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },

    # --- Category: Desserts ---
    {
        "kitchen": "CK-BLR-01",
        "category": "desserts",
        "name": "Chocolate Brownie",
        "description": "Decadent warm Belgian fudge brownie loaded with chocolate chunks and dusted with fine powdered icing sugar.",
        "base_price": Decimal("110.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 8,
        "calories": 320,
        "recipes": [
            ("Dark Belgian Cocoa Powder", Decimal("0.040"), UnitOfMeasure.KG),
            ("Heavy Dairy Cream", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "desserts",
        "name": "Gulab Jamun (2 pcs)",
        "description": "Traditional deep-fried golden milk dumplings steeped in fragrant rose-cardamom and saffron sugar syrup.",
        "base_price": Decimal("70.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 5,
        "calories": 260,
        "recipes": [
            ("Pure Desi Ghee", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "desserts",
        "name": "Rasmalai (2 pcs)",
        "description": "Delicate soft cottage cheese discs soaked in chilled thickened saffron milk, garnished with sliced pistachios and almond slivers.",
        "base_price": Decimal("90.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 5,
        "calories": 240,
        "recipes": [
            ("Fresh Malai Paneer", Decimal("0.080"), UnitOfMeasure.KG),
            ("Heavy Dairy Cream", Decimal("0.040"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "desserts",
        "name": "New York Baked Cheesecake",
        "description": "Classic creamy velvety cheesecake slice on a buttery graham cracker crust with a light berry swirl.",
        "base_price": Decimal("160.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 6,
        "calories": 390,
        "recipes": [
            ("Heavy Dairy Cream", Decimal("0.050"), UnitOfMeasure.LITER),
        ],
    },

    # --- Category: Beverages ---
    {
        "kitchen": "CK-BLR-01",
        "category": "beverages",
        "name": "Mango Lassi",
        "description": "Traditional thick Punjabi yogurt smoothie blended with ripe Alphonso mango pulp, green cardamom, and a touch of floral rosewater.",
        "base_price": Decimal("80.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 6,
        "calories": 210,
        "recipes": [
            ("Alphonso Mango Pulp", Decimal("0.080"), UnitOfMeasure.LITER),
            ("Heavy Dairy Cream", Decimal("0.030"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "beverages",
        "name": "Cold Coffee",
        "description": "Chilled rich milk blended with double-shot South Indian Arabica espresso, ice, and dark Belgian chocolate drizzle.",
        "base_price": Decimal("100.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 6,
        "calories": 190,
        "recipes": [
            ("Single Origin Arabica Beans", Decimal("0.025"), UnitOfMeasure.KG),
            ("Heavy Dairy Cream", Decimal("0.030"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "beverages",
        "name": "Fresh Lime Soda",
        "description": "Freshly squeezed lime juice with bubbly soda water, rock salt, mint sprigs, and natural cane sugar syrup.",
        "base_price": Decimal("60.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 5,
        "calories": 70,
        "recipes": [],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "beverages",
        "name": "Masala Chai Flask (500ml)",
        "description": "Robust Assam tea leaves slow-brewed with fresh ginger root, crushed green cardamom, cinnamon, and fresh milk.",
        "base_price": Decimal("90.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 8,
        "calories": 150,
        "recipes": [
            ("Heavy Dairy Cream", Decimal("0.030"), UnitOfMeasure.LITER),
        ],
    },

    # --- Category: Healthy Food ---
    {
        "kitchen": "CK-BLR-01",
        "category": "healthy-food",
        "name": "Mediterranean Quinoa Salad Bowl",
        "description": "Organic tri-color quinoa tossed with cherry tomatoes, cucumbers, kalamata olives, feta cheese, and lemon herb vinaigrette.",
        "base_price": Decimal("210.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 12,
        "calories": 310,
        "recipes": [
            ("Organic Quinoa Seeds", Decimal("0.100"), UnitOfMeasure.KG),
            ("Extra Virgin Olive Oil", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-01",
        "category": "healthy-food",
        "name": "Grilled Paneer Protein Salad",
        "description": "Herb-crusted grilled malai paneer on a bed of fresh rocket leaves, crunchy bell peppers, walnuts, and aged balsamic glaze.",
        "base_price": Decimal("220.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 14,
        "calories": 360,
        "recipes": [
            ("Fresh Malai Paneer", Decimal("0.160"), UnitOfMeasure.KG),
            ("Extra Virgin Olive Oil", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-02",
        "category": "healthy-food",
        "name": "Grilled Chicken Caesar Salad",
        "description": "Slices of tender grilled chicken breast over crisp romaine lettuce, crunchy herb croutons, and creamy parmesan garlic dressing.",
        "base_price": Decimal("250.00"),
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 15,
        "calories": 380,
        "recipes": [
            ("Boneless Chicken Breast", Decimal("0.180"), UnitOfMeasure.KG),
            ("Extra Virgin Olive Oil", Decimal("0.015"), UnitOfMeasure.LITER),
        ],
    },
    {
        "kitchen": "CK-BLR-03",
        "category": "healthy-food",
        "name": "Avocado Green Detox Bowl",
        "description": "Fresh Hass avocado slices, steamed edamame, baby spinach, pumpkin seeds, and cold-pressed extra virgin olive oil dressing.",
        "base_price": Decimal("240.00"),
        "is_vegetarian": True,
        "is_available": True,
        "preparation_time_minutes": 12,
        "calories": 290,
        "recipes": [
            ("Extra Virgin Olive Oil", Decimal("0.020"), UnitOfMeasure.LITER),
        ],
    },
]

# ----------------------------------------------------------------------
# 5. Coupons Data (5 Development Coupons)
# ----------------------------------------------------------------------
COUPONS_DATA = [
    {
        "code": "WELCOME50",
        "description": "50% off on your first order up to Rs 150",
        "discount_type": DiscountType.PERCENTAGE,
        "discount_value": Decimal("50.00"),
        "min_order_value": Decimal("200.00"),
        "max_discount_amount": Decimal("150.00"),
        "valid_from": datetime(2026, 1, 1, 0, 0, 0),
        "valid_to": datetime(2027, 12, 31, 23, 59, 59),
        "usage_limit_per_user": 1,
        "total_usage_limit": 1000,
        "current_usage_count": 0,
        "is_active": True,
    },
    {
        "code": "GOURMET20",
        "description": "20% off on gourmet chef orders above Rs 299",
        "discount_type": DiscountType.PERCENTAGE,
        "discount_value": Decimal("20.00"),
        "min_order_value": Decimal("299.00"),
        "max_discount_amount": Decimal("100.00"),
        "valid_from": datetime(2026, 1, 1, 0, 0, 0),
        "valid_to": datetime(2027, 12, 31, 23, 59, 59),
        "usage_limit_per_user": 3,
        "total_usage_limit": 2000,
        "current_usage_count": 0,
        "is_active": True,
    },
    {
        "code": "FESTIVE100",
        "description": "Flat Rs 100 off on party and feast orders above Rs 499",
        "discount_type": DiscountType.FIXED_AMOUNT,
        "discount_value": Decimal("100.00"),
        "min_order_value": Decimal("499.00"),
        "max_discount_amount": None,
        "valid_from": datetime(2026, 1, 1, 0, 0, 0),
        "valid_to": datetime(2027, 12, 31, 23, 59, 59),
        "usage_limit_per_user": 5,
        "total_usage_limit": 500,
        "current_usage_count": 0,
        "is_active": True,
    },
    {
        "code": "FREESHIP",
        "description": "Free zero-fee delivery discount of Rs 40 on orders above Rs 150",
        "discount_type": DiscountType.FIXED_AMOUNT,
        "discount_value": Decimal("40.00"),
        "min_order_value": Decimal("150.00"),
        "max_discount_amount": None,
        "valid_from": datetime(2026, 1, 1, 0, 0, 0),
        "valid_to": datetime(2027, 12, 31, 23, 59, 59),
        "usage_limit_per_user": 10,
        "total_usage_limit": 5000,
        "current_usage_count": 0,
        "is_active": True,
    },
    {
        "code": "HEALTHY15",
        "description": "15% off up to Rs 75 on clean organic salads and bowls",
        "discount_type": DiscountType.PERCENTAGE,
        "discount_value": Decimal("15.00"),
        "min_order_value": Decimal("250.00"),
        "max_discount_amount": Decimal("75.00"),
        "valid_from": datetime(2026, 1, 1, 0, 0, 0),
        "valid_to": datetime(2027, 12, 31, 23, 59, 59),
        "usage_limit_per_user": 5,
        "total_usage_limit": 1000,
        "current_usage_count": 0,
        "is_active": True,
    },
]

# ----------------------------------------------------------------------
# 6. Supporting Development Accounts (Staff, Drivers, Demo Customer)
# ----------------------------------------------------------------------
DEV_USERS = [
    {
        "email": "admin@cloudkitchen.com",
        "phone_number": "+919876543210",
        "first_name": "Rajesh",
        "last_name": "Sharma",
        "role": UserRole.ADMIN,
        "password": "AdminPassword@123",
    },
    {
        "email": "arjun.mehta@gmail.com",
        "phone_number": "+919811122233",
        "first_name": "Arjun",
        "last_name": "Mehta",
        "role": UserRole.CUSTOMER,
        "password": "CustomerPassword@123",
        "customer": {
            "loyalty_points": 250,
            "dietary_preference": DietaryPreference.ALL,
        },
        "addresses": [
            {
                "address_label": "Home",
                "recipient_name": "Arjun Mehta",
                "recipient_phone": "+919811122233",
                "address_line1": "Flat 402, Sunshine Heights",
                "address_line2": "12th Main Road, HAL 2nd Stage, Indiranagar",
                "landmark": "Behind BDA Complex",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560038",
                "latitude": Decimal("12.97340000"),
                "longitude": Decimal("77.64320000"),
                "is_default": True,
            },
            {
                "address_label": "Work",
                "recipient_name": "Arjun Mehta",
                "recipient_phone": "+919811122233",
                "address_line1": "7th Floor, Tech Hub Tower B",
                "address_line2": "Bagmane Tech Park, CV Raman Nagar",
                "landmark": "Near Gate 2",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560093",
                "latitude": Decimal("12.98120000"),
                "longitude": Decimal("77.65980000"),
                "is_default": False,
            },
        ],
    },
    {
        "email": "priya.nair@gmail.com",
        "phone_number": "+919822233344",
        "first_name": "Priya",
        "last_name": "Nair",
        "role": UserRole.CUSTOMER,
        "password": "CustomerPassword@123",
        "customer": {
            "loyalty_points": 120,
            "dietary_preference": DietaryPreference.VEGETARIAN,
        },
        "addresses": [
            {
                "address_label": "Home",
                "recipient_name": "Priya Nair",
                "recipient_phone": "+919822233344",
                "address_line1": "Villa 18, Palm Meadows",
                "address_line2": "Varthur Main Road, Whitefield",
                "landmark": "Near Forum Mall",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560066",
                "latitude": Decimal("12.96010000"),
                "longitude": Decimal("77.74900000"),
                "is_default": True,
            },
        ],
    },
    {
        "email": "vikram.singh@cloudkitchen.com",
        "phone_number": "+919833344455",
        "first_name": "Vikram",
        "last_name": "Singh",
        "role": UserRole.KITCHEN_STAFF,
        "password": "StaffPassword@123",
        "staff": {
            "kitchen_branch": "CK-BLR-01",
            "staff_role": StaffRole.KITCHEN_MANAGER,
            "shift_timing": ShiftTiming.MORNING,
            "hired_date": date(2024, 1, 15),
        },
    },
    {
        "email": "ananya.deshmukh@cloudkitchen.com",
        "phone_number": "+919844455566",
        "first_name": "Ananya",
        "last_name": "Deshmukh",
        "role": UserRole.KITCHEN_STAFF,
        "password": "StaffPassword@123",
        "staff": {
            "kitchen_branch": "CK-BLR-01",
            "staff_role": StaffRole.HEAD_CHEF,
            "shift_timing": ShiftTiming.MORNING,
            "hired_date": date(2024, 2, 1),
        },
    },
    {
        "email": "karan.verma@cloudkitchen.com",
        "phone_number": "+919855566677",
        "first_name": "Karan",
        "last_name": "Verma",
        "role": UserRole.KITCHEN_STAFF,
        "password": "StaffPassword@123",
        "staff": {
            "kitchen_branch": "CK-BLR-02",
            "staff_role": StaffRole.HEAD_CHEF,
            "shift_timing": ShiftTiming.EVENING,
            "hired_date": date(2024, 4, 10),
        },
    },
    {
        "email": "rohit.sharma@cloudkitchen.com",
        "phone_number": "+919855566688",
        "first_name": "Rohit",
        "last_name": "Sharma",
        "role": UserRole.KITCHEN_STAFF,
        "password": "StaffPassword@123",
        "staff": {
            "kitchen_branch": "CK-BLR-03",
            "staff_role": StaffRole.KITCHEN_MANAGER,
            "shift_timing": ShiftTiming.MORNING,
            "hired_date": date(2024, 5, 1),
        },
    },
    {
        "email": "rohit.kumar@delivery.com",
        "phone_number": "+919866677788",
        "first_name": "Rohit",
        "last_name": "Kumar",
        "role": UserRole.DELIVERY_PERSON,
        "password": "DriverPassword@123",
        "delivery_person": {
            "vehicle_type": VehicleType.MOTORCYCLE,
            "vehicle_number": "KA-01-EQ-4021",
            "driving_license_number": "DL-KA-2018-002419",
            "current_status": DeliveryPersonStatus.AVAILABLE,
            "current_latitude": Decimal("12.97200000"),
            "current_longitude": Decimal("77.64200000"),
            "rating": Decimal("4.90"),
        },
    },
    {
        "email": "suresh.patil@delivery.com",
        "phone_number": "+919877788899",
        "first_name": "Suresh",
        "last_name": "Patil",
        "role": UserRole.DELIVERY_PERSON,
        "password": "DriverPassword@123",
        "delivery_person": {
            "vehicle_type": VehicleType.ELECTRIC_VEHICLE,
            "vehicle_number": "KA-03-EV-8842",
            "driving_license_number": "DL-KA-2020-009183",
            "current_status": DeliveryPersonStatus.AVAILABLE,
            "current_latitude": Decimal("12.93600000"),
            "current_longitude": Decimal("77.62500000"),
            "rating": Decimal("4.85"),
        },
    },
]


def seed_all():
    db = get_db_session()
    try:
        print("=" * 60)
        print("GOURMETCLOUD: Idempotent Database Seeding Initiated")
        print("=" * 60)

        # 1. Seed Kitchens
        print("\n[1/7] Seeding Kitchens...")
        kitchen_map = {}  # branch_code -> kitchen_id
        for k_data in KITCHENS_DATA:
            existing = db.query(Kitchen).filter_by(branch_code=k_data["branch_code"]).first()
            if not existing:
                kitchen = Kitchen(**k_data)
                db.add(kitchen)
                db.flush()
                print(f"  + Created kitchen: {kitchen.name} ({kitchen.branch_code})")
                kitchen_map[kitchen.branch_code] = kitchen.kitchen_id
            else:
                for k, v in k_data.items():
                    setattr(existing, k, v)
                db.flush()
                print(f"  = Updated kitchen: {existing.name} ({existing.branch_code})")
                kitchen_map[existing.branch_code] = existing.kitchen_id

        # 2. Seed Categories
        print("\n[2/7] Seeding Categories...")
        category_map = {}  # slug -> category_id
        for c_data in CATEGORIES_DATA:
            existing = db.query(Category).filter_by(slug=c_data["slug"]).first()
            if not existing:
                cat = Category(**c_data)
                db.add(cat)
                db.flush()
                print(f"  + Created category: {cat.name} ({cat.slug})")
                category_map[cat.slug] = cat.category_id
            else:
                for k, v in c_data.items():
                    setattr(existing, k, v)
                db.flush()
                print(f"  = Updated category: {existing.name} ({existing.slug})")
                category_map[existing.slug] = existing.category_id

        # 3. Seed Ingredients
        print("\n[3/7] Seeding Ingredients...")
        ingredient_map = {}  # name -> ingredient_id
        for ing_data in INGREDIENTS_DATA:
            existing = db.query(Ingredient).filter_by(name=ing_data["name"]).first()
            if not existing:
                ing = Ingredient(**ing_data)
                db.add(ing)
                db.flush()
                print(f"  + Created ingredient: {ing.name} [{ing.unit_of_measure.value}]")
                ingredient_map[ing.name] = ing.ingredient_id
            else:
                for k, v in ing_data.items():
                    setattr(existing, k, v)
                db.flush()
                print(f"  = Updated ingredient: {existing.name}")
                ingredient_map[existing.name] = existing.ingredient_id

        # 4. Seed Inventory for each Kitchen
        print("\n[4/7] Seeding Kitchen Inventories...")
        inv_created = 0
        inv_updated = 0
        now = datetime.utcnow()
        for branch_code, k_id in kitchen_map.items():
            for ing_name, ing_id in ingredient_map.items():
                existing = (
                    db.query(Inventory)
                    .filter_by(kitchen_id=k_id, ingredient_id=ing_id)
                    .first()
                )
                if not existing:
                    inv = Inventory(
                        kitchen_id=k_id,
                        ingredient_id=ing_id,
                        current_stock=Decimal("45.000"),
                        reorder_level=Decimal("10.000"),
                        last_restocked_at=now,
                    )
                    db.add(inv)
                    inv_created += 1
                else:
                    if existing.current_stock < Decimal("10.000"):
                        existing.current_stock = Decimal("50.000")
                        existing.last_restocked_at = now
                    inv_updated += 1
        db.flush()
        print(f"  Inventory records: {inv_created} created, {inv_updated} verified/updated.")

        # 5. Seed Menu Items & Recipes (BOM)
        print("\n[5/7] Seeding Menu Items and BOM Recipes...")
        menu_items_created = 0
        menu_items_updated = 0
        recipe_links_created = 0

        for item_data in MENU_ITEMS_DATA:
            k_id = kitchen_map[item_data["kitchen"]]
            cat_id = category_map[item_data["category"]]
            name = item_data["name"]

            menu_item = (
                db.query(MenuItem)
                .filter_by(kitchen_id=k_id, name=name)
                .first()
            )

            if not menu_item:
                menu_item = MenuItem(
                    kitchen_id=k_id,
                    category_id=cat_id,
                    name=name,
                    description=item_data["description"],
                    base_price=item_data["base_price"],
                    is_vegetarian=item_data["is_vegetarian"],
                    is_available=item_data["is_available"],
                    preparation_time_minutes=item_data["preparation_time_minutes"],
                    calories=item_data["calories"],
                )
                db.add(menu_item)
                db.flush()
                menu_items_created += 1
            else:
                menu_item.category_id = cat_id
                menu_item.description = item_data["description"]
                menu_item.base_price = item_data["base_price"]
                menu_item.is_vegetarian = item_data["is_vegetarian"]
                menu_item.is_available = item_data["is_available"]
                menu_item.preparation_time_minutes = item_data["preparation_time_minutes"]
                menu_item.calories = item_data["calories"]
                db.flush()
                menu_items_updated += 1

            # Attach BOM Recipes
            for ing_name, qty, unit in item_data.get("recipes", []):
                if ing_name in ingredient_map:
                    ing_id = ingredient_map[ing_name]
                    recipe = (
                        db.query(MenuItemIngredient)
                        .filter_by(menu_item_id=menu_item.menu_item_id, ingredient_id=ing_id)
                        .first()
                    )
                    if not recipe:
                        recipe = MenuItemIngredient(
                            menu_item_id=menu_item.menu_item_id,
                            ingredient_id=ing_id,
                            quantity_required=qty,
                            unit_of_measure=unit,
                        )
                        db.add(recipe)
                        recipe_links_created += 1
                    else:
                        recipe.quantity_required = qty
                        recipe.unit_of_measure = unit

        db.flush()
        print(f"  Menu items: {menu_items_created} created, {menu_items_updated} updated.")
        print(f"  Recipe BOM links: {recipe_links_created} created.")

        # 6. Seed Coupons
        print("\n[6/7] Seeding Promotional Coupons...")
        coupons_created = 0
        coupons_updated = 0
        for c_data in COUPONS_DATA:
            existing = db.query(Coupon).filter_by(code=c_data["code"]).first()
            if not existing:
                coupon = Coupon(**c_data)
                db.add(coupon)
                coupons_created += 1
                print(f"  + Created coupon: {c_data['code']}")
            else:
                for k, v in c_data.items():
                    setattr(existing, k, v)
                coupons_updated += 1
                print(f"  = Verified coupon: {c_data['code']}")
        db.flush()

        # 7. Seed Supporting Dev Users (Admins, Staff, Drivers, Customers)
        print("\n[7/7] Seeding Supporting Accounts...")
        for u_data in DEV_USERS:
            email = u_data["email"]
            existing_user = db.query(User).filter_by(email=email).first()

            if not existing_user:
                pwd_hash = hash_password(u_data["password"])
                user = User(
                    email=email,
                    phone_number=u_data["phone_number"],
                    password_hash=pwd_hash,
                    first_name=u_data["first_name"],
                    last_name=u_data["last_name"],
                    role=u_data["role"],
                    is_active=True,
                )
                db.add(user)
                db.flush()
                print(f"  + Created user: {user.email} [{user.role.value}]")
            else:
                user = existing_user
                print(f"  = Existing user: {user.email} [{user.role.value}]")

            # Customer Profile
            if "customer" in u_data:
                c_info = u_data["customer"]
                cust = db.query(Customer).filter_by(customer_id=user.user_id).first()
                if not cust:
                    cust = Customer(
                        customer_id=user.user_id,
                        loyalty_points=c_info["loyalty_points"],
                        dietary_preference=c_info["dietary_preference"],
                    )
                    db.add(cust)
                    db.flush()
                else:
                    cust.loyalty_points = c_info["loyalty_points"]
                    cust.dietary_preference = c_info["dietary_preference"]

            # Customer Addresses
            if "addresses" in u_data and user.customer:
                for addr_info in u_data["addresses"]:
                    existing_addr = (
                        db.query(Address)
                        .filter_by(customer_id=user.user_id, address_label=addr_info["address_label"])
                        .first()
                    )
                    if not existing_addr:
                        addr = Address(customer_id=user.user_id, **addr_info)
                        db.add(addr)
                    else:
                        for k, v in addr_info.items():
                            setattr(existing_addr, k, v)

            # Staff Profile
            if "staff" in u_data:
                s_info = u_data["staff"]
                k_id = kitchen_map.get(s_info["kitchen_branch"])
                if k_id:
                    staff_rec = db.query(Staff).filter_by(staff_id=user.user_id).first()
                    if not staff_rec:
                        staff_rec = Staff(
                            staff_id=user.user_id,
                            kitchen_id=k_id,
                            staff_role=s_info["staff_role"],
                            shift_timing=s_info["shift_timing"],
                            hired_date=s_info["hired_date"],
                        )
                        db.add(staff_rec)
                    else:
                        staff_rec.kitchen_id = k_id
                        staff_rec.staff_role = s_info["staff_role"]
                        staff_rec.shift_timing = s_info["shift_timing"]

            # Delivery Person Profile
            if "delivery_person" in u_data:
                dp_info = u_data["delivery_person"]
                dp_rec = db.query(DeliveryPerson).filter_by(delivery_person_id=user.user_id).first()
                if not dp_rec:
                    dp_rec = DeliveryPerson(delivery_person_id=user.user_id, **dp_info)
                    db.add(dp_rec)
                else:
                    for k, v in dp_info.items():
                        setattr(dp_rec, k, v)

        db.commit()
        print("\n[✓] Transaction committed successfully to MySQL database!")

        # 8. Invalidate Redis Caches
        try:
            from app.db.redis import redis_client

            keys_to_clear = ["popular:menu_items"]
            for branch_code, k_id in kitchen_map.items():
                keys_to_clear.append(f"menu:kitchen:{k_id}")
                keys_to_clear.append(f"kitchen:{k_id}:availability")

            for k in keys_to_clear:
                redis_client.delete(k)
            print("[✓] Flushed relevant Redis catalog cache keys.")
        except Exception as e:
            print(f"[-] Redis cache flush note: {e}")

        print("\n" + "=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Seeding failed, rolled back: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
