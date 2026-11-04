import pytest
from datetime import date, datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password, create_access_token
from app.db.database import Base, get_db
from app.db.redis import redis_client, InMemoryRedisClient
from app.main import app
from app.models import (
    User,
    Customer,
    Staff,
    DeliveryPerson,
    UserRole,
    DietaryPreference,
    StaffRole,
    ShiftTiming,
    VehicleType,
    Kitchen,
    OperatingStatus,
    Category,
    MenuItem,
    Cuisine,
    Address,
    Coupon,
    DiscountType,
    DeliveryPersonStatus,
    Delivery,
    DeliveryStatus,
)
from app.models.inventory import Ingredient, Inventory, MenuItemIngredient, UnitOfMeasure

# In-memory SQLite for isolated, fast, non-destructive automated testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis client in memory for automated test speed and isolation."""
    mock = InMemoryRedisClient()
    orig = redis_client._client
    redis_client._client = mock
    yield mock
    redis_client._client = orig


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all schema tables in memory."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provides a transactional database session rolled back after every test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed baseline fixtures
    seed_fixtures(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def seed_fixtures(db):
    """Seeds baseline accounts, kitchens, dishes, and coupons for tests."""
    pwd = hash_password("Password@123")

    # 1. Customer user
    u_cust = User(
        user_id=10,
        email="customer1@test.com",
        phone_number="+919800000001",
        password_hash=pwd,
        first_name="Test",
        last_name="Customer",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(u_cust)
    db.flush()

    c_cust = Customer(
        customer_id=u_cust.user_id,
        loyalty_points=100,
        dietary_preference=DietaryPreference.ALL,
    )
    db.add(c_cust)

    # 2. Another Customer user
    u_other = User(
        user_id=20,
        email="customer2@test.com",
        phone_number="+919800000002",
        password_hash=pwd,
        first_name="Other",
        last_name="User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(u_other)
    db.flush()

    c_other = Customer(
        customer_id=u_other.user_id,
        loyalty_points=50,
        dietary_preference=DietaryPreference.VEGETARIAN,
    )
    db.add(c_other)

    # 3. Inactive Customer
    u_inactive = User(
        user_id=30,
        email="inactive@test.com",
        phone_number="+919800000003",
        password_hash=pwd,
        first_name="Inactive",
        last_name="User",
        role=UserRole.CUSTOMER,
        is_active=False,
    )
    db.add(u_inactive)

    # 4. Admin
    u_admin = User(
        user_id=40,
        email="admin@test.com",
        phone_number="+919800000004",
        password_hash=pwd,
        first_name="Super",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(u_admin)

    # Kitchens
    k1 = Kitchen(
        kitchen_id=1,
        name="Indiranagar Cloud Kitchen",
        branch_code="CK-IND-01",
        contact_phone="+918012345678",
        email="indiranagar@test.com",
        address_line1="100 Feet Rd",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560038",
        operating_status=OperatingStatus.ACTIVE,
    )
    k2 = Kitchen(
        kitchen_id=2,
        name="Koramangala Cloud Kitchen",
        branch_code="CK-KOR-02",
        contact_phone="+918087654321",
        email="koramangala@test.com",
        address_line1="80 Feet Rd",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560034",
        operating_status=OperatingStatus.ACTIVE,
    )
    db.add_all([k1, k2])
    db.flush()

    # Category
    cat1 = Category(category_id=1, name="Gourmet Bowls", slug="gourmet-bowls", is_active=True)
    cat2 = Category(category_id=2, name="Artisan Pizzas", slug="artisan-pizzas", is_active=True)
    db.add_all([cat1, cat2])
    db.flush()

    # Cuisines
    cuisines_list = [
        (1, "South Indian", "south-indian", 1),
        (2, "North Indian", "north-indian", 2),
        (3, "Chinese", "chinese", 3),
        (4, "Italian", "italian", 4),
        (5, "Japanese", "japanese", 5),
        (6, "Korean", "korean", 6),
        (7, "Mexican", "mexican", 7),
        (8, "American", "american", 8),
        (9, "Arabian", "arabian", 9),
        (10, "Thai", "thai", 10),
        (11, "Mediterranean", "mediterranean", 11),
        (12, "French", "french", 12),
        (13, "Hyderabadi", "hyderabadi", 13),
        (14, "Kerala", "kerala", 14),
        (15, "Maharashtrian", "maharashtrian", 15),
    ]
    db.add_all([
        Cuisine(
            cuisine_id=cid,
            cuisine_name=cname,
            cuisine_slug=cslug,
            cuisine_description=f"Authentic {cname} delicacies",
            cuisine_image_url="https://images.unsplash.com/photo-example",
            is_active=True,
            display_order=dorder,
        )
        for cid, cname, cslug, dorder in cuisines_list
    ])
    db.flush()

    # Menu Items
    dish1 = MenuItem(
        menu_item_id=1,
        kitchen_id=1,
        category_id=1,
        cuisine_id=2,
        name="Butter Chicken Rice Bowl",
        base_price=Decimal("320.00"),
        is_vegetarian=False,
        is_available=True,
    )
    dish2 = MenuItem(
        menu_item_id=2,
        kitchen_id=1,
        category_id=2,
        cuisine_id=4,
        name="Classic Margherita Pizza",
        base_price=Decimal("380.00"),
        is_vegetarian=True,
        is_available=True,
    )
    dish3 = MenuItem(
        menu_item_id=3,
        kitchen_id=1,
        category_id=1,
        cuisine_id=1,
        name="Out of Stock Dish",
        base_price=Decimal("200.00"),
        is_vegetarian=True,
        is_available=False,
    )
    dish_k2 = MenuItem(
        menu_item_id=4,
        kitchen_id=2,
        category_id=1,
        cuisine_id=13,
        name="Koramangala Special Biryani",
        base_price=Decimal("350.00"),
        is_vegetarian=False,
        is_available=True,
    )
    db.add_all([dish1, dish2, dish3, dish_k2])

    # Customer 1 Address
    addr1 = Address(
        address_id=1,
        customer_id=10,
        address_label="Home",
        recipient_name="Test Customer",
        recipient_phone="+919800000001",
        address_line1="Flat 101, Test Residency",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560038",
        is_default=True,
    )
    # Customer 2 Address
    addr2 = Address(
        address_id=2,
        customer_id=20,
        address_label="Office",
        recipient_name="Other User",
        recipient_phone="+919800000002",
        address_line1="Office 202, Tech Park",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560093",
        is_default=True,
    )
    db.add_all([addr1, addr2])

    # Coupons
    c1 = Coupon(
        coupon_id=1,
        code="TEST50",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50.00"),
        min_order_value=Decimal("200.00"),
        max_discount_amount=Decimal("150.00"),
        valid_from=datetime(2020, 1, 1),
        valid_to=datetime(2030, 12, 31),
        usage_limit_per_user=2,
        total_usage_limit=1000,
        is_active=True,
    )
    c2 = Coupon(
        coupon_id=2,
        code="EXPIRED10",
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=Decimal("100.00"),
        min_order_value=Decimal("100.00"),
        valid_from=datetime(2020, 1, 1),
        valid_to=datetime(2021, 1, 1),
        usage_limit_per_user=1,
        total_usage_limit=1000,
        is_active=True,
    )
    db.add_all([c1, c2])

    # Kitchen Staff
    # User 50: Manager for Kitchen 1
    u_km1 = User(
        user_id=50,
        email="manager1@test.com",
        phone_number="+919800000050",
        password_hash=pwd,
        first_name="Vikram",
        last_name="Singh",
        role=UserRole.KITCHEN_STAFF,
        is_active=True,
    )
    # User 51: Line Cook for Kitchen 1
    u_ks1 = User(
        user_id=51,
        email="staff1@test.com",
        phone_number="+919800000051",
        password_hash=pwd,
        first_name="Ananya",
        last_name="Deshmukh",
        role=UserRole.KITCHEN_STAFF,
        is_active=True,
    )
    # User 52: Staff for Kitchen 2
    u_ks2 = User(
        user_id=52,
        email="staff2@test.com",
        phone_number="+919800000052",
        password_hash=pwd,
        first_name="Karan",
        last_name="Verma",
        role=UserRole.KITCHEN_STAFF,
        is_active=True,
    )
    db.add_all([u_km1, u_ks1, u_ks2])
    db.flush()

    s_km1 = Staff(
        staff_id=50,
        kitchen_id=1,
        staff_role=StaffRole.KITCHEN_MANAGER,
        shift_timing=ShiftTiming.MORNING,
        hired_date=date(2024, 1, 1),
    )
    s_ks1 = Staff(
        staff_id=51,
        kitchen_id=1,
        staff_role=StaffRole.LINE_COOK,
        shift_timing=ShiftTiming.MORNING,
        hired_date=date(2024, 2, 1),
    )
    s_ks2 = Staff(
        staff_id=52,
        kitchen_id=2,
        staff_role=StaffRole.LINE_COOK,
        shift_timing=ShiftTiming.EVENING,
        hired_date=date(2024, 3, 1),
    )
    db.add_all([s_km1, s_ks1, s_ks2])

    # Ingredients
    ing1 = Ingredient(ingredient_id=1, name="Basmati Rice", category="Grains", unit_of_measure=UnitOfMeasure.KG)
    ing2 = Ingredient(ingredient_id=2, name="Boneless Chicken", category="Meat", unit_of_measure=UnitOfMeasure.KG)
    ing3 = Ingredient(ingredient_id=3, name="Paneer", category="Dairy", unit_of_measure=UnitOfMeasure.KG)
    db.add_all([ing1, ing2, ing3])
    db.flush()

    # Inventories
    # Kitchen 1: Rice=50kg (reorder=10), Chicken=20kg (reorder=5), Paneer=2kg (reorder=5 -> LOW STOCK)
    inv1_1 = Inventory(inventory_id=1, kitchen_id=1, ingredient_id=1, current_stock=Decimal("50.000"), reorder_level=Decimal("10.000"))
    inv1_2 = Inventory(inventory_id=2, kitchen_id=1, ingredient_id=2, current_stock=Decimal("20.000"), reorder_level=Decimal("5.000"))
    inv1_3 = Inventory(inventory_id=3, kitchen_id=1, ingredient_id=3, current_stock=Decimal("2.000"), reorder_level=Decimal("5.000"))
    # Kitchen 2
    inv2_1 = Inventory(inventory_id=4, kitchen_id=2, ingredient_id=1, current_stock=Decimal("30.000"), reorder_level=Decimal("10.000"))
    db.add_all([inv1_1, inv1_2, inv1_3, inv2_1])
    db.flush()

    # Recipe for Dish 1 ("Butter Chicken Rice Bowl"): 0.150kg Rice, 0.180kg Chicken
    rec1 = MenuItemIngredient(menu_item_id=1, ingredient_id=1, quantity_required=Decimal("0.150"), unit_of_measure=UnitOfMeasure.KG)
    rec2 = MenuItemIngredient(menu_item_id=1, ingredient_id=2, quantity_required=Decimal("0.180"), unit_of_measure=UnitOfMeasure.KG)
    db.add_all([rec1, rec2])

    # Delivery Personnel
    # User 60: Delivery Driver 1 (Available)
    u_dp1 = User(
        user_id=60,
        email="driver1@test.com",
        phone_number="+919800000060",
        password_hash=pwd,
        first_name="Ramesh",
        last_name="Kumar",
        role=UserRole.DELIVERY_PERSON,
        is_active=True,
    )
    # User 61: Delivery Driver 2 (Available)
    u_dp2 = User(
        user_id=61,
        email="driver2@test.com",
        phone_number="+919800000061",
        password_hash=pwd,
        first_name="Suresh",
        last_name="Patil",
        role=UserRole.DELIVERY_PERSON,
        is_active=True,
    )
    # User 62: Delivery Driver 3 (Off Duty)
    u_dp3 = User(
        user_id=62,
        email="driver3@test.com",
        phone_number="+919800000062",
        password_hash=pwd,
        first_name="Mahesh",
        last_name="Rao",
        role=UserRole.DELIVERY_PERSON,
        is_active=True,
    )
    db.add_all([u_dp1, u_dp2, u_dp3])
    db.flush()

    dp1 = DeliveryPerson(
        delivery_person_id=60,
        vehicle_type=VehicleType.MOTORCYCLE,
        vehicle_number="KA-01-AB-1234",
        driving_license_number="DL-KA-2020-001",
        current_status=DeliveryPersonStatus.AVAILABLE,
        rating=Decimal("4.85"),
    )
    dp2 = DeliveryPerson(
        delivery_person_id=61,
        vehicle_type=VehicleType.SCOOTER,
        vehicle_number="KA-01-CD-5678",
        driving_license_number="DL-KA-2021-002",
        current_status=DeliveryPersonStatus.AVAILABLE,
        rating=Decimal("4.60"),
    )
    dp3 = DeliveryPerson(
        delivery_person_id=62,
        vehicle_type=VehicleType.MOTORCYCLE,
        vehicle_number="KA-01-EF-9999",
        driving_license_number="DL-KA-2022-003",
        current_status=DeliveryPersonStatus.OFF_DUTY,
        rating=Decimal("4.90"),
    )
    db.add_all([dp1, dp2, dp3])

    db.commit()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def customer_auth_headers():
    """Generates valid Bearer authorization header for Customer 1."""
    token = create_access_token(subject=10)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_customer_auth_headers():
    """Generates valid Bearer authorization header for Customer 2."""
    token = create_access_token(subject=20)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers():
    """Generates valid Bearer authorization header for Admin."""
    token = create_access_token(subject=40)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def kitchen_manager_headers():
    """Generates valid Bearer authorization header for Kitchen Manager 1."""
    token = create_access_token(subject=50)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def kitchen_staff_headers():
    """Generates valid Bearer authorization header for Kitchen Staff 1."""
    token = create_access_token(subject=51)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def kitchen2_staff_headers():
    """Generates valid Bearer authorization header for Kitchen 2 Staff."""
    token = create_access_token(subject=52)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def delivery_auth_headers():
    """Generates valid Bearer authorization header for Delivery Driver 1."""
    token = create_access_token(subject=60)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_delivery_auth_headers():
    """Generates valid Bearer authorization header for Delivery Driver 2."""
    token = create_access_token(subject=61)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def off_duty_delivery_auth_headers():
    """Generates valid Bearer authorization header for Delivery Driver 3 (Off-duty)."""
    token = create_access_token(subject=62)
    return {"Authorization": f"Bearer {token}"}


