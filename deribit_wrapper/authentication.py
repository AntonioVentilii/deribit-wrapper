from __future__ import absolute_import, annotations

import json
import time
import uuid
import warnings
from typing import Any, overload

from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import DeribitBase
from .exceptions import DeribitClientWarning, ServiceUnavailable, RequestError
from .utilities import ParamsType, ScopeType, seconds_to_hms


class Authentication(DeribitBase):
    __AUTH = "/public/auth"

    __GET_TIME = "/public/get_time"
    __STATUS = "/public/status"
    __TEST = "/public/test"

    def __init__(
        self,
        env: str = "prod",
        client_id: str = None,
        client_secret: str = None,
        private_key: str | bytes | Any | None = None,
        auth_method: str = "credentials",
    ):
        super().__init__(env=env)
        self._client_id = None
        self._client_secret = None
        self._private_key = None
        self._auth_method = auth_method
        self.set_credentials(
            client_id, client_secret, private_key=private_key, auth_method=auth_method
        )
        self._access_token = None
        self._token_expiry = None
        self._refresh_token = None

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def client_secret(self) -> str:
        return self._client_secret

    @property
    def private_key(self) -> str | bytes | Any | None:
        return self._private_key

    @property
    def auth_method(self) -> str:
        return self._auth_method

    def set_credentials(
        self,
        client_id: str,
        client_secret: str = None,
        private_key: str | bytes | Any | None = None,
        auth_method: str = None,
    ):
        if auth_method is not None:
            self._auth_method = auth_method

        if private_key is not None:
            self._private_key = private_key
            if self._auth_method == "credentials":
                self._auth_method = "asymmetric"

        self._client_id = client_id
        self._client_secret = client_secret

        if self._auth_method == "asymmetric":
            if not client_id or not self._private_key:
                txt = "Client ID or Private Key not provided. Only 'public' requests will be available."
                warnings.warn(txt, DeribitClientWarning)
        else:
            if not client_id or not client_secret:
                txt = "Client ID or Client Secret not provided. Only 'public' requests will be available."
                warnings.warn(txt, DeribitClientWarning)

    @property
    def _session(self) -> Session:
        session = Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @overload
    def _request(
        self, uri: str, params: ParamsType, give_results: bool = True
    ) -> dict | list[dict]: ...

    @overload
    def _request(
        self, uri: str, params: ParamsType, give_results: False
    ) -> Response: ...

    def _request(
        self, uri: str, params: ParamsType, give_results: bool = True
    ) -> dict | list[dict] | Response:
        data = {"jsonrpc": "2.0", "id": 1, "method": uri, "params": params}
        headers = None
        if uri.startswith("/private"):
            token = self.access_token
            headers = {"Authorization": "bearer " + token}
        r = self._session.post(url=self.api_url, data=json.dumps(data), headers=headers)

        if give_results:
            ret = r.json()
            if "result" in ret:
                ret = ret["result"]
            elif "error" in ret:
                ret = ret["error"]
                error_code = ret.get("code")
                error_data = ret.get("data", {})
                return self._handle_error(
                    uri, params, error_code, error_data, give_results=give_results
                )
            else:
                raise RequestError(ret)

            if not isinstance(ret, dict) and not isinstance(ret, list):
                ret = {"result": ret}

        else:
            ret = r

        return ret

    def _handle_error(
        self,
        uri: str,
        params: ParamsType,
        error_code: int,
        error_data: dict,
        give_results: bool,
    ) -> dict:
        if error_code == 10028:
            return self._handle_too_many_requests(
                uri, params, error_data, give_results=give_results
            )
        if error_code == 13009:
            return self._handle_unauthorised(
                uri, params, error_data, give_results=give_results
            )
        if error_code == 13028:
            return self._handle_temporarily_unavailable(
                uri, params, give_results=give_results
            )
        if error_code == 10041:
            return self._handle_settlement_in_progress(
                uri, params, give_results=give_results
            )
        if error_code == -32602:
            self._handle_invalid_params(uri, error_data)
        else:
            print(f"Error code {error_code} for request {uri}.")
        return {}

    def _handle_too_many_requests(
        self, uri: str, params: ParamsType, error_data: dict, give_results: bool
    ) -> dict:
        wait = error_data.get("wait", 1)
        print(f"Too many requests for URI {uri}. Waiting {seconds_to_hms(wait)}...")
        for i in range(wait):
            time.sleep(1)
            print(f"Wait {seconds_to_hms(wait - i)}...", end="\r", flush=True)
        print()
        return self._request(uri, params, give_results=give_results)

    def _handle_unauthorised(
        self, uri: str, params: ParamsType, error_data: dict, give_results: bool
    ) -> dict:
        reason = error_data.get("reason")
        if reason == "invalid_token":
            max_attempts = 3
            for i in range(max_attempts):
                print(
                    f"Invalid token. Trying to get a new one. Attempt {i + 1} of {max_attempts}..."
                )
                self.get_new_token()
                return self._request(uri, params, give_results=give_results)
        return {}

    def _handle_temporarily_unavailable(
        self, uri: str, params: ParamsType, give_results: bool
    ) -> dict:
        max_attempts = 60
        for i in range(max_attempts):
            print(
                f"Temporarily unavailable. Waiting 1 minute [{i + 1}/{max_attempts}]..."
            )
            time.sleep(60)
            ret = self._request(uri, params, give_results=give_results)
            if ret.get("code") != 13028:
                return ret
        raise ServiceUnavailable("Service temporarily unavailable.")

    def _handle_settlement_in_progress(
        self, uri: str, params: ParamsType, give_results: bool
    ) -> dict:
        max_attempts = 60
        for i in range(max_attempts):
            print(
                f"Settlement in progress. Waiting 1 second [{i + 1}/{max_attempts}]..."
            )
            time.sleep(1)
            ret = self._request(uri, params, give_results=give_results)
            if isinstance(ret, dict) and ret.get("code") != 10041:
                return ret
            if not isinstance(ret, dict):
                return ret
        return {}

    def _handle_invalid_params(self, uri: str, error_data: dict):
        param = error_data.get("param")
        reason = error_data.get("reason")
        print(f"Invalid params for request {uri}: param={param}, reason={reason}")

    @property
    def access_token(self) -> str:
        self.refresh_token_if_expired()
        return self._access_token

    def is_token_expired(self) -> bool:
        if self._token_expiry is None or self._access_token is None:
            return True
        current_time = int(time.time())
        buffer = 60
        return current_time >= self._token_expiry - buffer

    def refresh_token_if_expired(self):
        if self.is_token_expired():
            self.get_new_token()

    def create_new_scope(
        self,
        session_name: str = None,
        account: ScopeType = None,
        trade: ScopeType = None,
        wallet: ScopeType = None,
        block_trade: ScopeType = None,
        expires_in: int = 0,
        ip: str = "",
    ) -> str:
        scope_parts = []

        if session_name is None:
            unique_part = uuid.uuid4()
            timestamp = int(time.time())
            session_name = f"{self.instance_name}_{timestamp}_{unique_part.hex}"
        scope_parts.append(f"session:{session_name}")

        if account:
            scope_parts.append(f"account:{account}")

        if trade:
            scope_parts.append(f"trade:{trade}")

        if wallet:
            scope_parts.append(f"wallet:{wallet}")

        if block_trade:
            scope_parts.append(f"block_trade:{block_trade}")

        if expires_in > 0:
            scope_parts.append(f"expires:{expires_in}")

        if ip:
            scope_parts.append(f"ip:{ip}")

        final_scope = " ".join(scope_parts)
        return final_scope

    def _generate_signature(self, timestamp: int, nonce: str, data: str = "") -> str:
        # pylint: disable=too-many-locals,too-many-branches,import-outside-toplevel,broad-exception-caught,no-else-return
        """
        Generates the cryptographic signature for client_signature authentication.
        Message to sign format: timestamp + "\n" + nonce + "\n" + data
        """
        message_str = f"{timestamp}\n{nonce}\n{data}"
        message_bytes = message_str.encode("utf-8")

        if self._auth_method == "signature":
            import hmac
            import hashlib

            if not self.client_secret:
                raise ValueError("Cannot generate signature without Client Secret")
            sig = hmac.new(
                self.client_secret.encode("utf-8"), message_bytes, hashlib.sha256
            ).hexdigest()
            return sig

        elif self._auth_method == "asymmetric":
            if not self._private_key:
                raise ValueError(
                    "Cannot generate asymmetric signature without Private Key"
                )
            from cryptography.hazmat.primitives.asymmetric import (
                ed25519,
                rsa,
                padding,
                ec,
            )
            from cryptography.hazmat.primitives.serialization import (
                load_pem_private_key,
            )
            from cryptography.hazmat.primitives import hashes

            pkey = self._private_key
            if isinstance(pkey, (str, bytes)):
                if isinstance(pkey, str) and len(pkey) < 1024 and "\n" not in pkey:
                    import os

                    if os.path.exists(pkey):
                        with open(pkey, "rb") as f:
                            pkey_bytes = f.read()
                    else:
                        pkey_bytes = pkey.encode("utf-8")
                else:
                    pkey_bytes = (
                        pkey if isinstance(pkey, bytes) else pkey.encode("utf-8")
                    )

                pkey = load_pem_private_key(pkey_bytes, password=None)

            if isinstance(pkey, ed25519.Ed25519PrivateKey):
                sig_bytes = pkey.sign(message_bytes)
                return sig_bytes.hex()
            elif isinstance(pkey, rsa.RSAPrivateKey):
                sig_bytes = pkey.sign(
                    message_bytes, padding.PKCS1v15(), hashes.SHA256()
                )
                return sig_bytes.hex()
            else:
                try:
                    sig_bytes = pkey.sign(message_bytes, ec.ECDSA(hashes.SHA256()))
                    return sig_bytes.hex()
                except Exception:
                    sig_bytes = pkey.sign(message_bytes)
                    return sig_bytes.hex()
        else:
            raise ValueError(
                f"Signature generation not supported for auth_method '{self._auth_method}'"
            )

    def get_new_token(
        self, use_refresh_token_if_available: bool = True, expires_in: int = 0
    ) -> str:
        if self._auth_method == "asymmetric":
            if not self.client_id or not self._private_key:
                raise ValueError(
                    "Cannot generate new token without Client ID and Private Key"
                )
        else:
            if not self.client_id or not self.client_secret:
                raise ValueError(
                    "Cannot generate new token without Client ID and Client Secret"
                )
        uri = self.__AUTH
        scope = self.create_new_scope(expires_in=expires_in)
        if use_refresh_token_if_available and self._refresh_token:
            params = {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "scope": scope,
            }
        else:
            if self._auth_method in ("signature", "asymmetric"):
                timestamp = int(time.time() * 1000)
                nonce = uuid.uuid4().hex
                data = ""
                signature = self._generate_signature(timestamp, nonce, data)
                params = {
                    "grant_type": "client_signature",
                    "client_id": self.client_id,
                    "timestamp": timestamp,
                    "nonce": nonce,
                    "signature": signature,
                    "data": data,
                    "scope": scope,
                }
            else:
                params = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": scope,
                }
        r = self._request(uri, params)
        self._access_token = r["access_token"]
        self._token_expiry = int(time.time()) + r["expires_in"]
        self._refresh_token = r["refresh_token"]
        return self._access_token

    def get_time(self) -> int:
        uri = self.__GET_TIME
        r = self._request(uri, {})
        return r["result"]

    def get_status(self) -> dict:
        uri = self.__STATUS
        r = self._request(uri, {})
        return r

    def get_locked_currencies(self) -> list[str]:
        return self.get_status().get("locked_currencies", [])

    def get_locked_indices(self) -> list[str]:
        return self.get_status().get("locked_indices", [])

    def test(self) -> dict:
        uri = self.__TEST
        r = self._request(uri, {})
        return r

    def get_api_version(self) -> str:
        return self.test()["version"]
