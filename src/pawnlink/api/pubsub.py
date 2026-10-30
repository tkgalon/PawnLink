import base64
import binascii
import json

from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


def verify_push_token(authorization: str | None, audience: str, service_account: str) -> None:
    # Pub/Sub signs each push with a Google ID token for our push service account;
    # anything else hitting this public endpoint is turned away.
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        claims = id_token.verify_oauth2_token(
            authorization.removeprefix("Bearer "), google_requests.Request(), audience=audience
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail="invalid token") from e
    if claims.get("email") != service_account or not claims.get("email_verified"):
        raise HTTPException(status_code=403, detail="unexpected sender")


def decode_url(data: str) -> str | None:
    """Message data is base64 of either {"url": "..."} or the bare URL."""
    try:
        text = base64.b64decode(data, validate=True).decode().strip()
    except (binascii.Error, UnicodeDecodeError):
        return None
    if text.startswith("{"):
        try:
            text = json.loads(text).get("url", "")
        except (json.JSONDecodeError, AttributeError):
            return None
    return text if isinstance(text, str) and text else None
