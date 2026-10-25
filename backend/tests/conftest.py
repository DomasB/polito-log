import os

# app.config builds Settings at import time, so the test key must be set before
# any app module is imported. It differs from DEFAULT_JWT_SECRET_KEY on purpose.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret")
