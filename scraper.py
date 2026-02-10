import requests
import re
import json
import os
import subprocess
import config
import utils

class SkynetScraper:
    def __init__(self):
        self.session = requests.Session()

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

    def fetch_dashboard_cabang(self):
        """Fetch Dashboard Cabang data."""
        print("Fetching Dashboard Cabang...")
        cmd = ["curl", "-k", "-b", "cookies.txt", config.URL_CABANG]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            html = result.stdout
            
            # Parse Table #example1
            # Columns: 0:Aksi, 1:No, 2:Cabang, 3:Jml Plg, 4:Baru, 5:Free, 6:Lunas, 7:Belum, 8:Masuk, 9:Keluar, 10:Balance...
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            data = []
            for row in rows:
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cols) < 10: continue
                
                try:
                    cabang = utils.clean_html_text(cols[2])
                    if not cabang or "Nama Cabang" in cabang: continue
                    
                    record = {
                        "cabang": cabang,
                        "jumlah_pelanggan": utils.clean_html_text(cols[3]),
                        "pelanggan_baru": utils.clean_html_text(cols[4]),
                        "pelanggan_free": utils.clean_html_text(cols[5]),
                        "pelanggan_lunas": utils.clean_html_text(cols[6]),
                        "pelanggan_belum_lunas": utils.clean_html_text(cols[7]),
                        "total_pemasukan": utils.parse_price(utils.clean_html_text(cols[8])),
                        "total_pengeluaran": utils.parse_price(utils.clean_html_text(cols[9])),
                        "balance": utils.parse_price(utils.clean_html_text(cols[10])),
                        "total_estimasi": utils.parse_price(utils.clean_html_text(cols[14])) if len(cols) > 14 else 0
                    }
                    data.append(record)
                except: pass
            
            print(f"   [+] Parsed {len(data)} branch records.")
            return data
        except Exception as e:
            print(f"   [!] Error fetching cabang: {e}")
            return []

    def fetch_data_ipl(self, year=None, month="Semua"):
        """Fetch Data IPL (Payment) data.
        
        Args:
            year (str, optional): Year to filter (e.g., "2025"). Defaults to None (Current/Default View).
            month (str, optional): Month to filter (e.g., "01" or "Semua"). Defaults to "Semua".
        """
        print(f"Fetching Data IPL for Year: {year}, Month: {month}...")
        
        # Construct URL based on filter
        # Default: config.URL_IPL
        # Filtered: config.URL_IPL + "-&tahun={year}&bulan={month}"
        # Note: The dash '-' after data-ipl is crucial for the filter to work.
        url = config.URL_IPL
        if year:
            url = f"{config.URL_IPL}-&tahun={str(year)}&bulan={str(month)}"
            
        cmd = ["curl", "-k", "-b", "cookies.txt", url]
        try:
            # Increase buffer limit conceptually by just reading stdout found
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            html = result.stdout
            
            # Parse Table #example1
            # Columns: 3:ID Plg, 4:Nama, 5:Alamat, 6:Harus Bayar, 7:Bayar, 8:Status, 9:Bukti, 10:Periode, 11:Metode...
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            data = []
            for row in rows:
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cols) < 12: continue

                try:
                    id_pel = utils.clean_html_text(cols[3])
                    if not id_pel or "ID Pelanggan" in id_pel: continue
                    
                    # Extract Proof URL from Col 9 (Bukti)
                    proof_url = ""
                    if len(cols) > 9:
                        proof_match = re.search(r'src="([^"]+)"', cols[9])
                        if proof_match:
                            proof_url = proof_match.group(1)

                    record = {
                        "id_pelanggan": id_pel,
                        "nama_pelanggan": utils.clean_html_text(cols[4]),
                        "alamat": utils.clean_html_text(cols[5]),
                        "nominal_harus_dibayar": utils.parse_price(utils.clean_html_text(cols[6])),
                        "nominal_pembayaran": utils.parse_price(utils.clean_html_text(cols[7])),
                        "status_pembayaran": utils.clean_html_text(cols[8]),
                        "bukti_pembayaran_url": proof_url,
                        "periode": utils.clean_html_text(cols[10]),
                        "metode": utils.clean_html_text(cols[11]),
                        "waktu_entry": utils.clean_html_text(cols[13]) if len(cols) > 13 else ""
                    }
                    data.append(record)
                except: pass
                
            print(f"   [+] Parsed {len(data)} IPL records for {year}/{month}.")
            return data
        except Exception as e:
            print(f"   [!] Error fetching IPL: {e}")
            return []

    def fetch_all_historical_transactions(self):
        """Fetch all transaction data from 2021 to 2026."""
        all_transactions = []
        years = range(2021, 2027) # 2021 to 2026
        
        print("Starting Historical Transaction Scraping (2021-2026)...")
        
        for year in years:
            # Use "Semua" to fetch the whole year at once
            year_data = self.fetch_data_ipl(year=year, month="Semua")
            all_transactions.extend(year_data)
            
        print(f"Total Transactions Scraped: {len(all_transactions)}")
        return all_transactions

    def fetch_data_warga(self):
        """Fetch Data Warga via Export URL (HTML disguised as XLS)."""
        print("Fetching Data Warga (Export)...")
        # Download to file first due to size
        temp_file = "temp_warga.html"
        cmd = ["curl", "-k", "-b", "cookies.txt", "-o", temp_file, config.URL_WARGA_EXPORT]
        try:
            subprocess.run(cmd, check=True)
            
            with open(temp_file, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
            
            # Parse Table #example1
            # Columns (Adjusted based on inspection):
            # 3:ID Pel, 5:Nama, 9:Alamat, 10:Tlp, 15:Paket, 18:Harga, 26:Lokasi, 28:Router, 36:Koordinat
            # 37: MAC, 38: IP/Secret, 39: Password Secret, 40: Nama Lokasi, 41: Jenis Koneksi, 42: Nama Router
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            data = []
            for row in rows:
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cols) < 20: continue # Header or short row

                try:
                    id_pel = utils.clean_html_text(cols[3])
                    if not id_pel or "ID Pelanggan" in id_pel: continue
                    
                    # Corrected Indices based on Header Analysis:
                    # 4: Tanggal Registrasi, 22: Jatuh Tempo
                    # 25: IP/Secret, 26: Password Secret, 27: Nama Lokasi, 29: Nama Router, 35: Koordinat
                    
                    tanggal_registrasi = utils.clean_html_text(cols[4]) if len(cols) > 4 else ""
                    jatuh_tempo = utils.clean_html_text(cols[22]) if len(cols) > 22 else ""
                    
                    nik = utils.clean_html_text(cols[12]) if len(cols) > 12 else ""
                    kk = "" 
                    
                    pppoe_user = utils.clean_html_text(cols[25]) if len(cols) > 25 else ""
                    pppoe_pass = utils.clean_html_text(cols[26]) if len(cols) > 26 else ""
                    nama_lokasi = utils.clean_html_text(cols[27]) if len(cols) > 27 else ""
                    nama_router = utils.clean_html_text(cols[29]) if len(cols) > 29 else ""
                    koordinat = utils.clean_html_text(cols[35]) if len(cols) > 35 else ""
                    
                    # Index 13 contains the KTP Photo URL directly
                    ktp_url = ""
                    if len(cols) > 13:
                        raw_col_13 = cols[13]
                        src_match = re.search(r'src="([^"]+)"', raw_col_13)
                        if src_match:
                            ktp_url = src_match.group(1)
                        else:
                            # Fallback to text content (stripped)
                            ktp_url = utils.clean_html_text(raw_col_13)

                    record = {
                        "id_pelanggan": id_pel,
                        "nama_pelanggan": utils.clean_html_text(cols[5]),
                        "nik": nik,
                        "kk": kk,
                        "alamat": utils.clean_html_text(cols[9]),
                        "telepon": utils.clean_html_text(cols[10]),
                        "paket": utils.clean_html_text(cols[15]),
                        "harga": utils.parse_price(utils.clean_html_text(cols[18])),
                        "tanggal_registrasi": tanggal_registrasi,
                        "jatuh_tempo": jatuh_tempo,
                        "pppoe_username": pppoe_user,
                        "pppoe_password": pppoe_pass,
                        "nama_lokasi": nama_lokasi,
                        "nama_router": nama_router,
                        "koordinat": koordinat,
                        "ktp_photo_url": ktp_url
                    }
                    data.append(record)
                except: pass
            
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            print(f"   [+] Parsed {len(data)} Warga records (Extended).")
            return data
            
        except Exception as e:
            print(f"   [!] Error fetching Warga: {e}")
            return []

    def fetch_customer_status(self):
        """Fetch Customer Connection Status (Active/Isolated).
        
        This requires a two-step process:
        1. Fetch 'data-status-langganan' to find the dynamic AJAX URL (contains account ID).
        2. Fetch the JSON data from that AJAX URL.
        """
        print("Fetching Customer Status...")
        
        # Step 1: Get the dynamic ID
        status_page_url = f"{config.DASHBOARD_URL}?page=data-status-langganan"
        cmd = ["curl", "-k", "-b", "cookies.txt", status_page_url]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            html = result.stdout
            
            # Look for "getData_langganan.php?nilai=XXXX"
            match = re.search(r'getData_langganan\.php\?nilai=(\d+)', html)
            if not match:
                print("   [!] Could not find dynamic AJAX URL for status.")
                return {}
            
            account_id = match.group(1)
            print(f"   [+] Found Account ID for Status: {account_id}")
            
            # Step 2: Fetch JSON Data
            # Note: BASE_URL already includes /billing
            json_url = f"{config.BASE_URL}/getData_langganan.php?nilai={account_id}"
            cmd_json = ["curl", "-k", "-b", "cookies.txt", json_url]
            
            result_json = subprocess.run(cmd_json, capture_output=True, text=True, check=True)
            try:
                data = json.loads(result_json.stdout)
                
                # Parse JSON
                # Structure: {"data": [[col0, col1, ...], ...]}
                # Index 2: ID Pelanggan
                # Index 14: Status HTML (e.g., <i class="...">On </i> or <i ...>Off </i>)
                
                status_map = {}
                for row in data.get("data", []):
                    if len(row) > 14:
                        id_pel = row[2]
                        status_html = row[14]
                        
                        # Extract "On" or "Off" from HTML
                        # Example: <i  class="btn btn-success btn-sm" class="fas fa-lock">On  </i>
                        status_text = "Unknown"
                        if "On" in status_html:
                            status_text = "Active"
                        elif "Off" in status_html or "Isolir" in status_html:
                            status_text = "Isolated"
                        
                        status_map[id_pel] = status_text
                
                print(f"   [+] Parsed status for {len(status_map)} customers.")
                return status_map
                
            except json.JSONDecodeError:
                print("   [!] Failed to parse Status JSON.")
                return {}
                
        except Exception as e:
            print(f"   [!] Error fetching status: {e}")
            return {}
