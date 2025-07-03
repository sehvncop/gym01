<file>
      <absolute_file_name>/app/backend/whatsapp_service.py</absolute_file_name>
      <content">"""
WhatsApp Integration for Gym Management SaaS
Simplified implementation using webhooks and external WhatsApp Business API
"""

import os
import json
import asyncio
from datetime import datetime, date
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "gym_saas")
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "YOUR_WHATSAPP_API_ENDPOINT")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "YOUR_WHATSAPP_API_TOKEN")

class WhatsAppService:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.api_configured = (
            WHATSAPP_API_URL != "YOUR_WHATSAPP_API_ENDPOINT" and 
            WHATSAPP_API_TOKEN != "YOUR_WHATSAPP_API_TOKEN"
        )
    
    async def send_message(self, phone_number: str, message: str) -> bool:
        """Send WhatsApp message to a phone number"""
        if not self.api_configured:
            print(f"WhatsApp not configured. Would send to {phone_number}: {message}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{WHATSAPP_API_URL}/messages",
                    headers={
                        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "text",
                        "text": {"body": message}
                    }
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return False
    
    async def get_unpaid_members(self) -> List[Dict]:
        """Get all unpaid members across all gyms"""
        unpaid_members = []
        
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
            unpaid_list = await unpaid_cursor.to_list(length=None)
            
            for member in unpaid_list:
                member["gym_info"] = gym_owner
                unpaid_members.append(member)
        
        return unpaid_members
    
    def generate_reminder_message(self, member: Dict, gym_info: Dict) -> str:
        """Generate personalized reminder message"""
        current_month = datetime.now().strftime("%B %Y")
        
        message = f"""🏋️‍♂️ *{gym_info['gym_name']}* 

Hi {member['name']}! 👋

This is a friendly reminder that your gym membership fee for {current_month} is due.

💰 *Amount Due:* ₹{member['current_month_fee']}

*Payment Options:*
🏪 *Cash Payment:* Visit the gym and pay directly
💳 *Online Payment:* Use our secure payment link

📞 *Contact:* {gym_info['phone']}
📍 *Address:* {gym_info['address']}

Thank you for being a valued member! 💪

_Reply STOP to unsubscribe from reminders_"""
        
        return message
    
    async def send_monthly_reminders(self) -> Dict:
        """Send monthly fee reminders to all unpaid members"""
        print("Starting monthly reminder process...")
        
        unpaid_members = await self.get_unpaid_members()
        
        if not unpaid_members:
            print("No unpaid members found.")
            return {
                "total_members": 0,
                "messages_sent": 0,
                "messages_failed": 0,
                "status": "completed"
            }
        
        messages_sent = 0
        messages_failed = 0
        
        for member in unpaid_members:
            try:
                message = self.generate_reminder_message(member, member["gym_info"])
                success = await self.send_message(member["phone"], message)
                
                if success:
                    messages_sent += 1
                    # Log the reminder
                    await self.db.whatsapp_logs.insert_one({
                        "member_id": member["id"],
                        "gym_id": member["gym_info"]["id"],
                        "phone": member["phone"],
                        "message_type": "monthly_reminder",
                        "status": "sent",
                        "sent_at": datetime.utcnow()
                    })
                else:
                    messages_failed += 1
                    # Log the failure
                    await self.db.whatsapp_logs.insert_one({
                        "member_id": member["id"],
                        "gym_id": member["gym_info"]["id"],
                        "phone": member["phone"],
                        "message_type": "monthly_reminder",
                        "status": "failed",
                        "failed_at": datetime.utcnow()
                    })
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                messages_failed += 1
                print(f"Error sending reminder to {member['phone']}: {e}")
        
        result = {
            "total_members": len(unpaid_members),
            "messages_sent": messages_sent,
            "messages_failed": messages_failed,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"Reminder process completed: {result}")
        return result
    
    async def send_payment_confirmation(self, member_id: str, gym_id: str) -> bool:
        """Send payment confirmation message"""
        try:
            # Get member and gym info
            collection_name = f"gym_{gym_id.replace('-', '_')}_members"
            members_collection = self.db[collection_name]
            member = await members_collection.find_one({"id": member_id})
            
            gym_owner = await self.db.gym_owners.find_one({"id": gym_id})
            
            if not member or not gym_owner:
                return False
            
            message = f"""✅ *Payment Confirmed!*

Hi {member['name']}! 

Your payment of ₹{member['current_month_fee']} has been successfully received.

🏋️‍♂️ *{gym_owner['gym_name']}*
📅 *Payment Date:* {datetime.now().strftime('%d %B %Y')}
💳 *Method:* {member.get('payment_method', 'Cash').title()}

Thank you for your prompt payment! Keep up the great work! 💪

_Reply STOP to unsubscribe from notifications_"""
            
            success = await self.send_message(member["phone"], message)
            
            if success:
                # Log the confirmation
                await self.db.whatsapp_logs.insert_one({
                    "member_id": member_id,
                    "gym_id": gym_id,
                    "phone": member["phone"],
                    "message_type": "payment_confirmation",
                    "status": "sent",
                    "sent_at": datetime.utcnow()
                })
            
            return success
            
        except Exception as e:
            print(f"Error sending payment confirmation: {e}")
            return False
    
    async def is_reminder_period(self) -> bool:
        """Check if current date is in reminder period (1st-7th of month)"""
        today = date.today()
        return 1 <= today.day <= 7

# Global instance
whatsapp_service = WhatsAppService()

async def run_monthly_reminders():
    """Run monthly reminders if in reminder period"""
    if await whatsapp_service.is_reminder_period():
        print("In reminder period (1st-7th). Sending monthly reminders...")
        return await whatsapp_service.send_monthly_reminders()
    else:
        print("Outside reminder period. No reminders sent.")
        return {"status": "outside_reminder_period"}

if __name__ == "__main__":
    # Test the service
    async def test():
        result = await run_monthly_reminders()
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
</content>
    </file>