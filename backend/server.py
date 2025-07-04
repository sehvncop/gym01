from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
import qrcode
import io
import base64
from calendar import monthrange
import razorpay
import hashlib
import hmac
import secrets
import time
import bcrypt

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "gym_saas")

# Razorpay configuration (with placeholders)
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "YOUR_RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "YOUR_RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "YOUR_WEBHOOK_SECRET")

# Frontend URL for QR codes
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# FastAPI app
app = FastAPI(title="Gym Management SaaS", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Razorpay client (only initialize if keys are provided)
razorpay_client = None
if RAZORPAY_KEY_ID != "YOUR_RAZORPAY_KEY_ID" and RAZORPAY_KEY_SECRET != "YOUR_RAZORPAY_KEY_SECRET":
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Pydantic models
class GymOwnerCreate(BaseModel):
    name: str
    phone: str
    gym_name: str
    address: str
    monthly_fee: float
    date_of_birth: str  # Will be combined with gym_name for password
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone number must be 10 digits')
        return v

class GymOwnerLogin(BaseModel):
    phone: str
    password: str  # DOB + gym_name

class GymOwnerResponse(BaseModel):
    id: str
    name: str
    phone: str
    gym_name: str
    address: str
    monthly_fee: float
    qr_code: str
    member_registration_url: str
    cash_verification_qr: str
    whatsapp_sender_number: str
    created_at: datetime

class MemberCreate(BaseModel):
    name: str
    phone: str
    gym_id: str
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone number must be 10 digits')
        return v

class MemberResponse(BaseModel):
    id: str
    name: str
    phone: str
    joining_date: str  # Changed from date to str for JSON serialization
    fee_status: str  # 'paid', 'unpaid'
    current_month_fee: float
    payment_method: Optional[str]  # 'cash', 'online', None
    is_active: bool
    created_at: datetime

class PaymentUpdate(BaseModel):
    payment_method: str  # 'cash' or 'online'

class RazorpayOrderCreate(BaseModel):
    amount: int  # Amount in paise
    currency: str = "INR"
    receipt: Optional[str] = None

class RazorpayPaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    member_id: str
    gym_id: str

class WhatsAppConfig(BaseModel):
    sender_number: str

class SendNotificationRequest(BaseModel):
    member_id: str
    custom_message: Optional[str] = None

class PaymentSessionRequest(BaseModel):
    member_id: str
    amount: float

# Utility functions
def generate_qr_code(data: str) -> str:
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def generate_payment_session_qr(gym_id: str, session_id: str) -> str:
    """Generate dynamic QR code for payment session"""
    payment_url = f"{FRONTEND_URL}/verify-cash-payment/{gym_id}?session={session_id}"
    return generate_qr_code(payment_url)

def generate_password_hash(password: str) -> str:
    """Generate password hash using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def calculate_prorated_fee(monthly_fee: float, joining_date: date) -> float:
    """Calculate prorated fee based on joining date"""
    today = date.today()
    
    # If joined on 1st, no proration needed
    if joining_date.day == 1:
        return 0.0
    
    # Calculate days remaining in current month
    days_in_month = monthrange(joining_date.year, joining_date.month)[1]
    days_remaining = days_in_month - joining_date.day + 1
    
    # Calculate prorated amount
    daily_rate = monthly_fee / days_in_month
    prorated_amount = daily_rate * days_remaining
    
    return round(prorated_amount, 2)

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature"""
    if not razorpay_client:
        return False
    
    try:
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        return True
    except:
        return False

# API Routes
@app.get("/")
async def root():
    return {"message": "Gym Management SaaS API", "status": "running"}

@app.post("/api/gym-owner/login")
async def login_gym_owner(credentials: GymOwnerLogin):
    """Login gym owner"""
    try:
        # Find gym owner by phone
        gym_owner = await db.gym_owners.find_one({"phone": credentials.phone})
        if not gym_owner:
            raise HTTPException(status_code=401, detail="Invalid phone number or password")
        
        # Verify password
        if not verify_password(credentials.password, gym_owner["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid phone number or password")
        
        # Return gym owner data (excluding password)
        return GymOwnerResponse(**{
            k: v for k, v in gym_owner.items() 
            if k != "password_hash"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gym-owner/register", response_model=GymOwnerResponse)
async def register_gym_owner(owner: GymOwnerCreate):
    """Register a new gym owner"""
    try:
        # Check if phone already exists
        existing_owner = await db.gym_owners.find_one({"phone": owner.phone})
        if existing_owner:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Generate unique ID
        gym_id = str(uuid.uuid4())
        
        # Create member registration URL with current frontend URL
        member_registration_url = f"{FRONTEND_URL}/register-member/{gym_id}"
        
        # Generate QR codes
        qr_code_data = member_registration_url
        qr_code = generate_qr_code(qr_code_data)
        
        # Cash verification QR
        cash_verification_url = f"{FRONTEND_URL}/verify-cash-payment/{gym_id}"
        cash_verification_qr = generate_qr_code(cash_verification_url)
        
        # Create gym owner document
        gym_doc = {
            "id": gym_id,
            "name": owner.name,
            "phone": owner.phone,
            "gym_name": owner.gym_name,
            "address": owner.address,
            "monthly_fee": owner.monthly_fee,
            "qr_code": qr_code,
            "member_registration_url": member_registration_url,
            "cash_verification_qr": cash_verification_qr,
            "created_at": datetime.utcnow()
        }
        
        # Insert gym owner
        await db.gym_owners.insert_one(gym_doc)
        
        # Create collection name for gym members
        collection_name = f"gym_{gym_id.replace('-', '_')}_members"
        
        # Store collection reference (create index)
        await db[collection_name].create_index("phone", unique=True)
        
        return GymOwnerResponse(**gym_doc)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gym-owner/{gym_id}")
async def get_gym_owner(gym_id: str):
    """Get gym owner details"""
    owner = await db.gym_owners.find_one({"id": gym_id})
    if not owner:
        raise HTTPException(status_code=404, detail="Gym owner not found")
    
    return GymOwnerResponse(**owner)

@app.post("/api/member/register", response_model=MemberResponse)
async def register_member(member: MemberCreate):
    """Register a new gym member"""
    try:
        # Get gym owner details
        gym_owner = await db.gym_owners.find_one({"id": member.gym_id})
        if not gym_owner:
            raise HTTPException(status_code=404, detail="Gym not found")
        
        # Get collection name
        collection_name = f"gym_{member.gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        
        # Check if member already exists
        existing_member = await members_collection.find_one({"phone": member.phone})
        if existing_member:
            raise HTTPException(status_code=400, detail="Member already registered with this gym")
        
        # Generate member ID
        member_id = str(uuid.uuid4())
        
        # Calculate joining date and fees
        joining_date = date.today()
        monthly_fee = gym_owner["monthly_fee"]
        prorated_fee = calculate_prorated_fee(monthly_fee, joining_date)
        
        # Create member document
        member_doc = {
            "id": member_id,
            "name": member.name,
            "phone": member.phone,
            "joining_date": joining_date.isoformat(),  # Convert date to string
            "fee_status": "unpaid",
            "current_month_fee": prorated_fee if prorated_fee > 0 else monthly_fee,
            "payment_method": None,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        # Insert member
        await members_collection.insert_one(member_doc)
        
        return MemberResponse(**member_doc)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gym/{gym_id}/members", response_model=List[MemberResponse])
async def get_gym_members(gym_id: str):
    """Get all members of a gym"""
    try:
        # Verify gym exists
        gym_owner = await db.gym_owners.find_one({"id": gym_id})
        if not gym_owner:
            raise HTTPException(status_code=404, detail="Gym not found")
        
        # Get collection name
        collection_name = f"gym_{gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        
        # Get all members
        members_cursor = members_collection.find({})
        members = await members_cursor.to_list(length=None)
        
        return [MemberResponse(**member) for member in members]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/member/{gym_id}/{member_id}/payment")
async def update_payment_status(gym_id: str, member_id: str, payment: PaymentUpdate):
    """Update member payment status (mark as paid)"""
    try:
        # Get collection name
        collection_name = f"gym_{gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        
        # Update member payment status
        update_result = await members_collection.update_one(
            {"id": member_id},
            {
                "$set": {
                    "fee_status": "paid",
                    "payment_method": payment.payment_method,
                    "payment_updated_at": datetime.utcnow()
                }
            }
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Member not found")
        
        return {"message": "Payment status updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/member/{gym_id}/{member_id}/toggle-active")
async def toggle_member_active_status(gym_id: str, member_id: str):
    """Toggle member active/inactive status"""
    try:
        # Get collection name
        collection_name = f"gym_{gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        
        # Get current member status
        member = await members_collection.find_one({"id": member_id})
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Toggle active status
        new_status = not member.get("is_active", True)
        
        await members_collection.update_one(
            {"id": member_id},
            {"$set": {"is_active": new_status}}
        )
        
        return {"message": f"Member {'activated' if new_status else 'deactivated'} successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/member/{gym_id}/{member_id}")
async def delete_member(gym_id: str, member_id: str):
    """Delete a member"""
    try:
        # Get collection name
        collection_name = f"gym_{gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        
        # Delete member
        delete_result = await members_collection.delete_one({"id": member_id})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Member not found")
        
        return {"message": "Member deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Razorpay integration endpoints
@app.post("/api/payment/create-order")
async def create_payment_order(order_data: RazorpayOrderCreate, gym_id: str, member_id: str):
    """Create Razorpay payment order"""
    if not razorpay_client:
        return {
            "error": "Razorpay not configured",
            "message": "Please add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to environment variables",
            "status": "not_configured"
        }
    
    try:
        # Verify gym and member exist
        gym_owner = await db.gym_owners.find_one({"id": gym_id})
        if not gym_owner:
            raise HTTPException(status_code=404, detail="Gym not found")
        
        collection_name = f"gym_{gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        member = await members_collection.find_one({"id": member_id})
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Create order
        order_data.receipt = f"gym_{gym_id}_member_{member_id}_{int(datetime.utcnow().timestamp())}"
        
        order = razorpay_client.order.create({
            "amount": order_data.amount,
            "currency": order_data.currency,
            "receipt": order_data.receipt,
            "payment_capture": 1
        })
        
        # Store order in database
        await db.payment_orders.insert_one({
            "order_id": order["id"],
            "gym_id": gym_id,
            "member_id": member_id,
            "amount": order_data.amount,
            "currency": order_data.currency,
            "status": "created",
            "created_at": datetime.utcnow()
        })
        
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": RAZORPAY_KEY_ID
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payment/verify")
async def verify_payment(payment_data: RazorpayPaymentVerify):
    """Verify Razorpay payment"""
    if not razorpay_client:
        return {
            "error": "Razorpay not configured",
            "status": "not_configured"
        }
    
    try:
        # Verify signature
        if not verify_razorpay_signature(
            payment_data.razorpay_order_id,
            payment_data.razorpay_payment_id,
            payment_data.razorpay_signature
        ):
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Update payment order status
        await db.payment_orders.update_one(
            {"order_id": payment_data.razorpay_order_id},
            {
                "$set": {
                    "payment_id": payment_data.razorpay_payment_id,
                    "status": "completed",
                    "verified_at": datetime.utcnow()
                }
            }
        )
        
        # Update member payment status
        collection_name = f"gym_{payment_data.gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        
        await members_collection.update_one(
            {"id": payment_data.member_id},
            {
                "$set": {
                    "fee_status": "paid",
                    "payment_method": "online",
                    "payment_id": payment_data.razorpay_payment_id,
                    "payment_updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Payment verified successfully", "status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payment/webhook")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhooks"""
    if not razorpay_client:
        return {"status": "not_configured"}
    
    try:
        # Get webhook payload and signature
        payload = await request.body()
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        # Verify webhook signature
        if RAZORPAY_WEBHOOK_SECRET != "YOUR_WEBHOOK_SECRET":
            expected_signature = hmac.new(
                RAZORPAY_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected_signature:
                raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Process webhook event
        import json
        event_data = json.loads(payload.decode())
        
        if event_data.get('event') == 'payment.captured':
            payment = event_data.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment.get('order_id')
            
            if order_id:
                # Update payment order status
                await db.payment_orders.update_one(
                    {"order_id": order_id},
                    {
                        "$set": {
                            "webhook_status": "captured",
                            "webhook_received_at": datetime.utcnow()
                        }
                    }
                )
        
        return {"status": "processed"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cash payment verification endpoint
@app.post("/api/verify-cash-payment/{gym_id}")
async def verify_cash_payment(gym_id: str, phone: str, name: str):
    """Verify cash payment"""
    try:
        # Get collection name
        collection_name = f"gym_{gym_id.replace('-', '_')}_members"
        members_collection = db[collection_name]
        
        # Find and verify member
        member = await members_collection.find_one({
            "phone": phone,
            "name": {"$regex": name, "$options": "i"}
        })
        
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Mark as paid
        await members_collection.update_one(
            {"id": member["id"]},
            {
                "$set": {
                    "fee_status": "paid",
                    "payment_method": "cash",
                    "payment_updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": f"Cash payment verified for {member['name']}", "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Monthly fee reset logic (to be called by a scheduler)
@app.post("/api/admin/reset-monthly-fees")
async def reset_monthly_fees():
    """Reset all member fee statuses for new month (admin endpoint)"""
    try:
        # Get all gym owners
        gym_owners_cursor = db.gym_owners.find({})
        gym_owners = await gym_owners_cursor.to_list(length=None)
        
        total_updated = 0
        
        for gym_owner in gym_owners:
            gym_id = gym_owner["id"]
            collection_name = f"gym_{gym_id.replace('-', '_')}_members"
            members_collection = db[collection_name]
            
            # Reset all active members to unpaid status
            update_result = await members_collection.update_many(
                {"is_active": True},
                {
                    "$set": {
                        "fee_status": "unpaid",
                        "payment_method": None,
                        "current_month_fee": gym_owner["monthly_fee"],
                        "month_reset_at": datetime.utcnow()
                    }
                }
            )
            
            total_updated += update_result.modified_count
        
        return {
            "message": f"Monthly fees reset for {total_updated} members across {len(gym_owners)} gyms",
            "total_members_updated": total_updated,
            "total_gyms": len(gym_owners)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WhatsApp integration endpoints (placeholders for now)
@app.get("/api/whatsapp/status")
async def get_whatsapp_status():
    """Get WhatsApp integration status"""
    return {
        "connected": False,
        "message": "WhatsApp integration not configured",
        "instructions": "WhatsApp automation for monthly reminders will be available once configured"
    }

@app.post("/api/whatsapp/send-reminders")
async def send_monthly_reminders():
    """Send monthly fee reminders to unpaid members"""
    return {
        "message": "WhatsApp reminders not configured",
        "instructions": "WhatsApp automation will be available once configured",
        "status": "not_configured"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)