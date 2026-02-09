from fastapi import APIRouter

from src.api.v1.movies import router as movies_router
from src.api.v1.genres import router as genres_router
from src.api.v1.stars import router as stars_router
from src.api.v1.directors import router as directors_router
from src.api.v1.certifications import router as certifications_router
from src.api.v1.accounts import router as accounts_router
from src.api.v1.cart import router as cart_router
from src.api.v1.orders import router as order_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(movies_router)
api_router.include_router(genres_router)
api_router.include_router(stars_router)
api_router.include_router(directors_router)
api_router.include_router(certifications_router)
api_router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(cart_router, prefix="/cart", tags=["Shopping Cart"])
api_router.include_router(order_router, prefix="/order", tags=["Order"])