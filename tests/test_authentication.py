import os
from unittest import TestCase, skipIf
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

from deribit_wrapper.authentication import Authentication
from deribit_wrapper.exceptions import (
    DeribitClientWarning,
    RequestError,
    ServiceUnavailable,
)

load_dotenv()

token_mock_response = {
    "access_token": "new_access_token",
    "expires_in": 3600,
    "refresh_token": "new_refresh_token",
}


@pytest.fixture
def auth_instance():
    """Fixture to create an Authentication instance with credentials loaded from environment variables."""
    client_id = os.environ.get("TEST_CLIENT_ID") or "dummy_id"
    client_secret = os.environ.get("TEST_CLIENT_SECRET") or "dummy_secret"
    return Authentication(env="test", client_id=client_id, client_secret=client_secret)


def test_credentials_set_correctly(auth_instance):
    """Test that client ID and client secret are set correctly from environment variables."""
    expected_id = os.environ.get("TEST_CLIENT_ID") or "dummy_id"
    expected_secret = os.environ.get("TEST_CLIENT_SECRET") or "dummy_secret"
    assert auth_instance.client_id == expected_id
    assert auth_instance.client_secret == expected_secret


def test_warning_raised_when_credentials_not_provided():
    """Test that a warning is raised when credentials are not provided."""
    with pytest.warns(DeribitClientWarning):
        Authentication(env="test")


@patch("deribit_wrapper.authentication.Authentication._request")
def test_authentication_process(mock_request, auth_instance):
    """Test the authentication process, assuming successful token retrieval."""
    # Mock the _request method to return a mock access token response
    mock_request.return_value = token_mock_response

    token = auth_instance.get_new_token()
    assert token == "new_access_token"
    mock_request.assert_called_once()


@patch(
    "deribit_wrapper.authentication.Authentication._request",
    side_effect=Exception(
        "Cannot generate new token without Client ID and Client Secret"
    ),
)
def test_authentication_failure_leads_to_exception(mock_request, auth_instance):
    """Test that an exception is raised when the authentication request fails."""
    with pytest.raises(Exception) as excinfo:
        auth_instance.get_new_token()
    assert "Cannot generate new token without Client ID and Client Secret" in str(
        excinfo.value
    )


def test_get_new_token_retrieves_new_token():
    mock_response = token_mock_response

    with (
        patch("deribit_wrapper.authentication.Authentication._request") as mock_request,
        patch(
            "deribit_wrapper.authentication.Authentication.create_new_scope",
            return_value="session:fixed_session_name",
        ) as mock_create_new_scope,
    ):
        mock_request.return_value = mock_response

        auth = Authentication(
            env="test", client_id="dummy_id", client_secret="dummy_secret"
        )
        new_token = auth.get_new_token()

        assert new_token == "new_access_token"
        mock_request.assert_called_once_with(
            "/public/auth",
            {
                "grant_type": "client_credentials",
                "client_id": "dummy_id",
                "client_secret": "dummy_secret",
                "scope": "session:fixed_session_name",
            },
        )
        mock_create_new_scope.assert_called()


def test_unauthorised_retries_token_acquisition(auth_instance):
    """Test that failed token acquisitions are retried before re-requesting."""
    with (
        patch.object(
            auth_instance,
            "get_new_token",
            side_effect=[KeyError("access_token"), KeyError("access_token"), None],
        ) as mock_token,
        patch.object(
            auth_instance, "_request", return_value={"ok": True}
        ) as mock_request,
    ):
        ret = auth_instance._handle_unauthorised(
            "/private/get_positions", {}, {"reason": "invalid_token"}, True
        )
    assert mock_token.call_count == 3
    mock_request.assert_called_once_with(
        "/private/get_positions", {}, give_results=True
    )
    assert ret == {"ok": True}


def test_unauthorised_gives_up_after_max_attempts(auth_instance):
    """Test that after three failed token acquisitions no request is re-sent."""
    with (
        patch.object(
            auth_instance, "get_new_token", side_effect=KeyError("access_token")
        ) as mock_token,
        patch.object(auth_instance, "_request") as mock_request,
    ):
        ret = auth_instance._handle_unauthorised(
            "/private/get_positions", {}, {"reason": "invalid_token"}, True
        )
    assert mock_token.call_count == 3
    mock_request.assert_not_called()
    assert ret == {}


def test_unauthorised_retries_on_request_error(auth_instance):
    """Test that RequestError during token acquisition is retried too."""
    with (
        patch.object(
            auth_instance,
            "get_new_token",
            side_effect=[RequestError("auth failed"), None],
        ) as mock_token,
        patch.object(
            auth_instance, "_request", return_value={"ok": True}
        ) as mock_request,
    ):
        ret = auth_instance._handle_unauthorised(
            "/private/get_positions", {}, {"reason": "invalid_token"}, True
        )
    assert mock_token.call_count == 2
    mock_request.assert_called_once_with(
        "/private/get_positions", {}, give_results=True
    )
    assert ret == {"ok": True}


