import re
import urllib3

def setup_environment():
    """Disable secure warnings for valid usage."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_html_text(text):
    """Remove HTML tags and extra whitespace."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()

def parse_price(price_str):
    """Parse format like '150,000' to 150000."""
    if not price_str:
        return 0
    clean = re.sub(r'[^\d]', '', price_str)
    return int(clean) if clean else 0
