import requests
import re
import json
import logging
import config
import utils

logger = logging.getLogger(__name__)

def _normalize_header(text):
    return re.sub(r'\s+', ' ', utils.clean_html_text(text)).strip().lower()

def _extract_cells(row, tag):
    return re.findall(rf'<{tag}[^>]*>(.*?)</{tag}>', row, re.DOTALL)

def _build_header_index(rows):
    for row in rows:
        headers = _extract_cells(row, "th")
        if headers:
            return {_normalize_header(header): idx for idx, header in enumerate(headers)}
    return {}

def _column(cols, header_index, header, fallback_idx=None):
    idx = header_index.get(_normalize_header(header))
    if idx is None:
        idx = fallback_idx
    if idx is None or idx >= len(cols):
        return ""
    return utils.clean_html_text(cols[idx])

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
        """Fetch Data IPL (Payment) data over all 12 months using tgl1 padding."""
        logger.info(f"Fetching Data IPL for Year: {year}, Month: {month}...")
        
        base_export_url = "https://e.ebilling.id/billing/admin/ipl/data_ipl.php?&data_account=2867&id_sales=787&id_lokasi=1226&data_level=Administrator"
        
        all_data = []
        months = [f"{i:02d}" for i in range(1, 13)] if month == "Semua" else [month]
        
        for m in months:
            url = f"{base_export_url}&tgl1={m}"
            if year:
                url += f"&tgl2={year}"
                
            try:
                res = self.session.get(url, verify=False)
                res.raise_for_status()
                html = res.text
                
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
                for row in rows:
                    cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
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
                            "bukti_pembayaran_url": "",
                            "periode": utils.clean_html_text(cols[13]),
                            "metode": utils.clean_html_text(cols[14]),
                            "waktu_entry": utils.clean_html_text(cols[16]) if len(cols) > 16 else ""
                        }
                        all_data.append(record)
                    except Exception: pass
            except Exception as e:
                logger.error(f"   [!] Error fetching IPL Export for month {m}: {e}")
                
        logger.info(f"   [+] Parsed {len(all_data)} IPL records from Export across {len(months)} months.")
        return all_data

    def fetch_data_warga(self):
        """Fetch Data Warga."""
        logger.info("Fetching Data Warga (Export)...")
        try:
            res = self.session.get(config.URL_WARGA_EXPORT, verify=False)
            res.raise_for_status()
            html = res.text
            
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            header_index = _build_header_index(rows)
            data = []
            for row in rows:
                cols = _extract_cells(row, "td")
                if len(cols) < 20: continue 

                try:
                    id_pel = _column(cols, header_index, "ID Pelanggan", 3)
                    if not id_pel or "ID Pelanggan" in id_pel: continue
                    
                    tanggal_registrasi = _column(cols, header_index, "Tanggal Registrasi", 4)
                    jatuh_tempo = _column(cols, header_index, "Jatuh Tempo", 22)
                    
                    nik = _column(cols, header_index, "No ID Identitas", 12)
                    kk = "" 
                    
                    pppoe_user = _column(cols, header_index, "IP / Secret", 28)
                    pppoe_pass = _column(cols, header_index, "Password Secret", 29)
                    nama_lokasi = _column(cols, header_index, "Nama Lokasi", 30)
                    nama_router = _column(cols, header_index, "Nama Router", 32)
                    koordinat = _column(cols, header_index, "Titik Koordinat Lokasi", 38)
                    
                    ktp_url = ""
                    ktp_idx = header_index.get(_normalize_header("Foto KTP"), 13)
                    if ktp_idx < len(cols):
                        raw_ktp_col = cols[ktp_idx]
                        src_match = re.search(r'src="([^"]+)"', raw_ktp_col)
                        if src_match:
                            ktp_url = src_match.group(1)
                        else:
                            ktp_url = utils.clean_html_text(raw_ktp_col)

                    record = {
                        "id_pelanggan": id_pel,
                        "nama_pelanggan": _column(cols, header_index, "Nama Pelanggan", 5),
                        "nik": nik,
                        "kk": kk,
                        "alamat": _column(cols, header_index, "Alamat", 9),
                        "telepon": _column(cols, header_index, "Tlp", 10),
                        "paket": _column(cols, header_index, "Nama Langganan", 15),
                        "harga": utils.parse_price(_column(cols, header_index, "Harga", 18)),
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
