import time

from deribit_wrapper.authentication import Authentication
from dev_scripts.config_dev import CLIENT_ID, CLIENT_SECRET, check_env

# This script is used to debug the authentication process.
# It requires the CLIENT_ID and CLIENT_SECRET to be set in the environment.

check_env()

authentication = Authentication(env='test', client_id=CLIENT_ID, client_secret=CLIENT_SECRET)


def debug_get_new_token():
    token_1 = authentication.get_new_token()
    print(f'First access token: {token_1}')
    token_2 = authentication.get_new_token()
    print(f'Access token using refresh token: {token_2}')
    token_3 = authentication.get_new_token(use_refresh_token_if_available=False)
    print(f'Access token using client id and secret: {token_3}')


def debug_token_that_expires():
    expires_in = 5
    token = authentication.get_new_token(use_refresh_token_if_available=False, expires_in=expires_in)
    print(f'Access token that expires in {expires_in} seconds: {token}')
    time.sleep(expires_in + 1)
    check = authentication.is_token_expired()
    assert check, 'Token should be expired.'
    print(f'Token expired correctly after {expires_in} seconds.')


def debug_get_time():
    ret = authentication.get_time()
    print(f'Time: {ret} | {time.strftime("%Y-%m-%d %H:%M:%S")}')


def debug_get_status():
    ret = authentication.get_status()
    print(f'Status: {ret}')
    locked_currencies = authentication.get_locked_currencies()
    print(f'Locked currencies: {locked_currencies}')
    locked_indices = authentication.get_locked_indices()
    print(f'Locked indices: {locked_indices}')


def debug_get_test():
    ret = authentication.test()
    print(f'Test: {ret}')
    api_version = authentication.get_api_version()
    print(f'API version: {api_version}')


def run():
    debug_get_new_token()
    debug_token_that_expires()
    debug_get_time()
    debug_get_status()
    debug_get_test()


if __name__ == "__main__":
    run()
