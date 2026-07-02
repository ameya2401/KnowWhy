from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth.tokens import token_service


def test_access_token_round_trip() -> None:
    user_id = uuid4()

    token = token_service.create_access_token(user_id)

    assert token_service.verify_token(token, expected_type="access") == user_id


def test_refresh_token_cannot_be_used_as_access_token() -> None:
    token = token_service.create_refresh_token(uuid4())

    with pytest.raises(HTTPException):
        token_service.verify_token(token, expected_type="access")
