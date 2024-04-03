import os

from dotenv import load_dotenv

load_dotenv()

client_id = os.environ.get("DERIBIT_CLIENT_ID")
client_secret = os.environ.get("DERIBIT_CLIENT_SECRET")
