import pytest
import json
from scripts.redis_crud_demo import RedisCRUDDemo, DEMO_NAMESPACE
from app.db.redis import InMemoryRedisClient


@pytest.fixture
def in_memory_demo_runner():
    """In-memory mock client fixture for isolated fallback testing."""
    demo = RedisCRUDDemo()
    demo.client = InMemoryRedisClient()
    demo.is_live = False
    yield demo
    demo.cleanup_demo_keys()


@pytest.fixture
def live_redis_demo_runner():
    """Live Redis client fixture connecting to real Redis 7.0 engine."""
    demo = RedisCRUDDemo()
    yield demo
    demo.cleanup_demo_keys()


def test_real_redis_live_operations(live_redis_demo_runner):
    """
    VERIFIED LIVE REDIS TEST:
    Executes real Redis operations (Hash, String, TTL, Sorted Set) directly
    against the running Redis 7.0 engine without mocks.
    """
    if not live_redis_demo_runner.is_live:
        pytest.skip("Live Redis engine is offline; skipping live engine test.")

    # 1. Live Hash Test
    cart_key = live_redis_demo_runner.k("cart:live:test")
    live_redis_demo_runner.client.hset(cart_key, "101", json.dumps({"dish": "Pizza", "qty": 1}))
    live_redis_demo_runner.client.expire(cart_key, 300)
    assert live_redis_demo_runner.client.ttl(cart_key) > 0
    raw = live_redis_demo_runner.client.hget(cart_key, "101")
    assert raw is not None
    assert json.loads(raw)["dish"] == "Pizza"

    # 2. Live Sorted Set (Leaderboard) Test
    zset_key = live_redis_demo_runner.k("leaderboard:live:test")
    live_redis_demo_runner.client.zadd(zset_key, {"Dish A": 10.0, "Dish B": 25.0})
    live_redis_demo_runner.client.zincrby(zset_key, 20.0, "Dish A")  # Now 30.0
    top = live_redis_demo_runner.client.zrevrange(zset_key, 0, 0, withscores=True)
    assert top[0][0] == "Dish A"
    assert top[0][1] == 30.0

    # 3. Live Cleanup Test
    live_redis_demo_runner.cleanup_demo_keys()
    assert live_redis_demo_runner.client.exists(cart_key) == 0
    assert live_redis_demo_runner.client.exists(zset_key) == 0


def test_redis_crud_create_and_read_cart(in_memory_demo_runner):
    """Verify storing customer shopping cart items in Redis Hash (In-Memory)."""
    cart_key = in_memory_demo_runner.k("cart:customer:999")
    item_payload = json.dumps({
        "menu_item_id": 501,
        "name": "Classic Margherita Pizza",
        "quantity": 2,
        "unit_price": 320.00
    })

    in_memory_demo_runner.client.hset(cart_key, "501", item_payload)
    fetched = in_memory_demo_runner.client.hget(cart_key, "501")
    assert fetched is not None
    data = json.loads(fetched)
    assert data["name"] == "Classic Margherita Pizza"
    assert data["quantity"] == 2


def test_redis_crud_update_cart_quantity(in_memory_demo_runner):
    """Verify mutating item quantity in cart hash (In-Memory)."""
    cart_key = in_memory_demo_runner.k("cart:customer:999")
    item_payload = json.dumps({
        "menu_item_id": 501,
        "name": "Classic Margherita Pizza",
        "quantity": 2,
        "unit_price": 320.00
    })
    in_memory_demo_runner.client.hset(cart_key, "501", item_payload)

    # Update quantity to 4
    updated_payload = json.dumps({
        "menu_item_id": 501,
        "name": "Classic Margherita Pizza",
        "quantity": 4,
        "unit_price": 320.00
    })
    in_memory_demo_runner.client.hset(cart_key, "501", updated_payload)

    fetched = json.loads(in_memory_demo_runner.client.hget(cart_key, "501"))
    assert fetched["quantity"] == 4


def test_redis_crud_delete_cart_item(in_memory_demo_runner):
    """Verify field deletion and full key eviction (In-Memory)."""
    cart_key = in_memory_demo_runner.k("cart:customer:999")
    in_memory_demo_runner.client.hset(cart_key, "501", "item1")
    in_memory_demo_runner.client.hset(cart_key, "502", "item2")

    # Delete 501
    in_memory_demo_runner.client.hdel(cart_key, "501")
    remaining = in_memory_demo_runner.client.hgetall(cart_key)
    assert "501" not in remaining
    assert "502" in remaining

    # Clear entire cart
    in_memory_demo_runner.client.delete(cart_key)
    assert len(in_memory_demo_runner.client.hgetall(cart_key)) == 0


def test_redis_crud_string_menu_cache(in_memory_demo_runner):
    """Verify string operations for catalog caching and TTL expiration (In-Memory)."""
    menu_key = in_memory_demo_runner.k("menu:kitchen:5")
    payload = {"kitchen_id": 5, "dishes": ["Pasta", "Pizza"]}
    in_memory_demo_runner.client.set(menu_key, json.dumps(payload), ex=3600)

    raw = in_memory_demo_runner.client.get(menu_key)
    assert raw is not None
    parsed = json.loads(raw)
    assert parsed["kitchen_id"] == 5

    # Delete cache (Cache invalidation on menu update)
    in_memory_demo_runner.client.delete(menu_key)
    assert in_memory_demo_runner.client.get(menu_key) is None


def test_redis_crud_targeted_cleanup(in_memory_demo_runner):
    """Verify cleanup purges only demonstration namespace keys (In-Memory)."""
    key1 = in_memory_demo_runner.k("cart:test:1")
    key2 = in_memory_demo_runner.k("session:test:1")
    in_memory_demo_runner.client.set(key1, "val1")
    in_memory_demo_runner.client.set(key2, "val2")

    assert in_memory_demo_runner.client.get(key1) == "val1"
    assert in_memory_demo_runner.client.get(key2) == "val2"

    in_memory_demo_runner.cleanup_demo_keys()
    assert in_memory_demo_runner.client.get(key1) is None
    assert in_memory_demo_runner.client.get(key2) is None
