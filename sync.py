import sys
import uuid
import logging
from datetime import datetime
from database import engine, Base, SessionLocal
from models import Area, Package, Customer, Invoice, Branch, SyncLog
from scraper import SkynetScraper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sync')

def parse_date(date_str):
    if not date_str or date_str == "-":
        return None
    try:
        # e.g., "03-October-2022"
        return datetime.strptime(date_str, "%d-%B-%Y").date()
    except ValueError:
        return None

def parse_period_to_date(period_str):
    # e.g., "Maret 2026" or "March 2026"
    if not period_str:
        return None
    
    # Indonesian Month Mapping
    months = {
        "januari": 1, "january": 1,
        "februari": 2, "february": 2,
        "maret": 3, "march": 3,
        "april": 4,
        "mei": 5, "may": 5,
        "juni": 6, "june": 6,
        "juli": 7, "july": 7,
        "agustus": 8, "august": 8,
        "september": 9,
        "oktober": 10, "october": 10,
        "november": 11,
        "desember": 12, "december": 12
    }
    
    parts = period_str.strip().lower().split()
    if len(parts) == 2:
        month_name = parts[0]
        year = parts[1]
        
        m = months.get(month_name)
        if m and year.isdigit():
            return datetime(int(year), m, 1).date()
    return None

