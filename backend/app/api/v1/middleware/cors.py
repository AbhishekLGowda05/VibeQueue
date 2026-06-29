"""
app/api/v1/middleware/cors.py

CORS configuration note.
The actual CORS middleware is registered in app/main.py (CORSMiddleware).
This file exists as the documentation and override point for any
route-level CORS customisation needed later (e.g., webhook endpoints
that need to accept requests from Razorpay's servers specifically).
"""
# CORS is configured globally in app/main.py via:
#   app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, ...)
# No additional code needed here for pilot phase.