def test_unauthorised_other_reason_does_not_retry(auth_instance):
    """Test that non-token reasons do not trigger token acquisition."""
    with patch.object(auth_instance, "get_new_token") as mock_token:
        ret = auth_instance._handle_unauthorised(
            "/private/get_positions", {}, {"reason": "scope_exceeded"}, True
        )
    mock_token.assert_not_called()
    assert ret == {}


@skipIf(
    not os.environ.get("TEST_CLIENT_ID") or not os.environ.get("TEST_CLIENT_SECRET"),
    "Integration tests require TEST_CLIENT_ID and TEST_CLIENT_SECRET env variables",
)
class TestDeribitIntegration(TestCase):
    def setUp(self):
        env = "test"
        client_id = os.environ.get("TEST_CLIENT_ID")
        client_secret = os.environ.get("TEST_CLIENT_SECRET")
        self.auth = Authentication(
            env=env, client_id=client_id, client_secret=client_secret
        )

    def test_get_new_token(self):
        token = self.auth.access_token
        self.assertIsNotNone(token)

    def test_get_time(self):
        time = self.auth.get_time()
        self.assertIsInstance(time, int)

    def test_get_api_version(self):
        version = self.auth.get_api_version()
        self.assertIsInstance(version, str)


def test_session_is_reused(auth_instance):
    """Test that the HTTP session is created once and reused across calls."""
    first = auth_instance._session
    second = auth_instance._session
    assert first is second


def test_session_is_per_instance():
    """Test that separate clients do not share an HTTP session."""
    a = Authentication(env="test", client_id="id_a", client_secret="secret_a")
    b = Authentication(env="test", client_id="id_b", client_secret="secret_b")
    assert a._session is not b._session


def test_close_releases_and_is_idempotent(auth_instance):
    """Test that close() shuts the session and is safe to call twice."""
    session = auth_instance._session
    auth_instance.close()
    assert auth_instance._http_session is None
    auth_instance.close()  # idempotent
    assert auth_instance._session is not session  # a new session is created lazily


def test_temporarily_unavailable_is_bounded(auth_instance, mocker):
    """Test that repeated 13028 responses give up instead of blocking forever."""
    mocker.patch("time.sleep")
    auth_instance.unavailable_max_attempts = 3
    auth_instance.unavailable_wait_seconds = 0
    with patch.object(
        auth_instance, "_request", return_value={"code": 13028}
    ) as mock_request:
        with pytest.raises(ServiceUnavailable, match="3 attempts"):
            auth_instance._handle_temporarily_unavailable("/private/x", {}, True)
    assert mock_request.call_count == 3


def test_temporarily_unavailable_returns_on_recovery(auth_instance, mocker):
    """Test that the first non-13028 response is returned."""
    mocker.patch("time.sleep")
    auth_instance.unavailable_wait_seconds = 0
    with patch.object(
        auth_instance, "_request", side_effect=[{"code": 13028}, {"ok": True}]
    ) as mock_request:
        ret = auth_instance._handle_temporarily_unavailable("/private/x", {}, True)
    assert ret == {"ok": True}
    assert mock_request.call_count == 2


def test_unavailable_defaults_are_bounded():
    """Test that the default retry budget cannot block for an hour."""
    auth = Authentication(env="test", client_id="id", client_secret="secret")
    worst_case = auth.unavailable_max_attempts * auth.unavailable_wait_seconds
    assert worst_case <= 600


@pytest.mark.parametrize("bad", [0, -1, 2.5, "3", None])
def test_retry_budget_rejects_bad_attempts(auth_instance, bad):
    """Test that a misconfigured attempt count raises a clear error."""
    auth_instance.unavailable_max_attempts = bad
    with pytest.raises(ValueError, match="unavailable_max_attempts"):
        auth_instance._retry_budget()


@pytest.mark.parametrize("bad", [-1, "60", None])
def test_retry_budget_rejects_bad_wait(auth_instance, bad):
    """Test that a misconfigured wait raises a clear error."""
    auth_instance.unavailable_wait_seconds = bad
    with pytest.raises(ValueError, match="unavailable_wait_seconds"):
        auth_instance._retry_budget()


def test_retry_budget_accepts_float_wait(auth_instance):
    """Test that a sub-second wait is allowed and formats without error."""
    auth_instance.unavailable_wait_seconds = 0.5
    assert auth_instance._retry_budget() == (
        auth_instance.unavailable_max_attempts,
        0.5,
    )
