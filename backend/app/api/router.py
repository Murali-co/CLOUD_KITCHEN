from fastapi import APIRouter

from app.api.routes import (
    health,
    auth,
    customer,
    kitchens,
    categories,
    cuisines,
    menu,
    cart,
    checkout,
    orders,
    payments,
    kitchen,
    inventory,
    delivery,
    admin,
)

api_router = APIRouter()

# Mount all endpoint modules under /api/v1
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(customer.router)
api_router.include_router(kitchens.router)
api_router.include_router(categories.router)
api_router.include_router(cuisines.router)
api_router.include_router(menu.router)
api_router.include_router(cart.router)
api_router.include_router(checkout.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(kitchen.router)
api_router.include_router(inventory.router)
api_router.include_router(delivery.router)
api_router.include_router(admin.router)


