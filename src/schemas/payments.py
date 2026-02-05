from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field

from database import payment_validators
from  import PaymentStatusEnum

class CreatePaymentSchema(BaseModel):
    user_id: int
    order_id: int
    status: PaymentStatusEnum
    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return accounts_validators.validate_email(value.lower())
