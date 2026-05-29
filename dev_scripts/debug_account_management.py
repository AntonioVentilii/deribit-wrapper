import json
import re
import time

from deribit_wrapper.account_management import AccountManagement
from deribit_wrapper.utilities import MarginModelType
from dev_scripts.config_dev import CLIENT_ID, CLIENT_SECRET, check_env

# This script is used to debug the account management process.
# It requires the CLIENT_ID and CLIENT_SECRET to be set in the environment.

check_env()

account_management = AccountManagement(
    env="test", client_id=CLIENT_ID, client_secret=CLIENT_SECRET
)


def compare_scopes(scope1: str, scope2: str, desc: str):
    pattern = r"(^|\s)(session:[^ ]*|[^ ]+:none)"
    scope1 = re.sub(pattern, "", scope1).strip()
    scope2 = re.sub(pattern, "", scope2).strip()
    segments1 = scope1.split()
    segments2 = scope2.split()
    segments1.sort()
    segments2.sort()
    s1 = " ".join(segments1)
    s2 = " ".join(segments2)
    assert s1 == s2, f"{desc.capitalize()} scope: {scope1} != {scope2}"


def debug_get_account_summary():
    summary = account_management.get_account_summary()
    print(f"Account summary:\n{summary.to_string()}")
    margin_model = account_management.get_margin_model()
    print(f"Margin model:\n{margin_model.to_string()}")


def debug_api_keys():
    api_keys = account_management.list_api_keys()
    print("API keys retrieved successfully.")
    for key_id in api_keys["id"]:
        key = account_management.get_api_key(key_id)
        print("API key retrieved successfully.")
    scope = account_management.create_new_scope(
        account="read", trade="none", wallet="read"
    )
    name = "test_key"
    new_key = account_management.create_api_key(max_scope=scope, name=name)
    new_key_scope = new_key["max_scope"]
    compare_scopes(scope, new_key_scope, "API Key")
    new_key_name = new_key["name"]
    assert new_key_name == name, "New key name mismatch"
    new_key_id = new_key["id"]
    print("New key created successfully.")
    new_scope = account_management.create_new_scope(
        account="read", trade="read", wallet="read"
    )
    new_name = "test_key_2"
    account_management.edit_api_key(new_key_id, max_scope=new_scope, name=new_name)
    edited_key = account_management.get_api_key(new_key_id)
    edited_key_scope = edited_key["max_scope"]
    compare_scopes(new_scope, edited_key_scope, "Edited API Key")
    edited_key_name = edited_key["name"]
    assert edited_key_name == new_name, "Edited key name mismatch"
    print("Edited key saved successfully.")
    account_management.disable_api_key(new_key_id)
    disabled_key = account_management.get_api_key(new_key_id)
    disabled_key_state = disabled_key["enabled"]
    assert not disabled_key_state, "Disabled key state mismatch"
    print("Disabled API key successfully.")
    account_management.enable_api_key(new_key_id)
    enabled_key = account_management.get_api_key(new_key_id)
    enabled_key_state = enabled_key["enabled"]
    assert enabled_key_state, "Enabled key state mismatch"
    print("Enabled API key successfully.")
    account_management.remove_api_key(new_key_id)
    new_api_keys = account_management.list_api_keys()
    assert (
        new_key_id not in new_api_keys["id"]
    ), "New key id still in active API keys list"
    print("API key removed successfully.")


def debug_subaccounts():
    subaccounts = account_management.get_subaccounts()
    print("Subaccounts retrieved successfully.")
    new_subaccount = account_management.create_subaccount()
    print("New subaccount created successfully.")
    new_subaccount_id = new_subaccount["id"]
    new_name = f"test_subaccount_{int(time.time())}"
    account_management.change_subaccount_name(new_subaccount_id, new_name)
    edited_subaccount = account_management.get_subaccount(new_subaccount_id)
    edited_subaccount_name = edited_subaccount["username"]
    assert edited_subaccount_name == new_name, "Edited subaccount name mismatch"
    print("Edited subaccount name successfully.")
    account_management.remove_subaccount(new_subaccount_id, wait_if_over_limit=True)
    try:
        account_management.get_subaccount(new_subaccount_id)
    except Exception as e:
        assert "Subaccount" in str(e), "Expected subaccount not found error"
    print("Subaccount removed successfully.")


def debug_margin_model():
    margin_models = account_management.get_margin_model()
    print(f"Margin model:\n{margin_models.to_string()}")
    current_margin_model: MarginModelType = margin_models["margin_model"][0]
    new_margin_model: MarginModelType = "segregated_sm"
    account_management.change_margin_model(new_margin_model)
    edited_margin_models = account_management.get_margin_model()
    assert (
        edited_margin_models["margin_model"] == new_margin_model
    ).all(), f"Margin model not changed to {new_margin_model}."
    print(
        f"Margin model changed to {new_margin_model} successfully. Reverting to {current_margin_model}."
    )
    account_management.change_margin_model(current_margin_model)
    change_is_possible = account_management.check_if_margin_model_change_is_possible(
        "cross_pm"
    )
    print(f'Change to cross_pm is {"" if change_is_possible else "not "}possible.')


def run():
    debug_get_account_summary()
    debug_api_keys()
    debug_subaccounts()
    debug_margin_model()


if __name__ == "__main__":
    run()
