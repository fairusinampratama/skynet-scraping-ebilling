from fastapi import FastAPI, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database import engine, get_db, Base
from models import Area, Package, Customer, Invoice, Branch, SyncLog
import sync

import logging
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger("api")

# Create tables if not exist (mostly for local sqlite testing)
Base.metadata.create_all(bind=engine)

def scheduled_sync_job():
    logger.info("Running scheduled eBilling sync job...")
    try:
        sync.run_sync()
    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup background scheduler
    scheduler = BackgroundScheduler()
    scrape_hour = int(os.environ.get("SCRAPE_HOUR", 0))  # Default: Midnight
    
    scheduler.add_job(
        scheduled_sync_job,
        'cron',
        hour=scrape_hour,
        minute=0,
        id='nightly_ebilling_sync',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"APScheduler started. Nightly sync scheduled at hour {scrape_hour:02d}:00.")
    
    yield
    
    # Shutdown scheduler
    scheduler.shutdown()
    logger.info("APScheduler stopped.")

app = FastAPI(title="eBilling Scraper API", version="1.0.0", lifespan=lifespan)

ADMIN_API_KEY = os.environ.get("API_KEY", "secret-key-123")

def verify_api_key(api_key: str = Header(None)):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.get("/api/v1/areas")
def get_areas(db: Session = Depends(get_db)):
    return db.query(Area).all()

@app.get("/api/v1/packages")
def get_packages(db: Session = Depends(get_db)):
    return db.query(Package).all()

@app.get("/api/v1/customers")
def get_customers(
    status: Optional[str] = None,
    area_id: Optional[int] = None,
    package_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Customer)
    if status:
        query = query.filter(Customer.status == status.lower())
    if area_id:
        query = query.filter(Customer.area_id == area_id)
    if package_id:
        query = query.filter(Customer.package_id == package_id)
        
    # Return relationships manually crafted for JSON serialization
    customers = query.all()
    results = []
    for c in customers:
        results.append({
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "nik": c.nik,
            "address": c.address,
            "phone": c.phone,
            "geo_lat": c.geo_lat,
            "geo_long": c.geo_long,
            "pppoe_user": c.pppoe_user,
            "status": c.status,
            "join_date": c.join_date,
            "due_day": c.due_day,
            "is_online": c.is_online,
            "ktp_photo_url": c.ktp_photo_url,
            "package": {"id": c.package.id, "name": c.package.name, "price": c.package.price} if c.package else None,
            "area": {"id": c.area.id, "code": c.area.code, "name": c.area.name} if c.area else None
        })
    return results

@app.get("/api/v1/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    return {
        "id": c.id,
        "code": c.code,
        "name": c.name,
        "nik": c.nik,
        "address": c.address,
        "phone": c.phone,
        "geo_lat": c.geo_lat,
        "geo_long": c.geo_long,
        "pppoe_user": c.pppoe_user,
        "status": c.status,
        "join_date": c.join_date,
        "due_day": c.due_day,
        "is_online": c.is_online,
        "ktp_photo_url": c.ktp_photo_url,
        "package": {"id": c.package.id, "name": c.package.name, "price": c.package.price} if c.package else None,
        "area": {"id": c.area.id, "code": c.area.code, "name": c.area.name} if c.area else None
    }

@app.get("/api/v1/invoices")
def get_invoices(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Invoice)
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if status:
        query = query.filter(Invoice.status == status.lower())
    if period:
        # Expected format YYYY-MM-DD
        query = query.filter(Invoice.period == period)
        
    return query.all()

@app.get("/api/v1/branches")
def get_branches(db: Session = Depends(get_db)):
    return db.query(Branch).all()

@app.get("/api/v1/sync/logs")
def get_sync_logs(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(SyncLog).order_by(SyncLog.id.desc()).limit(limit).all()

@app.post("/api/v1/sync/trigger")
def trigger_sync(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    # In a real async environment, we'd fire this off as a background task.
    # For simplicity, we just trigger it immediately and block.
    try:
        sync.run_sync()
        return {"status": "success", "message": "Manual sync triggered and finished."}
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
