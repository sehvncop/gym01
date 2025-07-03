from fastapi import FastAPI, HTTPException, Depends
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

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "gym_saas")

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

# Pydantic models
class GymOwnerCreate(BaseModel):
    name: str
    phone: str
    gym_name: str
    address: str
    monthly_fee: float
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone number must be 10 digits')
        return v

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

# API Routes
@app.get("/")
async def root():
    return {"message": "Gym Management SaaS API", "status": "running"}

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
        
        # Create member registration URL
        member_registration_url = f"https://your-domain.com/register-member/{gym_id}"
        
        # Generate QR codes
        qr_code_data = member_registration_url
        qr_code = generate_qr_code(qr_code_data)
        
        # Cash verification QR (static for now)
        cash_verification_url = f"https://your-domain.com/verify-cash-payment/{gym_id}"
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
            "joining_date": joining_date,
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

# Placeholder for Razorpay integration
@app.post("/api/payment/create-order")
async def create_payment_order():
    """Placeholder for Razorpay order creation"""
    return {
        "message": "Razorpay integration placeholder",
        "instructions": "Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env file",
        "status": "not_configured"
    }

@app.post("/api/payment/verify")
async def verify_payment():
    """Placeholder for Razorpay payment verification"""
    return {
        "message": "Razorpay payment verification placeholder",
        "status": "not_configured"
    }

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)