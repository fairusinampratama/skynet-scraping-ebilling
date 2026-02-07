import json
import os

OLD_FILE = "/home/fairusinampratama/python/final_customer_data.json"
NEW_FILE = "/home/fairusinampratama/python/skynet-scraping-ebilling/final_customer_data.json"

def load_json(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return []
    with open(path, 'r') as f:
        return json.load(f)

print(f"Comparing:")
print(f"  Old: {OLD_FILE}")
print(f"  New: {NEW_FILE}")

old_data = load_json(OLD_FILE)
new_data = load_json(NEW_FILE)

print(f"  Old Count: {len(old_data)}")
print(f"  New Count: {len(new_data)}")

# Create Maps by Code
old_map = {item.get('code'): item for item in old_data}
new_map = {item.get('code'): item for item in new_data}

old_codes = set(old_map.keys())
new_codes = set(new_map.keys())

added = new_codes - old_codes
removed = old_codes - new_codes
intersect = new_codes & old_codes

print(f"\n--- Differences ---")
print(f"Added Records: {len(added)}")
if added:
    print(f"  Examples: {list(added)[:5]}")

print(f"Removed Records: {len(removed)}")
if removed:
    print(f"  Examples: {list(removed)[:5]}")

modified_count = 0
modifications = []

keys_to_ignore = ['ktp_photo_url'] # URL might change slightly or be re-generated

for code in intersect:
    o = old_map[code]
    n = new_map[code]
    
    diffs = []
    for k, v in n.items():
        if k in keys_to_ignore: continue
        if o.get(k) != v:
            diffs.append(f"{k}: '{o.get(k)}' -> '{v}'")
    
    if diffs:
        modified_count += 1
        if len(modifications) < 10:
            modifications.append(f"  {code}: {', '.join(diffs)}")

print(f"Modified Records: {modified_count}")
if modifications:
    print("\nSample Modifications:")
    for mod in modifications:
        print(mod)
print("\nDone.")
