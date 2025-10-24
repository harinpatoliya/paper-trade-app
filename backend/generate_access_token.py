from fyers_apiv3 import fyersModel
import sys
import json
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

TOKEN_FILE = "backend/fyers_token.txt"

def generate_access_token(auth_code):
    """
    Generates the access token using the provided auth code.
    """
    session = fyersModel.SessionModel(
        client_id=APP_ID,
        secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )
    session.set_token(auth_code)
    response = session.generate_token()

    if "access_token" in response:
        with open(TOKEN_FILE, "w") as f:
            f.write(response["access_token"])
        print("Access token generated and saved to fyers_token.txt")
    else:
        print("Error generating access token:")
        print(response)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_access_token.py <auth_code>")
    else:
        generate_access_token(sys.argv[1])
