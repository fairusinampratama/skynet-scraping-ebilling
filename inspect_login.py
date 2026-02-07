
import requests
import re

url = "https://e.ebilling.id:2053/billing/login.php"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

try:
    res = requests.get(url, headers=headers, verify=False)
    print(f"Status: {res.status_code}")
    
    # Print all input fields
    inputs = re.findall(r'<input[^>]*>', res.text)
    print("Form Inputs found:")
    for i in inputs:
        print(i)
        
    # Check for textareas or buttons too just in case
    buttons = re.findall(r'<button[^>]*>.*?</button>', res.text, re.DOTALL)
    print("Buttons found:")
    for b in buttons:
        print(b[:100]) # truncated

except Exception as e:
    print(f"Error: {e}")
