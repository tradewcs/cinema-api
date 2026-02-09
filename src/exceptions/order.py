from fastapi import HTTPException, status

class OrderException(HTTPException):
    """Base exception for all order errors."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred in the order."
    ):
        super().__init__(status_code=status_code, detail=detail)

class CartNotFoundError(OrderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found for the given user."
        )

class CartEmptyError(OrderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart is empty."
        )

class OrdersNotExistError(OrderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current user doesn't have any order"
        )