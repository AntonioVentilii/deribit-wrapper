import os

from dotenv import load_dotenv

load_dotenv()

client_id = os.environ.get("TEST_CLIENT_ID")
client_secret = os.environ.get("TEST_CLIENT_SECRET")
