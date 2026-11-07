/**
 * GourmetCloud - Menu Item Image Resolver & Neutral Fallback
 * Provides deterministic mapping to genuine, dish-specific local photographs
 * in /assets/menu/ and supplies an elegant neutral SVG placeholder if an image is missing.
 */

// Neutral SVG placeholder: Elegant cloche/cutlery plate silhouette on soft warm background
export const NEUTRAL_FOOD_PLACEHOLDER =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="450" viewBox="0 0 600 450" fill="none">
  <rect width="600" height="450" fill="#F5F2EC"/>
  <circle cx="300" cy="225" r="90" fill="#EAE4D9"/>
  <path d="M260 225C260 202.909 277.909 185 300 185C322.091 185 340 202.909 340 225H260Z" fill="#C8BCA8"/>
  <rect x="250" y="228" width="100" height="6" rx="3" fill="#A89B84"/>
  <circle cx="300" cy="177" r="7" fill="#A89B84"/>
  <path d="M280 250H320" stroke="#C8BCA8" stroke-width="3" stroke-linecap="round"/>
  <text x="300" y="278" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="600" fill="#8F826E" text-anchor="middle" letter-spacing="1">GOURMET DISH</text>
</svg>
`);

// Primary Mapping by MenuItem ID
const MENU_ITEM_ID_MAP = {
  1: "/assets/menu/masala-dosa.jpg",
  2: "/assets/menu/idli-vada-combo.jpg",
  3: "/assets/menu/ghee-mysore-masala-dosa.jpg",
  4: "/assets/menu/medu-vada.jpg",
  5: "/assets/menu/paneer-butter-masala.jpg",
  6: "/assets/menu/butter-naan.jpg",
  7: "/assets/menu/dal-makhani.jpg",
  8: "/assets/menu/kadai-chicken.jpg",
  9: "/assets/menu/garlic-naan.jpg",
  10: "/assets/menu/gobi-manchurian.jpg",
  11: "/assets/menu/veg-hakka-noodles.jpg",
  12: "/assets/menu/chicken-fried-rice.jpg",
  13: "/assets/menu/chilli-chicken-dry.jpg",
  14: "/assets/menu/veg-schezwan-fried-rice.jpg",
  15: "/assets/menu/paneer-tikka.jpg",
  16: "/assets/menu/crispy-corn-pepper-salt.jpg",
  17: "/assets/menu/tandoori-chicken-wings.jpg",
  18: "/assets/menu/dahi-ke-kebab.jpg",
  19: "/assets/menu/chicken-biryani.jpg",
  20: "/assets/menu/veg-biryani.jpg",
  21: "/assets/menu/mutton-dum-biryani.jpg",
  22: "/assets/menu/jeera-rice-dal-tadka.jpg",
  23: "/assets/menu/classic-veg-burger.jpg",
  24: "/assets/menu/crispy-chicken-burger.jpg",
  25: "/assets/menu/bombay-grilled-sandwich.jpg",
  26: "/assets/menu/paneer-tikka-panini.jpg",
  27: "/assets/menu/margherita-pizza.jpg",
  28: "/assets/menu/creamy-white-sauce-penne-pasta.jpg",
  29: "/assets/menu/spicy-pepperoni-pizza.jpg",
  30: "/assets/menu/red-sauce-arrabiata-pasta.jpg",
  31: "/assets/menu/chocolate-brownie.jpg",
  32: "/assets/menu/gulab-jamun.jpg",
  33: "/assets/menu/rasmalai.jpg",
  34: "/assets/menu/new-york-baked-cheesecake.jpg",
  35: "/assets/menu/mango-lassi.jpg",
  36: "/assets/menu/cold-coffee.jpg",
  37: "/assets/menu/fresh-lime-soda.jpg",
  38: "/assets/menu/masala-chai.jpg",
  39: "/assets/menu/mediterranean-quinoa-salad-bowl.jpg",
  40: "/assets/menu/grilled-paneer-protein-salad.jpg",
  41: "/assets/menu/grilled-chicken-caesar-salad.jpg",
  42: "/assets/menu/avocado-green-detox-bowl.jpg",
};

// Normalized dish name fallback map
const NORM_NAME_MAP = {
  "masala dosa": "/assets/menu/masala-dosa.jpg",
  "idli vada combo": "/assets/menu/idli-vada-combo.jpg",
  "ghee mysore masala dosa": "/assets/menu/ghee-mysore-masala-dosa.jpg",
  "medu vada": "/assets/menu/medu-vada.jpg",
  "medu vada (2 pcs)": "/assets/menu/medu-vada.jpg",
  "paneer butter masala": "/assets/menu/paneer-butter-masala.jpg",
  "butter naan": "/assets/menu/butter-naan.jpg",
  "dal makhani": "/assets/menu/dal-makhani.jpg",
  "kadai chicken": "/assets/menu/kadai-chicken.jpg",
  "garlic naan": "/assets/menu/garlic-naan.jpg",
  "gobi manchurian": "/assets/menu/gobi-manchurian.jpg",
  "veg hakka noodles": "/assets/menu/veg-hakka-noodles.jpg",
  "chicken fried rice": "/assets/menu/chicken-fried-rice.jpg",
  "chilli chicken dry": "/assets/menu/chilli-chicken-dry.jpg",
  "veg schezwan fried rice": "/assets/menu/veg-schezwan-fried-rice.jpg",
  "paneer tikka": "/assets/menu/paneer-tikka.jpg",
  "crispy corn pepper salt": "/assets/menu/crispy-corn-pepper-salt.jpg",
  "tandoori chicken wings": "/assets/menu/tandoori-chicken-wings.jpg",
  "tandoori chicken wings (6 pcs)": "/assets/menu/tandoori-chicken-wings.jpg",
  "dahi ke kebab": "/assets/menu/dahi-ke-kebab.jpg",
  "chicken biryani": "/assets/menu/chicken-biryani.jpg",
  "veg biryani": "/assets/menu/veg-biryani.jpg",
  "mutton dum biryani": "/assets/menu/mutton-dum-biryani.jpg",
  "jeera rice with dal tadka": "/assets/menu/jeera-rice-dal-tadka.jpg",
  "classic veg burger": "/assets/menu/classic-veg-burger.jpg",
  "crispy chicken burger": "/assets/menu/crispy-chicken-burger.jpg",
  "bombay grilled sandwich": "/assets/menu/bombay-grilled-sandwich.jpg",
  "paneer tikka panini": "/assets/menu/paneer-tikka-panini.jpg",
  "margherita pizza": "/assets/menu/margherita-pizza.jpg",
  "creamy white sauce penne pasta": "/assets/menu/creamy-white-sauce-penne-pasta.jpg",
  "spicy pepperoni pizza": "/assets/menu/spicy-pepperoni-pizza.jpg",
  "red sauce arrabiata pasta": "/assets/menu/red-sauce-arrabiata-pasta.jpg",
  "chocolate brownie": "/assets/menu/chocolate-brownie.jpg",
  "gulab jamun": "/assets/menu/gulab-jamun.jpg",
  "gulab jamun (2 pcs)": "/assets/menu/gulab-jamun.jpg",
  "rasmalai": "/assets/menu/rasmalai.jpg",
  "rasmalai (2 pcs)": "/assets/menu/rasmalai.jpg",
  "new york baked cheesecake": "/assets/menu/new-york-baked-cheesecake.jpg",
  "mango lassi": "/assets/menu/mango-lassi.jpg",
  "cold coffee": "/assets/menu/cold-coffee.jpg",
  "fresh lime soda": "/assets/menu/fresh-lime-soda.jpg",
  "masala chai": "/assets/menu/masala-chai.jpg",
  "masala chai flask (500ml)": "/assets/menu/masala-chai.jpg",
  "mediterranean quinoa salad bowl": "/assets/menu/mediterranean-quinoa-salad-bowl.jpg",
  "grilled paneer protein salad": "/assets/menu/grilled-paneer-protein-salad.jpg",
  "grilled chicken caesar salad": "/assets/menu/grilled-chicken-caesar-salad.jpg",
  "avocado green detox bowl": "/assets/menu/avocado-green-detox-bowl.jpg",
};

/**
 * Returns the genuine dish-specific food photograph URL for any menu item.
 * Prioritizes custom dish.image_url (if not the generic salad photo),
 * then matches by ID, then by normalized dish name.
 * If no image matches, returns the neutral food placeholder.
 */
export function getMenuItemImage(dish) {
  if (!dish) return NEUTRAL_FOOD_PLACEHOLDER;

  // Check if dish has custom valid image that isn't the old generic salad placeholder
  if (
    dish.image_url &&
    !dish.image_url.includes("photo-1546069901-ba9599a7e63c")
  ) {
    return dish.image_url;
  }

  // 1. Direct match by menu_item_id
  if (dish.menu_item_id && MENU_ITEM_ID_MAP[dish.menu_item_id]) {
    return MENU_ITEM_ID_MAP[dish.menu_item_id];
  }

  // 2. Match by normalized name
  if (dish.name) {
    const cleaned = dish.name.toLowerCase().trim();
    if (NORM_NAME_MAP[cleaned]) {
      return NORM_NAME_MAP[cleaned];
    }
    // Partial search inside name
    for (const [key, path] of Object.entries(NORM_NAME_MAP)) {
      if (cleaned.includes(key) || key.includes(cleaned)) {
        return path;
      }
    }
  }

  // Neutral fallback (no wrong dish photo)
  return NEUTRAL_FOOD_PLACEHOLDER;
}
