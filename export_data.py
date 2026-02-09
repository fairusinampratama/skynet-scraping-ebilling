
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
    trans_file = f"{output_dir}/transactions.json"
    if os.path.exists(trans_file) and os.path.getsize(trans_file) > 1024:
        print(f"[!] Skipping Transaction Scraping (File exists: {trans_file})")
    else:
        # Fetch all historical data (2021-2026)
        ipl_data = scraper.fetch_all_historical_transactions()
        with open(trans_file, "w") as f:
            json.dump(ipl_data, f, indent=4)
        print(f"[✓] Saved {len(ipl_data)} transaction records to {trans_file}")
    
    # C. Data Warga (Customers - The Master List)
    # This export contains: Profile, Package, Price, PPPoE Creds (User/Pass), KTP Photo, Coordinates
    warga_data = scraper.fetch_data_warga()
    
    # [NEW] Fetch Connection Status (Active/Isolated)
    # This requires an extra step to hit the dynamic AJAX endpoint
    status_map = scraper.fetch_customer_status()
    
    # Merge Status into Customer Records
    for customer in warga_data:
        c_id = customer.get("id_pelanggan")
        # Default to "Offline" if not found in the status map (which covers Active/Isolated)
        # Note: "Offline" here just means "Not in the Active/Isolated list" or "Unknown"
        customer["connection_status"] = status_map.get(c_id, "Offline")

    with open(f"{output_dir}/customers.json", "w") as f:
        json.dump(warga_data, f, indent=4)
    print(f"[✓] Saved {len(warga_data)} customer records (with status) to {output_dir}/customers.json")
    
    print("\n=== Export Complete ===")
    print(f"Data is ready in '{output_dir}/' folder.")
    print("Please check README.md for mapping instructions.")

if __name__ == "__main__":
    main()
