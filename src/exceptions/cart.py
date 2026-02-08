from fastapi import HTTPException, status

class CartException(HTTPException):
    """Base exception for all shopping cart errors."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred in the shopping cart."
    ):
        super().__init__(status_code=status_code, detail=detail)

class CartNotFoundError(CartException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found for the given user."
        )

class CartItemAlreadyExistsError(CartException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="This movie is already in your cart."
        )

class MovieAlreadyPurchasedError(CartException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already purchased this movie. Double purchases are not allowed."
        )

class MovieNotAvailableError(CartException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested movie does not exist or is unavailable."
        )