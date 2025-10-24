from fyers_apiv3 import fyersModel
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# Fyers API credentials from environment variables
APP_ID = os.environ.get("FYERS_APP_ID")
SECRET_KEY = os.environ.get("FYERS_SECRET_KEY")
REDIRECT_URI = os.environ.get("FYERS_REDIRECT_URI")

if not all([APP_ID, SECRET_KEY, REDIRECT_URI]):
    raise Exception("Please set the FYERS_APP_ID, FYERS_SECRET_KEY, and FYERS_REDIRECT_URI environment variables.")

def generate_auth_url():
    """
    Generates and prints the authentication URL.
    """
    session = fyersModel.SessionModel(
        client_id=APP_ID,
        secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI,
        response_type="code"
    )
    auth_url = session.generate_authcode()
    print(f"Please visit this URL to authorize the app: {auth_url}")

if __name__ == "__main__":
    generate_auth_url()
