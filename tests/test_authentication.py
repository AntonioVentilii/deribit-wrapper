import os
from unittest import TestCase
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

from deribit_wrapper.authentication import Authentication
from deribit_wrapper.exceptions import DeribitClientWarning

load_dotenv()

token_mock_response = {
    'access_token': 'new_access_token',
    'expires_in': 3600,
    'refresh_token': 'new_refresh_token',
}


@pytest.fixture
def auth_instance():
    """Fixture to create an Authentication instance with credentials loaded from environment variables."""
    client_id = os.environ.get("TEST_CLIENT_ID")
    client_secret = os.environ.get("TEST_CLIENT_SECRET")
    return Authentication(env='test', client_id=client_id, client_secret=client_secret)


def test_credentials_set_correctly(auth_instance):
    """Test that client ID and client secret are set correctly from environment variables."""
    assert auth_instance.client_id == os.environ.get("TEST_CLIENT_ID")
    assert auth_instance.client_secret == os.environ.get("TEST_CLIENT_SECRET")


def test_warning_raised_when_credentials_not_provided():
    """Test that a warning is raised when credentials are not provided."""
    with pytest.warns(DeribitClientWarning):
        Authentication(env='test')


@patch('deribit_wrapper.authentication.Authentication._request')
def test_authentication_process(mock_request, auth_instance):
    """Test the authentication process, assuming successful token retrieval."""
    # Mock the _request method to return a mock access token response
    mock_request.return_value = token_mock_response

    token = auth_instance.get_new_token()
    assert token == 'new_access_token'
    mock_request.assert_called_once()


@patch('deribit_wrapper.authentication.Authentication._request',
       side_effect=Exception("Cannot generate new token without Client ID and Client Secret"))
def test_authentication_failure_leads_to_exception(mock_request, auth_instance):
    """Test that an exception is raised when the authentication request fails."""
    with pytest.raises(Exception) as excinfo:
        auth_instance.get_new_token()
    assert "Cannot generate new token without Client ID and Client Secret" in str(excinfo.value)


def test_get_new_token_retrieves_new_token():
    mock_response = token_mock_response

    with patch('deribit_wrapper.authentication.Authentication._request') as mock_request, \
            patch('deribit_wrapper.authentication.Authentication.create_new_scope',
                  return_value='session:fixed_session_name') as mock_create_new_scope:
        mock_request.return_value = mock_response

        auth = Authentication(env='test', client_id='dummy_id', client_secret='dummy_secret')
        new_token = auth.get_new_token()

        assert new_token == 'new_access_token'
        mock_request.assert_called_once_with('/public/auth', {
            'grant_type': 'client_credentials',
            'client_id': 'dummy_id',
            'client_secret': 'dummy_secret',
            'scope': 'session:fixed_session_name',
        })
        mock_create_new_scope.assert_called()


class TestDeribitIntegration(TestCase):
    def setUp(self):
        env = 'test'
        client_id = os.environ.get('TEST_CLIENT_ID')
        client_secret = os.environ.get('TEST_CLIENT_SECRET')
        self.auth = Authentication(env=env, client_id=client_id, client_secret=client_secret)

    def test_get_new_token(self):
        token = self.auth.access_token
        self.assertIsNotNone(token)

    def test_get_time(self):
        time = self.auth.get_time()
        self.assertIsInstance(time, int)

    def test_get_api_version(self):
        version = self.auth.get_api_version()
        self.assertIsInstance(version, str)
