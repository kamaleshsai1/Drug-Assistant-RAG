# ============================================================
# DRUGASSIST AUTHENTICATION
# ============================================================
#
# Handles:
#   - Password hashing
#   - Password verification
#   - JWT access-token creation
#   - JWT token validation
#   - Current-user authentication for FastAPI routes
#
# Compatible with:
#   database.py
# ============================================================

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from database.database import get_user_by_id


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# JWT CONFIGURATION
# ============================================================

JWT_SECRET = os.getenv(
    "DRUGASSIST_JWT_SECRET"
)

JWT_ALGORITHM = "HS256"

TOKEN_EXPIRE_HOURS = 24 * 30  # 30 days for seamless persistent login


# ============================================================
# BEARER AUTHENTICATION
# ============================================================

security = HTTPBearer(
    auto_error=True
)


# ============================================================
# SECURITY VALIDATION
# ============================================================

if not JWT_SECRET:
    raise RuntimeError(
        "DRUGASSIST_JWT_SECRET is missing from .env"
    )


if JWT_SECRET == "CHANGE_THIS_SECRET":
    raise RuntimeError(
        "Please set a secure DRUGASSIST_JWT_SECRET in .env"
    )


if len(JWT_SECRET) < 16:
    raise RuntimeError(
        "DRUGASSIST_JWT_SECRET must contain at least "
        "16 characters."
    )


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(
    password: str,
) -> str:
    """
    Hash a user's password using bcrypt.

    The original password is never stored in the database.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    password_bytes = password.encode(
        "utf-8"
    )

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return hashed.decode(
        "utf-8"
    )


# ============================================================
# PASSWORD VERIFICATION
# ============================================================

def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """
    Verify a plain-text password against its bcrypt hash.

    Returns:
        True  -> password is correct
        False -> password is incorrect
    """

    if not password:
        return False

    if not password_hash:
        return False

    try:

        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    except (
        ValueError,
        TypeError,
        bcrypt.errors.InvalidHash,
    ):
        return False


# ============================================================
# JWT ACCESS TOKEN
# ============================================================

def create_access_token(
    user_id: int,
) -> str:
    """
    Create a JWT access token for a user.

    Token contains:
        sub -> user ID
        iat -> issued-at time
        exp -> expiration time
    """

    now = datetime.now(
        timezone.utc
    )

    expiration = (
        now
        + timedelta(
            hours=TOKEN_EXPIRE_HOURS
        )
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expiration,
    }

    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return token


# ============================================================
# JWT DECODING
# ============================================================

def decode_access_token(
    token: str,
) -> dict:
    """
    Decode and validate a JWT access token.

    Raises:
        HTTP 401 when the token is invalid or expired.
    """

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication token is required.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        return payload

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail=(
                "Session expired. "
                "Please login again."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid authentication token."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    """
    FastAPI dependency used by protected endpoints.

    Example:

        @app.get("/protected")
        def protected_route(
            user=Depends(get_current_user)
        ):
            ...

    Returns the authenticated user's public database record.
    """

    token = credentials.credentials

    payload = decode_access_token(
        token
    )

    user_id = payload.get(
        "sub"
    )

    if user_id is None:

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid authentication token."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    try:

        user_id = int(user_id)

    except (
        TypeError,
        ValueError,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid user ID.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    user = get_user_by_id(
        user_id
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail=(
                "User account not found."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    return user


# ============================================================
# CURRENT USER ID
# ============================================================

def get_current_user_id(
    user=Depends(get_current_user),
) -> int:
    """
    Convenience FastAPI dependency that returns only the
    authenticated user's ID.

    This is useful for routes that only need the user ID.

    Example:

        @app.get("/my-data")
        def my_data(
            user_id: int = Depends(
                get_current_user_id
            )
        ):
            ...
    """

    return int(
        user["id"]
    )


# ============================================================
# DIRECT MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("DrugAssist Authentication Test")
    print("=" * 60)

    print(
        "JWT secret: configured"
        if JWT_SECRET
        else "JWT secret: missing"
    )

    # --------------------------------------------------------
    # Password test
    # --------------------------------------------------------

    test_password = "DrugAssistTest@2026"

    hashed = hash_password(
        test_password
    )

    valid_password = verify_password(
        test_password,
        hashed,
    )

    invalid_password = verify_password(
        "wrong-password",
        hashed,
    )

    print(
        f"Password hashing: "
        f"{'OK' if valid_password else 'FAILED'}"
    )

    print(
        f"Wrong password rejection: "
        f"{'OK' if not invalid_password else 'FAILED'}"
    )

    # --------------------------------------------------------
    # JWT test
    # --------------------------------------------------------

    test_user_id = 1

    token = create_access_token(
        test_user_id
    )

    decoded = decode_access_token(
        token
    )

    jwt_ok = (
        decoded.get("sub")
        == str(test_user_id)
    )

    print(
        f"JWT creation/decoding: "
        f"{'OK' if jwt_ok else 'FAILED'}"
    )

    print("=" * 60)

    if (
        valid_password
        and not invalid_password
        and jwt_ok
    ):
        print(
            "AUTH MODULE OK"
        )
    else:
        print(
            "AUTH MODULE FAILED"
        )

    print("=" * 60)