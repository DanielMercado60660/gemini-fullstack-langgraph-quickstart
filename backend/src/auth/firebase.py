import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

def initialize_firebase_app():
    """Initializes the Firebase Admin SDK."""
    try:
        # If GOOGLE_APPLICATION_CREDENTIALS is set, it will use that.
        # Otherwise, it will try to find default credentials.
        firebase_admin.initialize_app()
        print("Firebase app initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase app: {e}")
        # Depending on the application's needs, you might want to raise the exception
        # or handle it in a way that allows the app to continue running without Firebase.
        raise

async def verify_firebase_token(
    http_auth: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> dict:
    """
    Verifies the Firebase ID token from the Authorization header.

    Args:
        http_auth: The HTTP authorization credentials.

    Returns:
        The decoded token (user claims).

    Raises:
        HTTPException: If the token is invalid, expired, or not provided.
    """
    if http_auth is None or http_auth.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = http_auth.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except firebase_admin.auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"Token has expired\""},
        )
    except firebase_admin.auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"Invalid token\""},
        )
    except Exception as e:
        # Catch any other Firebase Admin SDK errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during token verification: {e}",
        )
