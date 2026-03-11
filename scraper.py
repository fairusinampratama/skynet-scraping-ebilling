import requests
import re
import json
import logging
import config
import utils

logger = logging.getLogger(__name__)

class SkynetScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        # Suppress insecure request warnings if verify=False is used
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def login(self):
        """Authenticate with the server using requests."""
        logger.info("1. Logging in via requests...")
        payload = {
            "account": config.ACCOUNT,
            "username": config.USERNAME,
            "password": config.PASSWORD,
            "btnLogin": "Masuk",
            "titik_lokasi": ""
        }
        
        try:
            res = self.session.post(
                config.LOGIN_URL,
                data=payload,
                headers=config.HEADERS,
                verify=False,    # The legacy server has a self-signed cert
                allow_redirects=True
            )
            res.raise_for_status()
            
            # The server returns a 200 OK with a javascript redirect on success
            if "window.location = 'https://e.ebilling.id:2053/billing/'" in res.text or "Keluar" in res.text:
                logger.info("   [+] Login successful.")
                return True
            else:
                logger.error("   [!] Login failed. Check credentials.")
                logger.debug(f"Response HTML excerpt: {res.text[:500]}")
                # Save full html for debugging
                with open("login_failed.html", "w") as f:
                    f.write(res.text)
                return False
        except Exception as e:
            logger.error(f"   [!] Login request error: {e}")
            return False

    def fetch_dashboard_cabang(self):
        """Fetch Dashboard Cabang data."""
        logger.info("Fetching Dashboard Cabang...")
        try:
            res = self.session.get(config.URL_CABANG, verify=False)
            res.raise_for_status()
            html = res.text
            
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
                except Exception as e:
                    logger.debug(f"Row parse error (Cabang): {e}")

            logger.info(f"   [+] Parsed {len(data)} branch records.")
            return data
        except Exception as e:
            logger.error(f"   [!] Error fetching cabang: {e}")
            return []

    def fetch_data_ipl(self, year=None, month="Semua"):
        """Fetch Data IPL (Payment) data."""
        logger.info(f"Fetching Data IPL for Year: {year}, Month: {month}...")
        
        # We must use the Export URL because the UI table ignores the year parameter entirely
        # The IDs here appear static to the account (2867). If they change, this needs dynamic extraction.
        # It accepts tgl2=YYYY to filter by year.
        base_export_url = "https://e.ebilling.id/billing/admin/ipl/data_ipl.php?&data_account=2867&id_sales=787&id_lokasi=1226&data_level=Administrator&tgl1=03"
        url = f"{base_export_url}&tgl2={year}" if year else base_export_url
            
        try:
            res = self.session.get(url, verify=False)
            res.raise_for_status()
            html = res.text
            
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            data = []
            for row in rows:
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                # the export table has 23 columns. Skip headers or weird rows.
                if len(cols) < 22: continue

                try:
                    id_pel = utils.clean_html_text(cols[1])
                    if not id_pel or "ID Pelanggan" in id_pel or id_pel == "N/A": continue
                    
                    record = {
                        "id_pelanggan": id_pel,
                        "nama_pelanggan": utils.clean_html_text(cols[3]),
                        "alamat": utils.clean_html_text(cols[6]),
                        "nominal_harus_dibayar": utils.parse_price(utils.clean_html_text(cols[9])),
                        "nominal_pembayaran": utils.parse_price(utils.clean_html_text(cols[10])),
                        "status_pembayaran": utils.clean_html_text(cols[11]),
                        "bukti_pembayaran_url": "", # Export doesn't include images
                        "periode": utils.clean_html_text(cols[13]),
                        "metode": utils.clean_html_text(cols[14]),
                        "waktu_entry": utils.clean_html_text(cols[16]) if len(cols) > 16 else ""
                    }
                    data.append(record)
                except Exception as e:
                    pass
                
            logger.info(f"   [+] Parsed {len(data)} IPL records from Export.")
            return data
        except Exception as e:
            logger.error(f"   [!] Error fetching IPL Export: {e}")
            return []

    def fetch_data_warga(self):
        """Fetch Data Warga."""
        logger.info("Fetching Data Warga (Export)...")
        try:
            res = self.session.get(config.URL_WARGA_EXPORT, verify=False)
            res.raise_for_status()
            html = res.text
            
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            data = []
            for row in rows:
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cols) < 20: continue 

                try:
                    id_pel = utils.clean_html_text(cols[3])
                    if not id_pel or "ID Pelanggan" in id_pel: continue
                    
                    tanggal_registrasi = utils.clean_html_text(cols[4]) if len(cols) > 4 else ""
                    jatuh_tempo = utils.clean_html_text(cols[22]) if len(cols) > 22 else ""
                    
                    nik = utils.clean_html_text(cols[12]) if len(cols) > 12 else ""
                    kk = "" 
                    
                    pppoe_user = utils.clean_html_text(cols[25]) if len(cols) > 25 else ""
                    pppoe_pass = utils.clean_html_text(cols[26]) if len(cols) > 26 else ""
                    nama_lokasi = utils.clean_html_text(cols[27]) if len(cols) > 27 else ""
                    nama_router = utils.clean_html_text(cols[29]) if len(cols) > 29 else ""
                    koordinat = utils.clean_html_text(cols[35]) if len(cols) > 35 else ""
                    
                    ktp_url = ""
                    if len(cols) > 13:
                        raw_col_13 = cols[13]
                        src_match = re.search(r'src="([^"]+)"', raw_col_13)
                        if src_match:
                            ktp_url = src_match.group(1)
                        else:
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
                except Exception: 
                    pass
            
            logger.info(f"   [+] Parsed {len(data)} Warga records.")
            return data
        except Exception as e:
            logger.error(f"   [!] Error fetching Warga: {e}")
            return []

    def fetch_customer_status(self):
        """Fetch Customer Connection Status."""
        logger.info("Fetching Customer Status...")
        status_page_url = f"{config.DASHBOARD_URL}?page=data-status-langganan"
        
        try:
            res = self.session.get(status_page_url, verify=False)
            res.raise_for_status()
            match = re.search(r'getData_langganan\.php\?nilai=(\d+)', res.text)
            
            if not match:
                logger.warning("   [!] Could not find dynamic AJAX URL for status.")
                return {}
            
            account_id = match.group(1)
            json_url = f"{config.BASE_URL}/getData_langganan.php?nilai={account_id}"
            
            res_json = self.session.get(json_url, verify=False)
            res_json.raise_for_status()
            
            try:
                data = res_json.json()
                status_map = {}
                for row in data.get("data", []):
                    if len(row) > 14:
                        id_pel = row[2]
                        status_html = row[14]
                        
                        status_text = "Unknown"
                        if "On" in status_html:
                            status_text = "active"
                        elif "Off" in status_html or "Isolir" in status_html:
                            status_text = "isolated"
                        
                        status_map[id_pel] = status_text
                
                logger.info(f"   [+] Parsed status for {len(status_map)} customers.")
                return status_map
            except Exception as e:
                logger.error(f"   [!] Failed to parse Status JSON: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"   [!] Error fetching status: {e}")
            return {}
