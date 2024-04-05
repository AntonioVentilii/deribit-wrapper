import os

from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("TEST_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TEST_CLIENT_SECRET")


def check_env():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("CLIENT_ID and CLIENT_SECRET not set in the environment.")
