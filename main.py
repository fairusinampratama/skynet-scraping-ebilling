import utils
from scraper import SkynetScraper

def main():
    print("=== SKYNET EBILLING SCRAPER ===")
    
    # 1. Setup
    utils.setup_environment()
    
    # 2. Initialize
    bot = SkynetScraper()
    
    # 3. Execution Pipeline
    bot.login()
    bot.fetch_master_data()  # 1800+ records
    bot.fetch_coordinates()  # Map parsing
    bot.enrich_data()        # Merge & Generate URLs
    bot.validate_photos()    # 404 cleanup
    
    # 4. Save
    bot.save_results("final_customer_data.json")
    print("=== MISSION COMPLETE ===")

if __name__ == "__main__":
    main()
