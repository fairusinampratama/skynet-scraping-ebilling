
import os
import json
import time
from scraper import SkynetScraper

def main():
    print("=== Skynet Migration Data Exporter ===")
    
    # 1. Initialize & Login
    scraper = SkynetScraper()
    scraper.login()
    
    # 2. Create Output Directory
    output_dir = "migration_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # 3. Fetch Data Sources
    
    # A. Dashboard Cabang (Branches/Financials)
    cabang_data = scraper.fetch_dashboard_cabang()
    with open(f"{output_dir}/branches.json", "w") as f:
        json.dump(cabang_data, f, indent=4)
    print(f"[✓] Saved {len(cabang_data)} branch records to {output_dir}/branches.json")
    
    # B. Data IPL (Payments/Transactions)
    # Using IPL as the primary source for 'invoices'/'transactions'
    # Fetch all historical data (2021-2026)
    ipl_data = scraper.fetch_all_historical_transactions()
    with open(f"{output_dir}/transactions.json", "w") as f:
        json.dump(ipl_data, f, indent=4)
    print(f"[✓] Saved {len(ipl_data)} transaction records to {output_dir}/transactions.json")
    
    # C. Data Warga (Customers - The Master List)
    # This export contains: Profile, Package, Price, PPPoE Creds (User/Pass), KTP Photo, Coordinates
    warga_data = scraper.fetch_data_warga()
    with open(f"{output_dir}/customers.json", "w") as f:
        json.dump(warga_data, f, indent=4)
    print(f"[✓] Saved {len(warga_data)} customer records to {output_dir}/customers.json")
    
    print("\n=== Export Complete ===")
    print(f"Data is ready in '{output_dir}/' folder.")
    print("Please check README.md for mapping instructions.")

if __name__ == "__main__":
    main()
