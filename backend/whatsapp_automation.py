"""
WhatsApp Web Automation Service
Browser-based automation similar to RocketSender Chrome extension
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
import random
import time

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "gym_saas")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

class WhatsAppAutomation:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.automation_active = False
        self.message_interval = random.randint(10, 15)  # 10-15 seconds
    
    async def generate_monthly_reminders(self):
        """Generate monthly reminders for unpaid members"""
        try:
            # Get all gym owners
            gym_owners_cursor = self.db.gym_owners.find({})
            gym_owners = await gym_owners_cursor.to_list(length=None)
            
            for gym_owner in gym_owners:
                gym_id = gym_owner["id"]
                collection_name = f"gym_{gym_id.replace('-', '_')}_members"
                members_collection = self.db[collection_name]
                
                # Get unpaid active members
                unpaid_cursor = members_collection.find({
                    "fee_status": "unpaid",
                    "is_active": True
                })
                unpaid_members = await unpaid_cursor.to_list(length=None)
                
                # Generate notifications for unpaid members
                for member in unpaid_members:
                    # Check if reminder already sent this month
                    current_month = datetime.now().strftime("%Y-%m")
                    existing_reminder = await self.db.notification_queue.find_one({
                        "member_id": member["id"],
                        "gym_id": gym_id,
                        "type": "monthly_reminder",
                        "month": current_month
                    })
                    
                    if not existing_reminder:
                        message = self.generate_reminder_message(member, gym_owner)
                        
                        notification = {
                            "id": f"reminder_{gym_id}_{member['id']}_{int(time.time())}",
                            "gym_id": gym_id,
                            "member_id": member["id"],
                            "phone": member["phone"],
                            "member_name": member["name"],
                            "gym_name": gym_owner["gym_name"],
                            "sender_number": gym_owner.get("whatsapp_sender_number", gym_owner["phone"]),
                            "message": message,
                            "status": "pending",
                            "type": "monthly_reminder",
                            "month": current_month,
                            "created_at": datetime.utcnow(),
                            "priority": 1  # Monthly reminders have high priority
                        }
                        
                        await self.db.notification_queue.insert_one(notification)
            
            print(f"Monthly reminders generated for {len(gym_owners)} gyms")
            
        except Exception as e:
            print(f"Error generating monthly reminders: {e}")
    
    def generate_reminder_message(self, member: Dict, gym_owner: Dict) -> str:
        """Generate personalized reminder message"""
        current_month = datetime.now().strftime("%B %Y")
        
        message = f"""🏋️ *{gym_owner['gym_name']}* 

Hi {member['name']}! 👋

This is a friendly reminder that your gym membership fee for {current_month} is due.

💰 *Amount Due:* ₹{member['current_month_fee']}

*Payment Options:*
💵 Cash Payment: Visit the gym and pay directly
💳 Online Payment: Use our secure payment portal

📞 *Contact:* {gym_owner['phone']}
📍 *Address:* {gym_owner['address']}

Thank you for being a valued member! 💪

_Reply STOP to unsubscribe from reminders_"""
        
        return message
    
    async def get_pending_notifications(self, limit: int = 10) -> List[Dict]:
        """Get pending notifications with rate limiting"""
        try:
            # Check rate limiting
            current_hour = datetime.utcnow().hour
            today = datetime.utcnow().date()
            
            # Count notifications sent in current hour
            hour_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            hour_count = await self.db.notification_queue.count_documents({
                "status": "sent",
                "sent_at": {"$gte": hour_start}
            })
            
            # Count notifications sent today
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            day_count = await self.db.notification_queue.count_documents({
                "status": "sent",
                "sent_at": {"$gte": day_start}
            })
            
            # Apply rate limiting (40-50 per hour, 250 per day)
            max_per_hour = random.randint(40, 50)
            max_per_day = 250
            
            if hour_count >= max_per_hour or day_count >= max_per_day:
                return []
            
            # Get pending notifications (prioritize monthly reminders)
            remaining_slots = min(max_per_hour - hour_count, max_per_day - day_count, limit)
            
            notifications_cursor = self.db.notification_queue.find({
                "status": "pending"
            }).sort("priority", -1).limit(remaining_slots)
            
            notifications = await notifications_cursor.to_list(length=remaining_slots)
            
            return notifications
            
        except Exception as e:
            print(f"Error getting pending notifications: {e}")
            return []
    
    async def mark_notification_sent(self, notification_id: str):
        """Mark notification as sent"""
        try:
            await self.db.notification_queue.update_one(
                {"id": notification_id},
                {
                    "$set": {
                        "status": "sent",
                        "sent_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error marking notification as sent: {e}")
    
    async def mark_notification_failed(self, notification_id: str, error: str):
        """Mark notification as failed"""
        try:
            await self.db.notification_queue.update_one(
                {"id": notification_id},
                {
                    "$set": {
                        "status": "failed",
                        "failed_at": datetime.utcnow(),
                        "error": error
                    }
                }
            )
        except Exception as e:
            print(f"Error marking notification as failed: {e}")
    
    async def cleanup_old_notifications(self):
        """Clean up old notifications (older than 7 days)"""
        try:
            seven_days_ago = datetime.utcnow().timestamp() - (7 * 24 * 60 * 60)
            
            # Delete old sent/failed notifications
            await self.db.notification_queue.delete_many({
                "status": {"$in": ["sent", "failed"]},
                "created_at": {"$lt": datetime.fromtimestamp(seven_days_ago)}
            })
            
            # Delete old payment sessions
            await self.db.payment_sessions.delete_many({
                "expires_at": {"$lt": datetime.utcnow().timestamp()}
            })
            
            print("Old notifications and sessions cleaned up")
            
        except Exception as e:
            print(f"Error cleaning up old notifications: {e}")
    
    def get_whatsapp_automation_instructions(self) -> Dict:
        """Get instructions for WhatsApp Web automation"""
        return {
            "automation_type": "whatsapp_web",
            "instructions": {
                "setup": [
                    "1. Open WhatsApp Web (web.whatsapp.com) in your browser",
                    "2. Scan QR code with your phone to login",
                    "3. Keep the WhatsApp Web tab open",
                    "4. The system will automatically send notifications"
                ],
                "features": [
                    "Automatic message sending with 10-15 second intervals",
                    "Rate limiting: 40-50 messages per hour, 250 per day",
                    "Monthly reminder automation",
                    "Manual notification sending",
                    "Dynamic QR code generation for payments"
                ],
                "endpoints": {
                    "get_queue": f"{FRONTEND_URL}/api/whatsapp/queue",
                    "update_status": f"{FRONTEND_URL}/api/whatsapp/update-status/<notification_id>",
                    "generate_reminders": f"{FRONTEND_URL}/api/whatsapp/generate-reminders"
                }
            }
        }

# Global instance
whatsapp_automation = WhatsAppAutomation()

async def run_automation_cycle():
    """Run one cycle of WhatsApp automation"""
    try:
        # Generate monthly reminders if needed
        today = datetime.now().day
        if 1 <= today <= 7:  # First 7 days of month
            await whatsapp_automation.generate_monthly_reminders()
        
        # Clean up old notifications
        await whatsapp_automation.cleanup_old_notifications()
        
        # Get pending notifications
        notifications = await whatsapp_automation.get_pending_notifications()
        
        return {
            "status": "success",
            "pending_notifications": len(notifications),
            "automation_instructions": whatsapp_automation.get_whatsapp_automation_instructions()
        }
        
    except Exception as e:
        print(f"Error in automation cycle: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Test the automation
    async def test():
        result = await run_automation_cycle()
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(test())