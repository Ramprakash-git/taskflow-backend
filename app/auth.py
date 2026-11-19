import os
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    PyJWTError,
    PyJWKClientError,
    PyJWKClientConnectionError,
)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


security = HTTPBearer(auto_error=False)


def get_cognito_config():
    region = os.getenv("COGNITO_REGION")
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
    app_client_id = os.getenv("COGNITO_APP_CLIENT_ID")

    if not all([region, user_pool_id, app_client_id]):
        raise RuntimeError("Cognito environment variables are missing")

    issuer = (
        f"https://cognito-idp.{region}.amazonaws.com/"
        f"{user_pool_id}"
    )

    return issuer, app_client_id


@lru_cache
def get_jwks_client(issuer: str):
    jwks_url = f"{issuer}/.well-known/jwks.json"
    return PyJWKClient(jwks_url)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        issuer, app_client_id = get_cognito_config()

        token = credentials.credentials

        signing_key = get_jwks_client(
            issuer
        ).get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_aud": False},
        )

        if claims.get("token_use") != "access":
            raise HTTPException(
                status_code=401,
                detail="Access token required",
            )

        if claims.get("client_id") != app_client_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid Cognito app client",
            )

        user_sub = claims.get("sub")

        if not user_sub:
            raise HTTPException(
                status_code=401,
                detail="Invalid user identity",
            )

        return {
            "sub": user_sub,
            "username": claims.get("username"),
        }

    except PyJWKClientConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Unable to reach Cognito for token verification",
        )

    except (PyJWTError, PyJWKClientError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )