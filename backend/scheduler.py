"""
Scheduler for Gym Management SaaS
Handles monthly fee resets and WhatsApp reminders
"""

import asyncio
import schedule
import time
from datetime import datetime
from whatsapp_service import run_monthly_reminders
import requests
import os

# Backend URL for API calls
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")

def reset_monthly_fees():
    """Reset monthly fees on the 1st of each month"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/admin/reset-monthly-fees")
        if response.status_code == 200:
            result = response.json()
            print(f"Monthly fees reset: {result}")
        else:
            print(f"Failed to reset monthly fees: {response.text}")
    except Exception as e:
        print(f"Error resetting monthly fees: {e}")

def send_daily_reminders():
    """Send WhatsApp reminders daily during reminder period (1st-7th)"""
    try:
        result = asyncio.run(run_monthly_reminders())
        print(f"Daily reminders result: {result}")
    except Exception as e:
        print(f"Error sending daily reminders: {e}")

def setup_scheduler():
    """Setup the scheduler for all recurring tasks"""
    
    # Reset monthly fees on the 1st of every month at 1 AM
    schedule.every().month.at("01:00").do(reset_monthly_fees)
    
    # Send reminders daily at 10 AM (will only send during 1st-7th period)
    schedule.every().day.at("10:00").do(send_daily_reminders)
    
    # Send reminders daily at 6 PM (will only send during 1st-7th period)
    schedule.every().day.at("18:00").do(send_daily_reminders)
    
    print("Scheduler setup complete:")
    print("- Monthly fee reset: 1st of every month at 1:00 AM")
    print("- WhatsApp reminders: Daily at 10:00 AM and 6:00 PM (1st-7th only)")

def run_scheduler():
    """Run the scheduler continuously"""
    setup_scheduler()
    
    print(f"Scheduler started at {datetime.now()}")
    print("Waiting for scheduled tasks...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # For testing - you can run specific tasks
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            print("Testing monthly fee reset...")
            reset_monthly_fees()
        elif sys.argv[1] == "reminders":
            print("Testing WhatsApp reminders...")
            send_daily_reminders()
        elif sys.argv[1] == "schedule":
            print("Running scheduler...")
            run_scheduler()
    else:
        print("Usage:")
        print("  python scheduler.py reset      - Test monthly fee reset")
        print("  python scheduler.py reminders  - Test WhatsApp reminders")
        print("  python scheduler.py schedule   - Run continuous scheduler")