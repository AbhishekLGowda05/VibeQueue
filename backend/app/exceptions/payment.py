"""app/exceptions/payment.py"""
from fastapi import HTTPException, status

class PaymentVerificationError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PAYMENT_VERIFICATION_FAILED", "message": "Payment signature verification failed."},
        )
