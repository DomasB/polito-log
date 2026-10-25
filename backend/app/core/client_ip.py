from typing import Optional
from fastapi import Request

from app.config import settings


def get_client_ip(request: Request) -> Optional[str]:
    """
    Dependency returning the client's IP address.

    Behind TRUSTED_PROXY_HOPS proxies, the client IP is the X-Forwarded-For
    entry that many places from the right: entries further left were sent by
    the client and can be forged.

    Args:
        request: Incoming request

    Returns:
        IP address, or None if unknown
    """
    hops = settings.TRUSTED_PROXY_HOPS
    forwarded = request.headers.get("x-forwarded-for")
    if hops > 0 and forwarded:
        entries = [entry.strip() for entry in forwarded.split(",") if entry.strip()]
        if entries:
            return entries[-hops] if len(entries) >= hops else entries[0]
    return request.client.host if request.client else None
