import json
import logging
from typing import Dict, List, Optional
from app.db.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory dictionary fallback in case Redis server is offline
_in_memory_cart_fallback: Dict[int, Dict[str, str]] = {}


class CartRepository:
    @staticmethod
    def _get_cart_key(customer_id: int) -> str:
        return f"cart:{customer_id}"

    @classmethod
    def get_cart_raw(cls, customer_id: int) -> Dict[str, dict]:
        """
        Retrieves raw cart items mapping string(menu_item_id) -> JSON dict.
        Returns dict: { "item_id": { "quantity": int, "customization_notes": str } }
        """
        client = redis_client.get_client()
        cart_data = {}
        if client:
            try:
                raw_hash = client.hgetall(cls._get_cart_key(customer_id))
                for item_id_str, val_str in raw_hash.items():
                    try:
                        cart_data[item_id_str] = json.loads(val_str)
                    except Exception:
                        pass
                return cart_data
            except Exception as e:
                logger.warning(f"Redis cart fetch error: {e}")

        # Fallback
        fallback = _in_memory_cart_fallback.get(customer_id, {})
        for item_id_str, val_str in fallback.items():
            try:
                cart_data[item_id_str] = json.loads(val_str)
            except Exception:
                pass
        return cart_data

    @classmethod
    def set_item(cls, customer_id: int, menu_item_id: int, quantity: int, notes: Optional[str] = None) -> bool:
        """Stores item quantity and notes in Redis cart hash."""
        payload = json.dumps({"quantity": quantity, "customization_notes": notes})
        key = cls._get_cart_key(customer_id)
        client = redis_client.get_client()

        if client:
            try:
                client.hset(key, str(menu_item_id), payload)
                client.expire(key, 7 * 86400)  # 7-day rolling TTL
                return True
            except Exception as e:
                logger.warning(f"Redis cart set error: {e}")

        # In-memory fallback
        if customer_id not in _in_memory_cart_fallback:
            _in_memory_cart_fallback[customer_id] = {}
        _in_memory_cart_fallback[customer_id][str(menu_item_id)] = payload
        return True

    @classmethod
    def remove_item(cls, customer_id: int, menu_item_id: int) -> bool:
        """Removes single item from cart."""
        key = cls._get_cart_key(customer_id)
        client = redis_client.get_client()
        if client:
            try:
                client.hdel(key, str(menu_item_id))
                return True
            except Exception as e:
                logger.warning(f"Redis cart remove error: {e}")

        fallback = _in_memory_cart_fallback.get(customer_id)
        if fallback and str(menu_item_id) in fallback:
            del fallback[str(menu_item_id)]
        return True

    @classmethod
    def clear_cart(cls, customer_id: int) -> bool:
        """Flushes the entire cart for a customer."""
        key = cls._get_cart_key(customer_id)
        client = redis_client.get_client()
        if client:
            try:
                client.delete(key)
                client.delete(f"{key}:coupon")
                return True
            except Exception as e:
                logger.warning(f"Redis cart clear error: {e}")

        _in_memory_cart_fallback.pop(customer_id, None)
        return True

    @classmethod
    def set_coupon(cls, customer_id: int, coupon_code: str) -> bool:
        key = f"{cls._get_cart_key(customer_id)}:coupon"
        return redis_client.set(key, coupon_code.upper().strip(), ttl_seconds=7 * 86400)

    @classmethod
    def get_coupon(cls, customer_id: int) -> Optional[str]:
        key = f"{cls._get_cart_key(customer_id)}:coupon"
        return redis_client.get(key)

    @classmethod
    def remove_coupon(cls, customer_id: int) -> bool:
        key = f"{cls._get_cart_key(customer_id)}:coupon"
        return redis_client.delete(key)
