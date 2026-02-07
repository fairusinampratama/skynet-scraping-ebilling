import os
from dotenv import load_dotenv

load_dotenv()

# Credentials & Endpoints
# Load from Environment Variables for safety
USERNAME = os.getenv("SKYNET_USER", "default_user") 
PASSWORD = os.getenv("SKYNET_PASS", "default_pass")
ACCOUNT = os.getenv("SKYNET_ACCT", "default_account")

BASE_URL = "https://e.ebilling.id:2053/billing"
LOGIN_URL = f"{BASE_URL}/login.php"
DASHBOARD_URL = f"{BASE_URL}/index.php"

# Page Endpoints
URL_LIST = f"{DASHBOARD_URL}?page=data-kartu-warga"   # Main List
URL_MAP = f"{DASHBOARD_URL}?page=data-map-pelanggan-" # Coordinates

# Image Server
IMG_BASE_URL = "https://e.ebilling.id:2096/img/ktp"

# Request Headers
# Request Headers
HEADERS = {
    "User-Agent": "curl/7.81.0",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded"
}