def run_sync():
    logger.info("Starting eBilling nightly sync...")
    
    # Init DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    sync_log = SyncLog(started_at=datetime.utcnow(), status="running")
    db.add(sync_log)
    db.commit()
    
    try:
        scraper = SkynetScraper()
        if not scraper.login():
            raise Exception("Failed to login to Skynet")

        # 1. Fetch Customers & Status
        warga_data = scraper.fetch_data_warga()
        status_map = scraper.fetch_customer_status()
        
        # Merge status
        for cust in warga_data:
            c_id = cust.get("id_pelanggan")
            cust["connection_status"] = status_map.get(c_id, "unknown")

        logger.info(f"Normalizing Data Warga (count: {len(warga_data)})...")
        # Ensure Packages & Areas exist, then insert Customers
        processed_customers = set()
        for p_data in warga_data:
            # Handle Customer Deduplication in Payload
            c_id = p_data.get("id_pelanggan")
            if not c_id or c_id in processed_customers:
                continue
            processed_customers.add(c_id)
            
            # Handle Package
            pkg_name = p_data.get("paket")
            pkg_price = p_data.get("harga", 0)
            
            pkg_id = None
            if pkg_name:
                pkg = db.query(Package).filter(Package.name == pkg_name).first()
                if not pkg:
                    pkg = Package(name=pkg_name, price=pkg_price)
                    db.add(pkg)
                    db.flush() # get ID
                else:
                    # Update price if changed
                    if pkg.price != pkg_price:
                        pkg.price = pkg_price
                pkg_id = pkg.id
            
            # Handle Area
            area_name = p_data.get("nama_lokasi")
            area_code = p_data.get("nama_router")
            
            area_id = None
            if area_name:
                area = db.query(Area).filter(Area.name == area_name).first()
                if not area:
                    area = Area(name=area_name, code=area_code)
                    db.add(area)
                    db.flush()
                else:
                    if area_code and area.code != area_code:
                        area.code = area_code
                area_id = area.id
            
            # Handle Customer
            c_id = p_data.get("id_pelanggan")
            if not c_id: continue
            
            geo_str = str(p_data.get("koordinat", ""))
            lat, lng = None, None
            if "," in geo_str:
                parts = geo_str.split(",")
                try:
                    parsed_lat = float(parts[0].strip())
                    parsed_lng = float(parts[1].strip())
                    # Validate bounds to prevent DB out of range errors
                    if -90 <= parsed_lat <= 90 and -180 <= parsed_lng <= 180:
                        lat = parsed_lat
                        lng = parsed_lng
                except: pass

            due_day_str = p_data.get("jatuh_tempo", "")
            due_day = None
            if due_day_str.isdigit():
                due_day = int(due_day_str)

            cust = db.query(Customer).filter(Customer.id == c_id).first()
            if not cust:
                cust = Customer(id=c_id)
                db.add(cust)
            
            cust.code = c_id
            cust.name = p_data.get("nama_pelanggan")
            cust.nik = p_data.get("nik")
            cust.address = p_data.get("alamat")
            cust.phone = p_data.get("telepon")
            cust.geo_lat = lat
            cust.geo_long = lng
            cust.pppoe_user = p_data.get("pppoe_username")
            cust.pppoe_password = p_data.get("pppoe_password")
            cust.package_id = pkg_id
            cust.area_id = area_id
            cust.status = p_data.get("connection_status").lower()
            if cust.status == "active":
                cust.is_online = True
                
            cust.join_date = parse_date(p_data.get("tanggal_registrasi"))
            cust.due_day = due_day
            cust.ktp_photo_url = p_data.get("ktp_photo_url")
            cust.last_synced_at = datetime.utcnow()
            
        db.commit()
        sync_log.customers_synced = len(warga_data)

        # 2. Fetch Invoices (We'll only do current year to limit strain, unless BACKFILL_YEARS is set)
        import os
        backfill_str = os.environ.get("BACKFILL_YEARS", "")
        years_to_sync = []
        if backfill_str:
            years_to_sync = [int(y.strip()) for y in backfill_str.split(",") if y.strip().isdigit()]
        
        curr_year = datetime.now().year
        if curr_year not in years_to_sync:
            years_to_sync.append(curr_year)
            
        ipl_data = []
        for y in years_to_sync:
            logger.info(f"Fetching IPL data for year {y}...")
            year_data = scraper.fetch_data_ipl(year=y)
            ipl_data.extend(year_data)
        
        logger.info(f"Normalizing Data IPL (count: {len(ipl_data)})...")
        
        # Pre-load existing customers to prevent foreign key errors from deleted accounts
        valid_customers = {c[0] for c in db.query(Customer.id).all()}
        
        for i_data in ipl_data:
            c_id = i_data.get("id_pelanggan")
            period_str = i_data.get("periode")
            
            period_date = parse_period_to_date(period_str)
            if not period_date or not c_id:
                continue
                
            # Handle orphaned invoices (deleted customers) by inserting a stub
            if c_id not in valid_customers:
                stub_cust = Customer(
                    id=c_id,
                    name=i_data.get("nama_pelanggan", "Unknown (Deleted)"),
                    address=i_data.get("alamat", ""),
                    status="deleted",
                    is_online=False,
                    last_synced_at=datetime.utcnow()
                )
                db.add(stub_cust)
                valid_customers.add(c_id)
                db.flush()
                
            inv = db.query(Invoice).filter(
                Invoice.customer_id == c_id,
                Invoice.period == period_date
            ).first()
                
            if not inv:
                inv = Invoice()
                inv.uuid = str(uuid.uuid4())
                inv.customer_id = c_id
                inv.period = period_date
                
                yyyymm = period_date.strftime("%Y%m")
                inv.code = f"INV-{yyyymm}-{c_id}"
                db.add(inv)
                db.flush() # Force ID generation and session awareness immediately
                
            inv.amount = i_data.get("nominal_harus_dibayar", 0)
            status_raw = i_data.get("status_pembayaran", "").lower()
            inv.status = "paid" if "lunas" in status_raw else "unpaid"
            
            due_day = 20
            # To avoid slow queries inside the loop, we could pre-fetch, but for now we query
            cust_ref = db.query(Customer).filter(Customer.id == c_id).first()
            if cust_ref and cust_ref.due_day:
                due_day = cust_ref.due_day
                
            try:
                inv.due_date = period_date.replace(day=due_day)
            except ValueError:
                inv.due_date = period_date 
                
            inv.payment_link = i_data.get("bukti_pembayaran_url")
            inv.last_synced_at = datetime.utcnow()
            
        db.commit()
        sync_log.invoices_synced = len(ipl_data)

        # 3. Fetch Branches
        branch_data = scraper.fetch_dashboard_cabang()
        logger.info(f"Normalizing Branches (count: {len(branch_data)})...")
        for b_data in branch_data:
            cabang = b_data.get("cabang")
            branch = db.query(Branch).filter(Branch.cabang == cabang).first()
            if not branch:
                branch = Branch(cabang=cabang)
                db.add(branch)
                
            branch.jumlah_pelanggan = int(b_data.get("jumlah_pelanggan") or 0)
            branch.pelanggan_lunas = int(b_data.get("pelanggan_lunas") or 0)
            branch.pelanggan_belum_lunas = int(b_data.get("pelanggan_belum_lunas") or 0)
            branch.total_pemasukan = b_data.get("total_pemasukan", 0)
            branch.total_pengeluaran = b_data.get("total_pengeluaran", 0)
            branch.balance = b_data.get("balance", 0)
            branch.total_estimasi = b_data.get("total_estimasi", 0)
            branch.last_synced_at = datetime.utcnow()
            
        db.commit()

        sync_log.status = "success"
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        db.rollback()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
    finally:
        sync_log.finished_at = datetime.utcnow()
        final_status = sync_log.status
        db.commit()
        db.close()
        logger.info(f"Sync finished with status: {final_status}")

if __name__ == "__main__":
    run_sync()
