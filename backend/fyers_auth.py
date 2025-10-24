from fyers_apiv3 import fyersModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file before importing other modules
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# Fyers API credentials from environment variables
APP_ID = os.environ.get("FYERS_APP_ID")
SECRET_KEY = os.environ.get("FYERS_SECRET_KEY")

if not all([APP_ID, SECRET_KEY]):
    raise Exception("Please set the FYERS_APP_ID and FYERS_SECRET_KEY environment variables.")

TOKEN_FILE = "backend/fyers_token.txt"

def get_fyers_model():
    """
    Initializes and returns a fyers_model object.
    """
    if not os.path.exists(TOKEN_FILE):
        raise Exception("Fyers token file not found. Please generate the token first.")

    with open(TOKEN_FILE, "r") as f:
        access_token = f.read().strip()

    return fyersModel.FyersModel(
        client_id=APP_ID,
        token=access_token,
        log_path=os.path.join(os.path.dirname(__file__), "logs")
    )
