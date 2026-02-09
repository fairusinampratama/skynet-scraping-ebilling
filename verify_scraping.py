
from scraper import SkynetScraper
import json

def verify():
    scraper = SkynetScraper()
    scraper.login()
    
    # Verify Cabang
    cabang_data = scraper.fetch_dashboard_cabang()
    with open("scraped_cabang.json", "w") as f:
        json.dump(cabang_data, f, indent=4)
    
    # Verify IPL
    ipl_data = scraper.fetch_data_ipl()
    with open("scraped_ipl.json", "w") as f:
        json.dump(ipl_data, f, indent=4)
        
    # Verify Warga
    warga_data = scraper.fetch_data_warga()
    with open("scraped_warga.json", "w") as f:
        json.dump(warga_data, f, indent=4)

if __name__ == "__main__":
    verify()
