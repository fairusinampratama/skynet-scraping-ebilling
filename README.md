# Skynet Migration Data

This folder contains the cleaned data extracted from the legacy e-billing system, ready for import into the new database.

## 📂 File Structure

- **`customers_final.json`**: **USE THIS FOR IMPORT** - Final cleaned data (1,743 records, sanitized coordinates)
- `customers_clean.json`: Deduplicated but with unsanitized coordinates
- `customers.json`: Original export with duplicates
- `transactions.json`: Payment history (from "Data IPL")
- `branches.json`: Branch financial summaries (from "Dashboard Cabang")

## 🔄 Mapping Guide for Migration

### 1. Table: `customers`
Source: `customers.json`

| Destination Column | Source JSON Key | Notes |
| :--- | :--- | :--- |
| `id` | `id_pelanggan` | Primary Key (String/Char) |
| `name` | `nama_pelanggan` | |
| `address` | `alamat` | |
| `phone_number` | `telepon` | |
| `nik` | `nik` | National Identity Number |
| `kk` | `kk` | Family Card Number |
| `coordinates` | `koordinat` | Format: "lat,lng" (Needs splitting) |
| `pppoe_username` | `pppoe_username` | |
| `pppoe_password` | `pppoe_password` | **Warning**: Often empty in source. |
| `identity_card_photo_path` | `ktp_photo_url` | URL needs downloading if storing locally. |
| `is_active` | `connection_status` | "Active" -> true, "Isolated" -> false |
| `registered_at` | `tanggal_registrasi` | Registration date (e.g., "01-February-2026") |
| `billing_day` | `jatuh_tempo` | Day of month for bill due date (e.g., "30") |

### 2. Table: `packages`
Source: `customers.json` (Derived)

- Extract unique `paket` values from `customers.json`.
- Map `paket` name AND `harga`.
- Create new records in `packages` table.

### 3. Table: `routers`
Source: `customers.json` (Derived)

- Extract unique `nama_router` values.
- **Action Required**: You must manually update the `routers` table with IP Address, Username, and Password for each router name found (e.g., "SKYNET-SRIGADING").

### 4. Table: `invoices` & `transactions`
Source: `transactions.json`

| Destination Column | Source JSON Key | Notes |
| :--- | :--- | :--- |
| `customer_id` | `id_pelanggan` | Foreign Key |
| `period` | `periode` | e.g., "February 2026" |
| `amount` | `nominal_harus_dibayar` | |
| `status` | `status_pembayaran` | "Lunas" -> "paid" |
| `payment_method` | `metode` | |
| `proof_of_payment` | `bukti_pembayaran_url` | |

## 🚀 How to Run the Export

To regenerate these files:

```bash
python3 export_data.py
```

This will fetch the latest data and overwrite the files in the `migration_data/` folder.
