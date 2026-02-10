import json
import os
import re
from datetime import datetime

def parse_date(date_str):
    """Parse date formats like '01-February-2026' or '01/02/2026'."""
    if not date_str or date_str == "00-00-0000":
        return datetime.min
    
    formats = ["%d-%B-%Y", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.min

def sanitize_coordinate(coord_str):
    """Extract lat/long from various messy formats."""
    if not coord_str or coord_str.lower() in ["null", "none", "0,0", "0", ""]:
        return None, None
    
    # Replace Indonesian comma decimals with dots
    # But only if it's like "-7,123456"
    # We first split by common separators if possible
    parts = re.split(r'[,;|\s]+', coord_str.strip())
    
    if len(parts) < 2:
        return None, None
        
    def clean_num(s):
        # Remove directional suffixes and other junk
        s = re.sub(r'[^\d.,-]', '', s)
        # If it has more than one comma, it's definitely messy
        # If it has a comma that looks like a decimal (-7,123), replace it
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        # If it still has multiple dots, keep only the first dot and the negative sign
        # Actually just try to float it
        try:
            return float(s)
        except ValueError:
            return None

    lat = clean_num(parts[0])
    lon = clean_num(parts[1])
    
    # Validation
    if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None, None

def main():
    input_file = "migration_data/customers.json"
    output_file = "migration_data/customers_final.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r") as f:
        data = json.load(f)

    print(f"Processing {len(data)} records from {input_file}...")

    # 1. Deduplication
    # Group by id_pelanggan
    grouped = {}
    for record in data:
        cid = record.get("id_pelanggan")
        if not cid: continue
        if cid not in grouped:
            grouped[cid] = []
        grouped[cid].append(record)

    final_records = []
    duplicates_count = 0
    
    for cid, records in grouped.items():
        if len(records) > 1:
            duplicates_count += len(records) - 1
            # Strategy: Keep Active over others
            # Then keep most recent tanggal_registrasi
            records.sort(key=lambda x: (
                1 if x.get("connection_status") == "Active" else 0,
                parse_date(x.get("tanggal_registrasi"))
            ), reverse=True)
            best_record = records[0]
        else:
            best_record = records[0]
            
        # 2. Fix Empty PPPoE Username
        if not best_record.get("pppoe_username"):
            best_record["pppoe_username"] = f"NOPPPOE_{cid}"
            
        # 3. Sanitize Coordinates
        orig_coord = best_record.get("koordinat", "")
        lat, lon = sanitize_coordinate(orig_coord)
        best_record["geo_lat"] = lat
        best_record["geo_long"] = lon
        best_record["koordinat_original"] = orig_coord
        
        final_records.append(best_record)

    # Sort final list by ID for consistency
    final_records.sort(key=lambda x: x.get("id_pelanggan", ""))

    with open(output_file, "w") as f:
        json.dump(final_records, f, indent=4)

    print(f"\n=== Finalization Complete ===")
    print(f"Original Records: {len(data)}")
    print(f"Removed Duplicates: {duplicates_count}")
    print(f"Final Unique Records: {len(final_records)}")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
