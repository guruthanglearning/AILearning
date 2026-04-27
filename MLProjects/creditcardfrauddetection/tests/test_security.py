"""
Tests for app/core/security.py (currently 36% coverage).
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_api_key_hash,
    verify_api_key,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core.config import settings


# ── create_access_token ───────────────────────────────────────────────────────

class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token({"sub": "user1"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_with_custom_expires_delta(self):
        token = create_access_token({"sub": "user1"}, expires_delta=timedelta(minutes=5))
        assert isinstance(token, str)

    def test_with_zero_expires_delta(self):
        token = create_access_token({"sub": "user1"}, expires_delta=timedelta(seconds=0))
        assert isinstance(token, str)

    def test_token_contains_data(self):
        token = create_access_token({"sub": "testuser", "role": "admin"})
        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"

    def test_default_expiry_added(self):
        token = create_access_token({"sub": "user"})
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_empty_data(self):
        token = create_access_token({})
        assert isinstance(token, str)


# ── decode_access_token ───────────────────────────────────────────────────────

class TestDecodeAccessToken:
    def test_valid_token_decoded(self):
        token = create_access_token({"sub": "alice"})
        payload = decode_access_token(token)
        assert payload["sub"] == "alice"

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("this.is.not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_401(self):
        token = create_access_token({"sub": "user"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(tampered)
        assert exc_info.value.status_code == 401

    def test_empty_string_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("")
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        token = create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        assert exc_info.value.status_code == 401

    def test_roundtrip_preserves_all_fields(self):
        data = {"sub": "bob", "role": "analyst", "dept": "fraud"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload["sub"] == "bob"
        assert payload["role"] == "analyst"
        assert payload["dept"] == "fraud"


# ── get_api_key_hash ──────────────────────────────────────────────────────────

class TestGetApiKeyHash:
    def test_returns_string(self):
        h = get_api_key_hash("my_api_key")
        assert isinstance(h, str)

    def test_hash_is_64_chars(self):
        # SHA-256 hex digest is always 64 characters
        h = get_api_key_hash("any_key")
        assert len(h) == 64

    def test_same_key_same_hash(self):
        assert get_api_key_hash("key123") == get_api_key_hash("key123")

    def test_different_keys_different_hashes(self):
        assert get_api_key_hash("key_a") != get_api_key_hash("key_b")

    def test_empty_string(self):
        h = get_api_key_hash("")
        assert isinstance(h, str)
        assert len(h) == 64


# ── verify_api_key ────────────────────────────────────────────────────────────

class TestVerifyApiKey:
    def test_valid_key_returns_true(self):
        assert verify_api_key(settings.API_KEY) is True

    def test_invalid_key_returns_false(self):
        assert verify_api_key("wrong_key_12345") is False

    def test_empty_string_returns_false(self):
        assert verify_api_key("") is False

    def test_partial_key_returns_false(self):
        partial = settings.API_KEY[:5] if len(settings.API_KEY) > 5 else "x"
        assert verify_api_key(partial) is False

    def test_case_sensitive(self):
        assert verify_api_key(settings.API_KEY.upper()) is False or \
               verify_api_key(settings.API_KEY.upper()) == (settings.API_KEY.upper() == settings.API_KEY)


# ── constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_algorithm_is_hs256(self):
        assert ALGORITHM == "HS256"

    def test_default_expiry_is_30_minutes(self):
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30
