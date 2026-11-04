"""
GourmetCloud - Idempotent Cuisine Catalog Seeder
Seeds the 15 distinct culinary cuisines with realistic descriptions, unique images,
display orders, slugs, and maps existing menu items to cuisines.
"""

import os
import sys
from dotenv import dotenv_values

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.cuisine import Cuisine
from app.models.kitchen import MenuItem


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


CUISINES_DATA = [
    {
        "cuisine_id": 1,
        "cuisine_name": "South Indian",
        "cuisine_slug": "south-indian",
        "cuisine_description": "Crispy fermented dosas, steamed fluffy idlis, crunchy medu vadas, and aromatic filter coffees from the southern peninsula.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80",
        "display_order": 1,
        "is_active": True,
    },
    {
        "cuisine_id": 2,
        "cuisine_name": "North Indian",
        "cuisine_slug": "north-indian",
        "cuisine_description": "Rich slow-cooked gravies, buttery dal makhani, tender tandoori paneer, hot butter naans, and Mughlai culinary feasts.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80",
        "display_order": 2,
        "is_active": True,
    },
    {
        "cuisine_id": 3,
        "cuisine_name": "Chinese",
        "cuisine_slug": "chinese",
        "cuisine_description": "Wok-seared Hakka noodles, crispy Manchurian sizzlers, aromatic dim sums, and flavor-packed Indo-Chinese street favorites.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
        "display_order": 3,
        "is_active": True,
    },
    {
        "cuisine_id": 4,
        "cuisine_name": "Italian",
        "cuisine_slug": "italian",
        "cuisine_description": "Stone-baked artisan sourdough pizzas, al dente penne in velvety cream and pomodoro sauces, and fresh fragrant basil.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80",
        "display_order": 4,
        "is_active": True,
    },
    {
        "cuisine_id": 5,
        "cuisine_name": "Japanese",
        "cuisine_slug": "japanese",
        "cuisine_description": "Artisanal hand-rolled sushi, slow-simmered umami ramen bowls, delicate tempura crunches, and savory teriyaki glazes.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=600&q=80",
        "display_order": 5,
        "is_active": True,
    },
    {
        "cuisine_id": 6,
        "cuisine_name": "Korean",
        "cuisine_slug": "korean",
        "cuisine_description": "Fiery gochujang glazed double-crunch chicken, spicy fermented kimchi, hearty bibimbap, and savory tteokbokki.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1498654896293-37aacf113fd9?auto=format&fit=crop&w=600&q=80",
        "display_order": 6,
        "is_active": True,
    },
    {
        "cuisine_id": 7,
        "cuisine_name": "Mexican",
        "cuisine_slug": "mexican",
        "cuisine_description": "Zesty soft tacos, loaded corn chips with creamy queso, stuffed burritos, and fresh tomato pico de gallo.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=600&q=80",
        "display_order": 7,
        "is_active": True,
    },
    {
        "cuisine_id": 8,
        "cuisine_name": "American",
        "cuisine_slug": "american",
        "cuisine_description": "Gourmet smashed brioche burgers, crispy seasoned fries, smoky barbecue chicken wings, and artisanal milkshakes.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80",
        "display_order": 8,
        "is_active": True,
    },
    {
        "cuisine_id": 9,
        "cuisine_name": "Arabian",
        "cuisine_slug": "arabian",
        "cuisine_description": "Fragrant saffron-tinted mandi rice, slow-turned chicken shawarma, velvety chickpea hummus, and warm stone pita.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&q=80",
        "display_order": 9,
        "is_active": True,
    },
    {
        "cuisine_id": 10,
        "cuisine_name": "Thai",
        "cuisine_slug": "thai",
        "cuisine_description": "Exquisite balance of sweet, sour, salty, and spicy in aromatic green coconut curries, Pad Thai, and Tom Yum.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=600&q=80",
        "display_order": 10,
        "is_active": True,
    },
    {
        "cuisine_id": 11,
        "cuisine_name": "Mediterranean",
        "cuisine_slug": "mediterranean",
        "cuisine_description": "Nutritious organic quinoa bowls, Greek salads with aged feta, crispy spiced falafels, and cold-pressed extra virgin olive oil.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80",
        "display_order": 11,
        "is_active": True,
    },
    {
        "cuisine_id": 12,
        "cuisine_name": "French",
        "cuisine_slug": "french",
        "cuisine_description": "Masterful pastry arts, flaky golden croissants, savory potato gratins, rich velouté sauces, and delicate fruit tarts.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=600&q=80",
        "display_order": 12,
        "is_active": True,
    },
    {
        "cuisine_id": 13,
        "cuisine_name": "Hyderabadi",
        "cuisine_slug": "hyderabadi",
        "cuisine_description": "Royal Nizami dum-cooked saffron basmati biryanis, spicy mirchi ka salan, slow-simmered haleem, and shahi tukda.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80",
        "display_order": 13,
        "is_active": True,
    },
    {
        "cuisine_id": 14,
        "cuisine_name": "Kerala",
        "cuisine_slug": "kerala",
        "cuisine_description": "Coastal coconut curries, flaky layered Malabar parottas, tempered pepper roasts, and crispy appams.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=600&q=80",
        "display_order": 14,
        "is_active": True,
    },
    {
        "cuisine_id": 15,
        "cuisine_name": "Maharashtrian",
        "cuisine_slug": "maharashtrian",
        "cuisine_description": "Iconic Mumbai street food delights, buttery spiced pav bhaji, fiery misal pav, and crunchy sabudana vadas.",
        "cuisine_image_url": "https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80",
        "display_order": 15,
        "is_active": True,
    },
]

