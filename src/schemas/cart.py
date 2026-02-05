from datetime import datetime
from typing import List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

# TODO: Import GenreSchema from movies module when available
class CartMovieGenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CartMovieReadSchema(BaseModel):
    """Short movie information for the cart view"""
    id: int
    name: str
    price: Decimal
    # TODO: Implement logic to extract only the release year from the movie's date
    year: int
    genres: List[CartMovieGenreSchema]

    model_config = ConfigDict(from_attributes=True)


class CartItemReadSchema(BaseModel):
    """Cart item details"""
    id: int
    movie_id: int
    added_at: datetime
    movie: CartMovieReadSchema

    model_config = ConfigDict(from_attributes=True)


class CartReadSchema(BaseModel):
    """Full cart information including nested items"""
    id: int
    user_id: int
    items: List[CartItemReadSchema]
    # TODO: Implement total items and total price calculation in Service/CRUD layer
    total_items: int
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class CartItemAddSchema(BaseModel):
    """Schema for adding a movie to the cart"""
    movie_id: int = Field(..., description="The ID of the movie to add")

    # TODO: Add validation to check if the movie was already purchased (via Service/Dependency)
    model_config = ConfigDict(from_attributes=True)