"""app/exceptions/venue.py"""
from fastapi import HTTPException, status

class VenueNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "VENUE_NOT_FOUND", "message": "Venue not found."},
        )

class VenueInactiveError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "VENUE_INACTIVE", "message": "VibeQueue is not active at this venue tonight."},
        )
