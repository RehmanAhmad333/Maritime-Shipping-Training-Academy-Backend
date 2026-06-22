from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address, default_limits=["500/minute"])

def _rate_limit_exceeded_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )