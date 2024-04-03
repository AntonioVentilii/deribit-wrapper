import pytest

from deribit_wrapper.base import DeribitBase


def test_instance_creation_with_default_env():
    """Test instance creation with default environment."""
    instance = DeribitBase()
    assert instance.env == 'prod'
    assert instance.api_url == 'https://www.deribit.com/api/v2'


def test_instance_creation_with_test_env():
    """Test instance creation with specified 'test' environment."""
    instance = DeribitBase(env='test')
    assert instance.env == 'test'
    assert instance.api_url == 'https://test.deribit.com/api/v2'


def test_invalid_environment_creation():
    """Test instance creation with an invalid environment."""
    with pytest.raises(ValueError) as excinfo:
        DeribitBase(env='invalid_env')
    assert "Environment 'invalid_env' not supported." in str(excinfo.value)


def test_env_property_setter(mocker):
    """Test the env property setter with a mocked logger and sleep."""
    mocker.patch('time.sleep', return_value=None)  # Mock sleep to avoid delay.
    mocker.patch('logging.warning')  # Mock logging to avoid actual log output.

    instance = DeribitBase(env='test')
    instance.env = 'prod'  # Change environment to prod.

    assert instance.env == 'prod'


def test_api_url_property():
    """Test that the api_url property constructs URLs correctly."""
    instance_test = DeribitBase(env='test')
    instance_prod = DeribitBase(env='prod')
    assert instance_test.api_url == 'https://test.deribit.com/api/v2'
    assert instance_prod.api_url == 'https://www.deribit.com/api/v2'
