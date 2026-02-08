from fastapi import APIRouter
from src.api.v1.accounts import router as accounts_router
api_router = APIRouter()

api_router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])