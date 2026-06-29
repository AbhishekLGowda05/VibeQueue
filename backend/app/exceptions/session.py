"""app/exceptions/session.py"""
from fastapi import HTTPException, status

class InvalidTableCodeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TABLE_CODE", "message": "Invalid or expired table code."},
        )

class SessionExpiredError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "SESSION_EXPIRED", "message": "Your session has ended. Get the new table code from your waiter."},
        )