# Mapping dish names (partial match or exact) to cuisine slugs
ITEM_CUISINE_MAPPINGS = {
    # South Indian
    "Masala Dosa": "south-indian",
    "Idli Vada Combo": "south-indian",
    "Ghee Mysore Masala Dosa": "south-indian",
    "Medu Vada (2 pcs)": "south-indian",
    "Masala Chai Flask (500ml)": "south-indian",

    # North Indian
    "Paneer Butter Masala": "north-indian",
    "Butter Naan": "north-indian",
    "Dal Makhani": "north-indian",
    "Kadai Chicken": "north-indian",
    "Garlic Naan": "north-indian",
    "Paneer Tikka": "north-indian",
    "Crispy Corn Pepper Salt": "north-indian",
    "Tandoori Chicken Wings (6 pcs)": "north-indian",
    "Dahi Ke Kebab": "north-indian",
    "Veg Biryani": "north-indian",
    "Jeera Rice with Dal Tadka": "north-indian",
    "Gulab Jamun (2 pcs)": "north-indian",
    "Rasmalai (2 pcs)": "north-indian",
    "Mango Lassi": "north-indian",

    # Chinese
    "Gobi Manchurian": "chinese",
    "Veg Hakka Noodles": "chinese",
    "Chicken Fried Rice": "chinese",
    "Chilli Chicken Dry": "chinese",
    "Veg Schezwan Fried Rice": "chinese",

    # Italian
    "Margherita Pizza": "italian",
    "Creamy White Sauce Penne Pasta": "italian",
    "Spicy Pepperoni Pizza": "italian",
    "Red Sauce Arrabiata Pasta": "italian",

    # American
    "Classic Veg Burger": "american",
    "Crispy Chicken Burger": "american",
    "Chocolate Brownie": "american",
    "Cold Coffee": "american",

    # Hyderabadi
    "Chicken Biryani": "hyderabadi",
    "Mutton Dum Biryani": "hyderabadi",

    # Maharashtrian
    "Bombay Grilled Sandwich": "maharashtrian",

    # Mediterranean
    "Mediterranean Quinoa Salad Bowl": "mediterranean",
    "Grilled Paneer Protein Salad": "mediterranean",
    "Grilled Chicken Caesar Salad": "mediterranean",
    "Avocado Green Detox Bowl": "mediterranean",
    "Fresh Lime Soda": "mediterranean",

    # French
    "New York Baked Cheesecake": "french",
    "Paneer Tikka Panini": "french",
}


def seed_cuisines():
    db = get_db_session()
    try:
        print("=" * 60)
        print("GOURMETCLOUD: Seeding 15 Cuisines & Dish Relationships")
        print("=" * 60)

        cuisine_map = {}  # slug -> cuisine_id
        inserted_count = 0
        updated_count = 0

        for c_data in CUISINES_DATA:
            existing = db.query(Cuisine).filter(
                (Cuisine.cuisine_slug == c_data["cuisine_slug"]) |
                (Cuisine.cuisine_name == c_data["cuisine_name"])
            ).first()

            if not existing:
                cuisine = Cuisine(
                    cuisine_name=c_data["cuisine_name"],
                    cuisine_slug=c_data["cuisine_slug"],
                    cuisine_description=c_data["cuisine_description"],
                    cuisine_image_url=c_data["cuisine_image_url"],
                    display_order=c_data["display_order"],
                    is_active=c_data["is_active"],
                )
                db.add(cuisine)
                db.flush()
                cuisine_map[cuisine.cuisine_slug] = cuisine.cuisine_id
                inserted_count += 1
                print(f"  + Inserted cuisine [{cuisine.cuisine_id}]: {cuisine.cuisine_name} ({cuisine.cuisine_slug})")
            else:
                existing.cuisine_name = c_data["cuisine_name"]
                existing.cuisine_slug = c_data["cuisine_slug"]
                existing.cuisine_description = c_data["cuisine_description"]
                existing.cuisine_image_url = c_data["cuisine_image_url"]
                existing.display_order = c_data["display_order"]
                existing.is_active = c_data["is_active"]
                db.flush()
                cuisine_map[existing.cuisine_slug] = existing.cuisine_id
                updated_count += 1
                print(f"  = Updated cuisine [{existing.cuisine_id}]: {existing.cuisine_name}")

        print(f"\n[✓] Cuisines: {inserted_count} inserted, {updated_count} updated.")

        # Map Menu Items to Cuisines
        print("\nMapping Menu Items to Cuisines...")
        mapped_count = 0
        all_items = db.query(MenuItem).all()
        for item in all_items:
            slug = ITEM_CUISINE_MAPPINGS.get(item.name)
            if slug and slug in cuisine_map:
                c_id = cuisine_map[slug]
                if item.cuisine_id != c_id:
                    item.cuisine_id = c_id
                    mapped_count += 1

        db.commit()
        print(f"[✓] Successfully linked {mapped_count} dishes to their respective cuisines!")

        # Flush Redis caches
        try:
            from app.db.redis import redis_client
            redis_client.delete("popular:menu_items")
            # Clear all menu caches
            for key in redis_client.keys("menu:*"):
                redis_client.delete(key)
            print("[✓] Flushed menu Redis caches.")
        except Exception as e:
            print(f"[-] Redis note: {e}")

        print("=" * 60)
        print("CUISINE SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed cuisines: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_cuisines()
