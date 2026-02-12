class PaymentError(Exception):
    pass


# general


class PaymentDoesNotExist(PaymentError):
    pass


# create session error


class PaymentSessionError(PaymentError):
    pass


class PaymentAmountMismatch(PaymentSessionError):
    pass


class PaymentNotAllowed(PaymentSessionError):
    pass


class OrderNotFoundError(PaymentError):
    pass


# webhook error


class WebHookPaymentError(PaymentError):
    pass


class InvalidPayload(WebHookPaymentError):
    pass


class InvalidSignature(WebHookPaymentError):
    pass


class SessionDoesNotExistError(WebHookPaymentError):
    pass
