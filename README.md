# Skynet e-Billing Scraper

A robust Python tool designed to scrape, aggregate, and enrich customer data from the Skynet e-Billing dashboard.

## Features
- **Master Data Scraping**: Extracts full customer list from the main dashboard table.
- **Coordinate Recovery**: Parses hidden Google Maps JavaScript blobs to valid Latitude/Longitude coordinates.
- **Photo Enrichment**: Generates valid KTP photo URLs by fuzzing and verifying paths against the server.
- **Data Validation**: Automatically merges data and cleans up broken links.

## Prerequisites
- Python 3.8+
- An active account on the e-Billing dashboard.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/skynet_scraping_ebilling.git
   cd skynet_scraping_ebilling
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment:
   Copy `.env.example` to `.env` and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```ini
   SKYNET_USER=your_username
   SKYNET_PASS=your_password
   SKYNET_ACCT=your_account_id
   ```

## Usage

Run the main script to start the scraping pipeline:

```bash
python3 -m skynet_scraping_ebilling.main
```

The script will:
1. Login to the dashboard.
2. Scrape the master customer list.
3. Fetch map data and link coordinates to customers.
4. Generate and validate KTP photo URLs.
5. Save the final output to `final_customer_data.json`.

## Disclaimer
This tool is for educational and authorized administrative use only. Ensure you have permission to scrape the target dashboard.
