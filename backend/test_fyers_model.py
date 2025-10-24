import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    print("Loading .env file")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(".env file not found")

from fyers_auth import get_fyers_model

try:
    print("Attempting to initialize FyersModel...")
    fyers = get_fyers_model()
    print("FyersModel initialized successfully!")

    # Optional: Make a simple API call to verify
    profile = fyers.get_profile()
    if profile.get("s") == "ok":
        print("API call successful. Profile fetched.")
    else:
        print(f"API call failed: {profile}")

except Exception as e:
    print(f"An error occurred: {e}")
