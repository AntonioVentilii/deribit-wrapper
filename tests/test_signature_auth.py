import hmac
import hashlib
import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives.serialization import (
    PrivateFormat,
    NoEncryption,
    Encoding,
)

from deribit_wrapper.authentication import Authentication
from deribit_wrapper.exceptions import DeribitClientWarning

token_mock_response = {
    "access_token": "sig_access_token",
    "expires_in": 3600,
    "refresh_token": "sig_refresh_token",
}


def test_signature_symmetric_init():
    """Test initializing with symmetric signature auth_method."""
    auth = Authentication(
        env="test",
        client_id="dummy_id",
        client_secret="dummy_secret",
        auth_method="signature",
    )
    assert auth.auth_method == "signature"
    assert auth.client_id == "dummy_id"
    assert auth.client_secret == "dummy_secret"


def test_signature_asymmetric_init_from_pkey_obj():
    """Test initializing with asymmetric private key object."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    auth = Authentication(env="test", client_id="dummy_id", private_key=private_key)
    # private_key promotion should auto-set auth_method to 'asymmetric'
    assert auth.auth_method == "asymmetric"
    assert auth.client_id == "dummy_id"
    assert auth.private_key == private_key


def test_symmetric_signature_calculation():
    """Test that HMAC-SHA256 signature is calculated correctly."""
    client_secret = "my_secret_key"
    auth = Authentication(
        env="test",
        client_id="dummy_id",
        client_secret=client_secret,
        auth_method="signature",
    )

    timestamp = 1715678900000
    nonce = "random_nonce"
    data = ""

    sig = auth._generate_signature(timestamp, nonce, data)

    # Manually calculate expected signature
    message = f"{timestamp}\n{nonce}\n{data}".encode("utf-8")
    expected = hmac.new(
        client_secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()

    assert sig == expected


def test_asymmetric_ed25519_signature_calculation():
    """Test that Ed25519 asymmetric signature is generated and can be verified."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    auth = Authentication(env="test", client_id="dummy_id", private_key=private_key)

    timestamp = 1715678900000
    nonce = "random_nonce"
    data = ""

    sig_hex = auth._generate_signature(timestamp, nonce, data)
    sig_bytes = bytes.fromhex(sig_hex)

    # Verify the signature using cryptography public key
    message = f"{timestamp}\n{nonce}\n{data}".encode("utf-8")
    public_key.verify(
        sig_bytes, message
    )  # Should not raise cryptography.exceptions.InvalidSignature


def test_asymmetric_pem_string_signature_calculation():
    """Test loading and signing with PEM private key string."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    pem_bytes = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
    pem_string = pem_bytes.decode("utf-8")

    auth = Authentication(env="test", client_id="dummy_id", private_key=pem_string)

    timestamp = 1715678900000
    nonce = "random_nonce"
    data = ""

    sig_hex = auth._generate_signature(timestamp, nonce, data)
    sig_bytes = bytes.fromhex(sig_hex)

    message = f"{timestamp}\n{nonce}\n{data}".encode("utf-8")
    private_key.public_key().verify(sig_bytes, message)


def test_asymmetric_pem_file_signature_calculation(tmp_path):
    """Test loading and signing with PEM private key file path."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    pem_bytes = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )

    key_file = tmp_path / "private.pem"
    key_file.write_bytes(pem_bytes)

    auth = Authentication(env="test", client_id="dummy_id", private_key=str(key_file))

    timestamp = 1715678900000
    nonce = "random_nonce"
    data = ""

    sig_hex = auth._generate_signature(timestamp, nonce, data)
    sig_bytes = bytes.fromhex(sig_hex)

    message = f"{timestamp}\n{nonce}\n{data}".encode("utf-8")
    private_key.public_key().verify(sig_bytes, message)


@patch("deribit_wrapper.authentication.Authentication._request")
def test_get_new_token_symmetric_signature(mock_request):
    """Test get_new_token with symmetric client_signature grant."""
    mock_request.return_value = token_mock_response

    auth = Authentication(
        env="test",
        client_id="my_id",
        client_secret="my_secret",
        auth_method="signature",
    )

    token = auth.get_new_token()
    assert token == "sig_access_token"

    mock_request.assert_called_once()
    call_args = mock_request.call_args[0]
    uri = call_args[0]
    params = call_args[1]

    assert uri == "/public/auth"
    assert params["grant_type"] == "client_signature"
    assert params["client_id"] == "my_id"
    assert "timestamp" in params
    assert "nonce" in params
    assert "signature" in params
    assert params["data"] == ""


@patch("deribit_wrapper.authentication.Authentication._request")
def test_get_new_token_asymmetric_signature(mock_request):
    """Test get_new_token with asymmetric client_signature grant."""
    mock_request.return_value = token_mock_response
    private_key = ed25519.Ed25519PrivateKey.generate()

    auth = Authentication(env="test", client_id="my_id", private_key=private_key)

    token = auth.get_new_token()
    assert token == "sig_access_token"

    mock_request.assert_called_once()
    call_args = mock_request.call_args[0]
    uri = call_args[0]
    params = call_args[1]

    assert uri == "/public/auth"
    assert params["grant_type"] == "client_signature"
    assert params["client_id"] == "my_id"
    assert "signature" in params


def test_missing_credentials_warnings():
    """Test warning behavior on missing symmetric or asymmetric credentials."""
    # Standard warning when Client Secret/ID is missing in credentials auth_method
    with pytest.warns(DeribitClientWarning):
        Authentication(env="test", auth_method="credentials")

    # Standard warning when Client Secret/ID is missing in signature auth_method
    with pytest.warns(DeribitClientWarning):
        Authentication(env="test", auth_method="signature")

    # Warning when Private Key is missing in asymmetric auth_method
    with pytest.warns(DeribitClientWarning):
        Authentication(env="test", auth_method="asymmetric", client_id="dummy_id")
