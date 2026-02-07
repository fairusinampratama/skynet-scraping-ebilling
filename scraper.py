import requests
import re
import json
import time
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import config
import utils

class SkynetScraper:
    def __init__(self):
        self.session = requests.Session()
        self.customers = [] # List of dicts
        self.id_map = {}    # Code -> Internal ID
        self.coord_map = {} # Name -> {lat, lng}

    def login(self):
        """Authenticate with the server using curl (subprocess)."""
        print("1. Logging in (via curl)...")
        # Clear old cookies
        if os.path.exists("cookies.txt"):
            os.remove("cookies.txt")
            
        cmd = [
            "curl", "-k", "-c", "cookies.txt", "-v",
            "-d", f"account={config.ACCOUNT}&username={config.USERNAME}&password={config.PASSWORD}&btnLogin=Masuk&titik_lokasi=",
            config.LOGIN_URL
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists("cookies.txt"):
                print("   [+] Login command executed. Cookies saved.")
            else:
                print("   [!] Login failed: No cookies file created.")
        except Exception as e:
            print(f"   [!] Login Execution Error: {e}")

    def fetch_master_data(self):
        """Fetch customer list using curl and parse content."""
        print("2. Fetching Master Customer List (via curl)...")
        
        cmd = [
            "curl", "-k", "-b", "cookies.txt", 
            config.URL_LIST
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            html = result.stdout
            
            # Parse Rows
            # Regex might need adjustment if HTML structure changed slightly, but keeping original logic
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            print(f"   [+] Found {len(rows)} potential records (including headers).")
    
            valid_count = 0
            
            for row in rows:
                # Columns
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cols) < 10: 
                    continue
    
                try:
                    # 1. Parse Basic Data
                    code = utils.clean_html_text(cols[1])
                    name = utils.clean_html_text(cols[2])
                    
                    if not code or "ID Pelanggan" in code: continue # Skip header
    
                    # 2. Extract Internal ID (Hidden in Row)
                    # Look for `id_warga=1234`
                    internal_id = ""
                    id_match = re.search(r'id_warga=(\d+)', row)
                    if id_match:
                        internal_id = id_match.group(1)
                        self.id_map[code] = internal_id
    
                    # 3. Parse Details
                    address = utils.clean_html_text(cols[3])
                    phone = utils.clean_html_text(cols[4])
                    nik = utils.clean_html_text(cols[5])
                    package = utils.clean_html_text(cols[6])
                    bandwidth = utils.clean_html_text(cols[7])
                    price = utils.parse_price(utils.clean_html_text(cols[8]))
                    
                    # Notes often contain Username: " , , USERNAME"
                    notes = utils.clean_html_text(cols[9])
                    pppoe_user = ""
                    parts = [p.strip() for p in notes.split(',')]
                    if len(parts) > 2:
                        pppoe_user = parts[2]
                    elif len(parts) > 0 and parts[0]:
                        pppoe_user = parts[0] # Fallback
    
                    join_date = utils.clean_html_text(cols[10])
    
                    # Build Object
                    cust = {
                        "code": code,
                        "internal_id": internal_id,
                        "name": name,
                        "address": address,
                        "phone": phone,
                        "nik": nik,
                        "package": package,
                        "bandwidth": bandwidth,
                        "price": price,
                        "connection_type": "PPPOE", # Assumed
                        "pppoe_username": pppoe_user,
                        "join_date": join_date,
                        "status": "Active",
                        "latitude": None,
                        "longitude": None,
                        "ktp_photo_url": ""
                    }
                    
                    self.customers.append(cust)
                    valid_count += 1
    
                except Exception as e:
                    pass # Skip malformed rows safely
    
            print(f"   [+] Successfully parsed {len(self.customers)} customers.")
            
        except Exception as e:
            print(f"   [!] Fetch Error: {e}")

    def fetch_coordinates(self):
        """Fetch map page and extract JavaScript location data using curl."""
        print("3. Fetching Map Coordinates (via curl)...")
        
        cmd = [
            "curl", "-k", "-b", "cookies.txt", 
            config.URL_MAP
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            html = result.stdout
            
            # Regex to find `addMarkerAndInfoWindow` calls
            # Matches: var locationData = "LAT,LNG"; ... Name ...
            pattern = r'var locationData = "([^"]+)";.*?addMarkerAndInfoWindow.*?<td>Nama Pelanggan</td><td><b>" \+ "([^"]+)" \+ "</b>'
            matches = re.findall(pattern, html, re.DOTALL)
            
            print(f"   [+] Found {len(matches)} coordinate pairs in map script.")
            
            for latlng, raw_name in matches:
                try:
                    lat, lng = latlng.split(',')
                    clean_name = raw_name.strip()
                    self.coord_map[clean_name] = {
                        "lat": float(lat), 
                        "lng": float(lng)
                    }
                except:
                    continue
        except Exception as e:
             print(f"   [!] Map Fetch Error: {e}")
                
    def enrich_data(self):
        """Merge ID maps, Coordinates, and Generate Photo URLs."""
        print("4. Enriching Data (Merging Coordinates & Generating URLs)...")
        
        for cust in self.customers:
            name = cust['name']
            
            # 1. Merge Coordinates
            if name in self.coord_map:
                cust['latitude'] = self.coord_map[name]['lat']
                cust['longitude'] = self.coord_map[name]['lng']
            
            # 2. Generate Photo URL
            # Pattern: /img/ktp/{ACCOUNT}{INTERNAL_ID}.jpg
            iid = cust.get('internal_id')
            if iid:
                cust['ktp_photo_url'] = f"{config.IMG_BASE_URL}/{config.ACCOUNT}{iid}.jpg"

    def validate_photos(self):
        """Check Photo URLs in parallel and remove 404s."""
        print("5. Validating Photo URLs (Removing 404s)...")
        
        def check_url(cust):
            url = cust.get('ktp_photo_url')
            if not url: return cust
            
            try:
                # Check JPG
                res = requests.head(url, verify=False, timeout=5)
                if res.status_code == 200:
                    return cust
                
                # Check PNG
                url_png = url.replace(".jpg", ".png")
                res = requests.head(url_png, verify=False, timeout=5)
                if res.status_code == 200:
                    cust['ktp_photo_url'] = url_png
                    return cust
            except:
                pass
            
            # If failed
            cust['ktp_photo_url'] = "" 
            return cust

        # Parallel Execution
        with ThreadPoolExecutor(max_workers=50) as executor:
            self.customers = list(executor.map(check_url, self.customers))
            
        # Count stats
        valid = sum(1 for c in self.customers if c['ktp_photo_url'])
        print(f"   [+] Photo Validation Complete: {valid} valid images found.")

    def save_results(self, filename="full_customer_data.json"):
        with open(filename, "w") as f:
            json.dump(self.customers, f, indent=4)
        print(f"6. Data Saved to {filename}")
