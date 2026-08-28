"""Account management: summaries, API keys, subaccounts, positions, and logs."""

from __future__ import absolute_import, annotations

import logging

import time
from datetime import datetime

from typing import Any

import pandas as pd

from .exceptions import (
    SubaccountNameAlreadyTaken,
    SubaccountNameWrongFormat,
    SubaccountError,
    WaitRequiredError,
    SubaccountNotRemovable,
    SubaccountAlreadyRemoved,
    InvalidMarginModelError,
    InvalidParameterForRequest,
)
from .market_data import MarketData
from .utilities import (
    DEFAULT_END,
    DEFAULT_START,
    MarginModelType,
    MarketOrderType,
    create_multilevel_df,
    from_dt_to_ts,
    seconds_to_hms,
)

logger = logging.getLogger(__name__)


class AccountManagement(MarketData):
    """Manage the Deribit account: summaries, API keys, subaccounts, and logs."""

    __GET_ACCOUNT_SUMMARY = "/private/get_account_summary"
    __LIST_API_KEYS = "/private/list_api_keys"
    __CREATE_API_KEY = "/private/create_api_key"
    __EDIT_API_KEY = "/private/edit_api_key"
    __ENABLE_API_KEY = "/private/enable_api_key"
    __DISABLE_API_KEY = "/private/disable_api_key"
    __REMOVE_API_KEY = "/private/remove_api_key"
    __CHANGE_API_KEY_NAME = "/private/change_api_key_name"
    __CHANGE_API_KEY_SCOPE = "/private/change_scope_in_api_key"
    __GET_SUBACCOUNTS = "/private/get_subaccounts"
    __CREATE_SUBACCOUNT = "/private/create_subaccount"
    __CHANGE_SUBACCOUNT_NAME = "/private/change_subaccount_name"
    __REMOVE_SUBACCOUNT = "/private/remove_subaccount"
    __CHANGE_MARGIN_MODEL = "/private/change_margin_model"
    __TOGGLE_PORTFOLIO_MARGIN = "/private/toggle_portfolio_margin"
    __GET_POSITIONS = "/private/get_positions"
    __GET_TRANSACTION_LOG = "/private/get_transaction_log"
    __GET_PORTFOLIO_MARGINS = "/private/get_portfolio_margins"

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        env: str = "prod",
        private_key: str | bytes | Any | None = None,
        auth_method: str = "credentials",
        private_key_password: str | bytes | None = None,
        progress_bar_desc: str = None,
    ):
        """Create an account management client."""
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            env=env,
            private_key=private_key,
            auth_method=auth_method,
            private_key_password=private_key_password,
            progress_bar_desc=progress_bar_desc,
        )

    def get_account_summary(
        self, currency: str | list[str] = None, subaccount_id: int = None
    ) -> pd.DataFrame:
        """Return the extended account summary per currency as a DataFrame."""
        uri = self.__GET_ACCOUNT_SUMMARY
        params = {"currency": "", "extended": True}
        if subaccount_id is not None:
            params["subaccount_id"] = subaccount_id
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        frames = []
        for c in currency:
            params["currency"] = c
            r = self._request(uri, params)
            frames.append(pd.DataFrame({k: [v] for k, v in r.items()}))
        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if "currency" in df.columns:
            cols = df.columns.tolist()
            cols = ["currency"] + [col for col in cols if col != "currency"]
            df = df[cols].copy()
        return df

    def get_margin_model(
        self, currency: str | list[str] = None, subaccount_id: int = None
    ) -> pd.DataFrame:
        """Return the margin model configuration per currency."""
        df = self.get_account_summary(currency=currency, subaccount_id=subaccount_id)
        df = df[
            [
                "currency",
                "margin_model",
                "portfolio_margining_enabled",
                "cross_collateral_enabled",
            ]
        ]
        return df

    def list_api_keys(self) -> pd.DataFrame:
        """Return all API keys of the account as a DataFrame."""
        uri = self.__LIST_API_KEYS
        r = self._request(uri, {})
        df = pd.DataFrame(r)
        return df

    def get_api_key(self, api_key_id: int | str) -> dict:
        """Return the API key with the given id; raises if no key matches."""
        keys = self.list_api_keys()
        records = keys.to_dict(orient="records") if not keys.empty else []
        # the API reports ids as integers, but accept the string form too
        matches = [r for r in records if str(r.get("id")) == str(api_key_id)]
        if not matches:
            raise ValueError(f"API key {api_key_id} not found.")
        return matches[0]

    def create_api_key(self, max_scope: str, name: str = None) -> dict:
        """Create an API key with the given maximum scope and optional name."""
        uri = self.__CREATE_API_KEY
        params = {"max_scope": max_scope}
        if name is not None:
            params["name"] = name
        r = self._request(uri, params)
        return r

    def edit_api_key(
        self, api_key_id: int | str, max_scope: str, name: str = None
    ) -> dict:
        """Edit an API key's maximum scope and optional name."""
        uri = self.__EDIT_API_KEY
        params = {"id": api_key_id, "max_scope": max_scope}
        if name is not None:
            params["name"] = name
        r = self._request(uri, params)
        return r

    def enable_api_key(self, api_key_id: int | str) -> dict:
        """Enable the API key with the given id."""
        uri = self.__ENABLE_API_KEY
        params = {"id": api_key_id}
        r = self._request(uri, params)
        return r

    def disable_api_key(self, api_key_id: int | str) -> dict:
        """Disable the API key with the given id."""
        uri = self.__DISABLE_API_KEY
        params = {"id": api_key_id}
        r = self._request(uri, params)
        return r

    def remove_api_key(self, api_key_id: int | str) -> dict:
        """Remove the API key with the given id."""
        uri = self.__REMOVE_API_KEY
        params = {"id": api_key_id}
        r = self._request(uri, params)
        return r

    def _get_subaccounts(self, with_portfolio: bool = False) -> list[dict]:
        uri = self.__GET_SUBACCOUNTS
        params = {"with_portfolio": with_portfolio}
        r = self._request(uri, params)
        return r

    def get_subaccounts(self) -> pd.DataFrame:
        """Return all subaccounts as a DataFrame."""
        r = self._get_subaccounts()
        df = pd.DataFrame(r)
        return df

    def get_subaccounts_with_portfolio(self) -> list[dict]:
        """Return all subaccounts including their portfolios."""
        r = self._get_subaccounts(with_portfolio=True)
        return r

    def get_subaccount(self, subaccount_id: int, with_portfolio: bool = False) -> dict:
        """Return the subaccount with the given id, raising if not found."""
        r = self._get_subaccounts(with_portfolio=with_portfolio)
        for subaccount in r:
            if subaccount["id"] == subaccount_id:
                return subaccount
        raise ValueError(f"Subaccount {subaccount_id} not found.")

    def create_subaccount(self) -> dict:
        """Create a new subaccount."""
        uri = self.__CREATE_SUBACCOUNT
        r = self._request(uri, {})
        return r

    def change_subaccount_name(self, subaccount_id: int, name: str) -> dict:
        """Rename a subaccount, mapping API errors to typed exceptions."""
        if len(name) > 32:
            raise ValueError(
                f"Subaccount name '{name}' is too long, maximum 32 characters."
            )
        uri = self.__CHANGE_SUBACCOUNT_NAME
        params = {"sid": subaccount_id, "name": name}
        r = self._request(uri, params)
        error_code = r.get("code")

        # Error code 12002: already taken
        if error_code == 12002:
            data = r.get("data")
            if data == "already_taken":
                raise SubaccountNameAlreadyTaken(
                    f"Subaccount name '{name}' is already taken."
                )
            if data == "wrong_format":
                raise SubaccountNameWrongFormat(
                    f"Subaccount name '{name}' has the wrong format."
                )
            raise SubaccountError(
                f"Error changing subaccount name to '{name}': {data}."
            )

        return r

    def remove_subaccount(
        self, subaccount_id: int, wait_if_over_limit: bool = False
    ) -> dict:
        """Remove a subaccount, optionally waiting out the rate limit."""
        uri = self.__REMOVE_SUBACCOUNT
        params = {"subaccount_id": subaccount_id}
        r = self._request(uri, params)
        error_code = r.get("code")
        error_data = r.get("data", {})

        # Error code 12006: remove subaccount over limit
        if error_code == 12006:
            wait = error_data.get("wait", 1)
            if wait_if_over_limit:
                logger.warning(
                    "Waiting %s before removing subaccount %s.",
                    seconds_to_hms(wait),
                    subaccount_id,
                )
                time.sleep(wait)
                r = self._request(uri, params)
            else:
                raise WaitRequiredError(
                    f"Wait {wait} seconds before removing subaccount {subaccount_id}."
                )

        # Error code 12007: subaccount not removable
        elif error_code == 12007:
            reason = error_data.get("reason")
            raise SubaccountNotRemovable(
                f"Subaccount {subaccount_id} is not removable: {reason}."
            )

        # Error code 13009: unauthorized
        elif error_code == 13009:
            reason = error_data.get("reason")
            if reason == "already_removed":
                raise SubaccountAlreadyRemoved(
                    f"Subaccount {subaccount_id} already removed."
                )
            raise SubaccountError(
                f"Unauthorized to remove subaccount {subaccount_id}: {reason}."
            )

        return r

    def _change_margin_model(
        self,
        margin_model: MarginModelType,
        subaccount_id: int = None,
        dry_run: bool = False,
    ) -> pd.DataFrame:
        uri = self.__CHANGE_MARGIN_MODEL
        params = {"margin_model": margin_model, "dry_run": dry_run}
        if subaccount_id is not None:
            params["subaccount_id"] = subaccount_id
        r = self._request(uri, params)
        if isinstance(r, dict):
            error_code = r.get("code")
            error_data = r.get("data", {})
        else:
            error_code = None
            error_data = {}

        # Error -32602: invalid params
        if error_code == -32602:
            param = error_data.get("param")
            reason = error_data.get("reason")
            if param == "margin_model":
                raise InvalidMarginModelError(
                    f"Invalid margin model {margin_model}: {reason}"
                )
            raise InvalidParameterForRequest(
                f"Invalid params for request {uri} with param {param}: {reason}"
            )

        df = create_multilevel_df(r)
        return df

    def change_margin_model(
        self, margin_model: MarginModelType, subaccount_id: int = None
    ) -> pd.DataFrame:
        """Change the margin model, optionally for one subaccount."""
        return self._change_margin_model(
            margin_model, subaccount_id=subaccount_id, dry_run=False
        )

    def check_if_margin_model_change_is_possible(
        self, margin_model: MarginModelType, subaccount_id: int = None
    ) -> bool:
        """Return True if a margin model change would keep margin rates below 1."""
        df = self._change_margin_model(
            margin_model, subaccount_id=subaccount_id, dry_run=True
        )
        df["check_initial_margin"] = df[("new_state", "initial_margin_rate")] < 1
        df["check_maintenance_margin"] = (
            df[("new_state", "maintenance_margin_rate")] < 1
        )
        check = df[["check_initial_margin", "check_maintenance_margin"]].all().all()
        return check

    def get_positions(
        self,
        currency: str | list[str] = None,
        kind: str = None,
        subaccount_id: int = None,
    ) -> pd.DataFrame:
        """Return open positions per currency as a DataFrame."""
        uri = self.__GET_POSITIONS
        params = {"currency": ""}
        if kind is not None:
            params["kind"] = kind
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        if subaccount_id is not None:
            params["subaccount_id"] = subaccount_id
        frames = []
        for c in currency:
            params["currency"] = c
            frames.append(pd.DataFrame(self._request(uri, params)))
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def get_transaction_log(
        self,
        start: str | datetime = None,
        end: str | datetime = None,
        currency: str | list[str] = None,
        query: str | list[str] = None,
    ) -> pd.DataFrame:
        """Return the paginated transaction log for a period as a DataFrame."""
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        uri = self.__GET_TRANSACTION_LOG
        params = {}
        if not isinstance(query, list):
            query = [query]
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        params["start_timestamp"] = from_dt_to_ts(pd.to_datetime(start, utc=True))
        params["end_timestamp"] = from_dt_to_ts(pd.to_datetime(end, utc=True))
        frames = []
        for q in query:
            if q is not None:
                params["query"] = q
            for c in currency:
                params["currency"] = c
                params.pop("continuation", None)
                continuation = True
                while continuation is not None:
                    ret = self._request(uri, params)
                    new_results = pd.DataFrame(ret["logs"])
                    frames.append(new_results.dropna(axis=1, how="all"))
                    continuation = ret["continuation"]
                    params["continuation"] = continuation
        results = pd.concat(frames) if frames else pd.DataFrame()
        if "profit_as_cashflow" in results.columns:
            results = results.astype({"profit_as_cashflow": bool})
        results.reset_index(drop=True, inplace=True)
        return results

    def get_delivery_log(
        self,
        start: str | datetime = None,
        end: str | datetime = None,
        currency: str | list[str] = None,
    ) -> pd.DataFrame:
        """Return delivery entries of the transaction log."""
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        return self.get_transaction_log(start, end, currency, query="delivery")

    def get_flow_history(
        self,
        start: str | datetime = None,
        end: str | datetime = None,
        currency: str | list[str] = None,
    ) -> pd.DataFrame:
        """Return deposit and transfer entries of the transaction log."""
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        return self.get_transaction_log(
            start, end, currency, query=["deposit", "transfer"]
        )

    def get_portfolio_margins(
        self, orders: list[MarketOrderType], add_positions: bool = True
    ) -> dict:
        """Return portfolio margins for simulated positions, grouped by currency."""
        uri = self.__GET_PORTFOLIO_MARGINS
        data = {}
        for instrument, amount in orders:
            currency = self.get_base_currency(instrument)
            if currency not in data:
                data[currency] = {}
            data[currency][instrument] = amount
        ret = {}
        for currency, simulated_positions in data.items():
            params = {
                "currency": currency,
                "simulated_positions": simulated_positions,
                "add_positions": add_positions,
            }
            r = self._request(uri, params)
            ret[currency] = r
        return ret
