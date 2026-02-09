from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.cart import CartReadSchema, CartItemAddSchema
from src.services.cart import CartService
from src.dependencies.user import get_current_user, get_admin_user
from src.models.accounts import User

router = APIRouter()

@router.get("/my", response_model=CartReadSchema)
async def get_my_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the current user's shopping cart details.
    """
    return await CartService(db).get_user_cart(user_id=current_user.id)

@router.post("/add", response_model=CartReadSchema, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    schema: CartItemAddSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Adds a movie to the cart and returns the updated cart state.
    """
    return await CartService(db).add_item_to_cart(
        user_id=current_user.id,
        movie_id=schema.movie_id
    )

@router.delete("/remove/{movie_id}", response_model=CartReadSchema)
async def remove_item(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Removes a single item from the cart by movie ID.
    """
    return await CartService(db).remove_from_cart(
        user_id=current_user.id,
        movie_id=movie_id
    )

@router.delete("/clear", response_model=CartReadSchema)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Removes all items from the current user's cart.
    """
    return await CartService(db).clear_user_cart(user_id=current_user.id)

@router.get("/{user_id}", response_model=CartReadSchema)
async def get_user_cart_admin(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Allows administrators to view the cart of any user.
    """
    return await CartService(db).get_user_cart(user_id=user_id)