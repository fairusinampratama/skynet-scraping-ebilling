import os
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import sync

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("scheduler")

def job():
    logger.info("Scheduler triggered nightly sync task.")
    sync.run_sync()

if __name__ == "__main__":
    scrape_hour = int(os.environ.get("SCRAPE_HOUR", "0"))
    
    scheduler = BlockingScheduler()
    # Trigger every day at the designated hour (default 00:00)
    scheduler.add_job(job, 'cron', hour=scrape_hour, minute=0)
    
    logger.info(f"Starting APScheduler, scheduled to run daily at hour: {scrape_hour}:00")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
