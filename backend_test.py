import requests
import json
import unittest
import uuid
from datetime import datetime, date
import base64
import re
from io import BytesIO
from PIL import Image

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://5d34af7c-83d6-445f-b180-77e8b539ea1b.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

class GymManagementAPITest(unittest.TestCase):
    """Test suite for Gym Management SaaS API"""
    
    def setUp(self):
        """Setup for tests - generate unique data for each test run"""
        # Generate unique identifiers for this test run
        self.unique_id = str(uuid.uuid4())[:8]
        self.gym_owner_data = {
            "name": f"Test Owner {self.unique_id}",
            "phone": f"9{self.unique_id.replace('-', '')}123",  # Ensure 10 digits
            "gym_name": f"Test Gym {self.unique_id}",
            "address": f"123 Test Street, Test City {self.unique_id}",
            "monthly_fee": 1000.0
        }
        # Fix phone number to ensure it's 10 digits
        if len(self.gym_owner_data["phone"]) > 10:
            self.gym_owner_data["phone"] = self.gym_owner_data["phone"][:10]
        elif len(self.gym_owner_data["phone"]) < 10:
            self.gym_owner_data["phone"] = self.gym_owner_data["phone"].ljust(10, '0')
        
        self.gym_id = None
        self.member_id = None
    
    def test_01_gym_owner_registration(self):
        """Test gym owner registration API"""
        print("\n--- Testing Gym Owner Registration ---")
        
        # Test registration
        response = requests.post(f"{API_BASE_URL}/gym-owner/register", json=self.gym_owner_data)
        self.assertEqual(response.status_code, 200, f"Failed to register gym owner: {response.text}")
        
        data = response.json()
        self.assertIn("id", data, "Gym ID not found in response")
        self.assertIn("qr_code", data, "QR code not found in response")
        self.assertIn("cash_verification_qr", data, "Cash verification QR not found in response")
        
        # Store gym_id for subsequent tests
        self.gym_id = data["id"]
        print(f"Successfully registered gym owner with ID: {self.gym_id}")
        
        # Verify QR code is valid base64
        self.assertTrue(self._is_valid_base64_image(data["qr_code"]), "QR code is not a valid base64 image")
        print("QR code validation successful")
        
        # Test duplicate registration (should fail)
        response = requests.post(f"{API_BASE_URL}/gym-owner/register", json=self.gym_owner_data)
        self.assertEqual(response.status_code, 400, "Duplicate registration should fail")
        print("Duplicate registration check passed")
        
        # Test invalid phone number
        invalid_data = self.gym_owner_data.copy()
        invalid_data["phone"] = "123"  # Too short
        response = requests.post(f"{API_BASE_URL}/gym-owner/register", json=invalid_data)
        self.assertEqual(response.status_code, 422, "Invalid phone validation failed")
        print("Phone number validation check passed")
    
    def test_02_get_gym_owner(self):
        """Test get gym owner API"""
        print("\n--- Testing Get Gym Owner ---")
        
        # Skip if gym_id is not available
        if not self.gym_id:
            self.test_01_gym_owner_registration()
        
        # Test get gym owner
        response = requests.get(f"{API_BASE_URL}/gym-owner/{self.gym_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get gym owner: {response.text}")
        
        data = response.json()
        self.assertEqual(data["id"], self.gym_id, "Gym ID mismatch")
        self.assertEqual(data["name"], self.gym_owner_data["name"], "Gym owner name mismatch")
        self.assertEqual(data["gym_name"], self.gym_owner_data["gym_name"], "Gym name mismatch")
        print(f"Successfully retrieved gym owner with ID: {self.gym_id}")
        
        # Test non-existent gym owner
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{API_BASE_URL}/gym-owner/{fake_id}")
        self.assertEqual(response.status_code, 404, "Non-existent gym owner should return 404")
        print("Non-existent gym owner check passed")
    
    def test_03_member_registration(self):
        """Test member registration API"""
        print("\n--- Testing Member Registration ---")
        
        # Skip if gym_id is not available
        if not self.gym_id:
            self.test_01_gym_owner_registration()
        
        # Create member data
        member_data = {
            "name": f"Test Member {self.unique_id}",
            "phone": f"8{self.unique_id.replace('-', '')}456",  # Ensure 10 digits
            "gym_id": self.gym_id
        }
        
        # Fix phone number to ensure it's 10 digits
        if len(member_data["phone"]) > 10:
            member_data["phone"] = member_data["phone"][:10]
        elif len(member_data["phone"]) < 10:
            member_data["phone"] = member_data["phone"].ljust(10, '0')
        
        # Test member registration
        response = requests.post(f"{API_BASE_URL}/member/register", json=member_data)
        self.assertEqual(response.status_code, 200, f"Failed to register member: {response.text}")
        
        data = response.json()
        self.assertIn("id", data, "Member ID not found in response")
        self.assertIn("current_month_fee", data, "Fee calculation not found in response")
        self.assertIn("fee_status", data, "Fee status not found in response")
        self.assertEqual(data["fee_status"], "unpaid", "New member should have unpaid status")
        
        # Store member_id for subsequent tests
        self.member_id = data["id"]
        print(f"Successfully registered member with ID: {self.member_id}")
        
        # Verify prorated fee calculation
        today = date.today()
        self.assertIsInstance(data["current_month_fee"], (int, float), "Fee should be a number")
        print(f"Prorated fee calculation successful: {data['current_month_fee']}")
        
        # Test duplicate registration (should fail)
        response = requests.post(f"{API_BASE_URL}/member/register", json=member_data)
        self.assertEqual(response.status_code, 400, "Duplicate member registration should fail")
        print("Duplicate member registration check passed")
        
        # Test registration with invalid gym_id
        invalid_member = member_data.copy()
        invalid_member["gym_id"] = str(uuid.uuid4())
        invalid_member["phone"] = "9876543210"  # Different phone to avoid duplicate
        response = requests.post(f"{API_BASE_URL}/member/register", json=invalid_member)
        self.assertEqual(response.status_code, 404, "Registration with invalid gym_id should fail")
        print("Invalid gym_id check passed")
    
    def test_04_get_gym_members(self):
        """Test get gym members API"""
        print("\n--- Testing Get Gym Members ---")
        
        # Skip if previous tests haven't been run
        if not self.gym_id:
            self.test_01_gym_owner_registration()
        if not self.member_id:
            self.test_03_member_registration()
        
        # Test get gym members
        response = requests.get(f"{API_BASE_URL}/gym/{self.gym_id}/members")
        self.assertEqual(response.status_code, 200, f"Failed to get gym members: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response should be a list of members")
        self.assertGreaterEqual(len(data), 1, "At least one member should be returned")
        
        # Verify our test member is in the list
        member_found = False
        for member in data:
            if member["id"] == self.member_id:
                member_found = True
                break
        
        self.assertTrue(member_found, "Test member not found in members list")
        print(f"Successfully retrieved {len(data)} members for gym ID: {self.gym_id}")
        
        # Test with non-existent gym_id
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{API_BASE_URL}/gym/{fake_id}/members")
        self.assertEqual(response.status_code, 404, "Non-existent gym should return 404")
        print("Non-existent gym check passed")
    
    def test_05_update_payment_status(self):
        """Test update payment status API"""
        print("\n--- Testing Update Payment Status ---")
        
        # Skip if previous tests haven't been run
        if not self.gym_id:
            self.test_01_gym_owner_registration()
        if not self.member_id:
            self.test_03_member_registration()
        
        # Test update payment status (cash)
        payment_data = {"payment_method": "cash"}
        response = requests.patch(f"{API_BASE_URL}/member/{self.gym_id}/{self.member_id}/payment", json=payment_data)
        self.assertEqual(response.status_code, 200, f"Failed to update payment status: {response.text}")
        print("Successfully updated payment status to cash")
        
        # Verify payment status was updated
        response = requests.get(f"{API_BASE_URL}/gym/{self.gym_id}/members")
        data = response.json()
        member_found = False
        for member in data:
            if member["id"] == self.member_id:
                member_found = True
                self.assertEqual(member["fee_status"], "paid", "Fee status should be paid")
                self.assertEqual(member["payment_method"], "cash", "Payment method should be cash")
                break
        
        self.assertTrue(member_found, "Test member not found in members list")
        print("Payment status verification successful")
        
        # Test with non-existent member_id
        fake_id = str(uuid.uuid4())
        response = requests.patch(f"{API_BASE_URL}/member/{self.gym_id}/{fake_id}/payment", json=payment_data)
        self.assertEqual(response.status_code, 404, "Non-existent member should return 404")
        print("Non-existent member check passed")
    
    def test_06_toggle_member_active_status(self):
        """Test toggle member active status API"""
        print("\n--- Testing Toggle Member Active Status ---")
        
        # Skip if previous tests haven't been run
        if not self.gym_id:
            self.test_01_gym_owner_registration()
        if not self.member_id:
            self.test_03_member_registration()
        
        # Get current status
        response = requests.get(f"{API_BASE_URL}/gym/{self.gym_id}/members")
        data = response.json()
        current_status = None
        for member in data:
            if member["id"] == self.member_id:
                current_status = member["is_active"]
                break
        
        self.assertIsNotNone(current_status, "Could not determine current active status")
        print(f"Current active status: {current_status}")
        
        # Test toggle active status
        response = requests.patch(f"{API_BASE_URL}/member/{self.gym_id}/{self.member_id}/toggle-active")
        self.assertEqual(response.status_code, 200, f"Failed to toggle active status: {response.text}")
        print("Successfully toggled active status")
        
        # Verify status was toggled
        response = requests.get(f"{API_BASE_URL}/gym/{self.gym_id}/members")
        data = response.json()
        new_status = None
        for member in data:
            if member["id"] == self.member_id:
                new_status = member["is_active"]
                break
        
        self.assertIsNotNone(new_status, "Could not determine new active status")
        self.assertNotEqual(current_status, new_status, "Active status should have been toggled")
        print(f"New active status: {new_status}")
        
        # Toggle back to original status
        response = requests.patch(f"{API_BASE_URL}/member/{self.gym_id}/{self.member_id}/toggle-active")
        self.assertEqual(response.status_code, 200, "Failed to toggle active status back")
        print("Successfully toggled active status back to original")
        
        # Test with non-existent member_id
        fake_id = str(uuid.uuid4())
        response = requests.patch(f"{API_BASE_URL}/member/{self.gym_id}/{fake_id}/toggle-active")
        self.assertEqual(response.status_code, 404, "Non-existent member should return 404")
        print("Non-existent member check passed")
    
    def test_07_cash_payment_verification(self):
        """Test cash payment verification API"""
        print("\n--- Testing Cash Payment Verification ---")
        
        # Skip if previous tests haven't been run
        if not self.gym_id:
            self.test_01_gym_owner_registration()
        if not self.member_id:
            self.test_03_member_registration()
        
        # First, ensure member has unpaid status
        # Register a new member for this test
        member_data = {
            "name": f"Cash Test Member {self.unique_id}",
            "phone": f"7{self.unique_id.replace('-', '')}789",  # Ensure 10 digits
            "gym_id": self.gym_id
        }
        
        # Fix phone number to ensure it's 10 digits
        if len(member_data["phone"]) > 10:
            member_data["phone"] = member_data["phone"][:10]
        elif len(member_data["phone"]) < 10:
            member_data["phone"] = member_data["phone"].ljust(10, '0')
        
        # Register new member
        response = requests.post(f"{API_BASE_URL}/member/register", json=member_data)
        self.assertEqual(response.status_code, 200, f"Failed to register test member: {response.text}")
        
        # Test cash payment verification
        verify_data = {
            "phone": member_data["phone"],
            "name": member_data["name"]
        }
        
        response = requests.post(f"{API_BASE_URL}/verify-cash-payment/{self.gym_id}", params=verify_data)
        self.assertEqual(response.status_code, 200, f"Failed to verify cash payment: {response.text}")
        
        data = response.json()
        self.assertTrue(data.get("success", False), "Cash verification should be successful")
        print("Successfully verified cash payment")
        
        # Verify member status was updated
        response = requests.get(f"{API_BASE_URL}/gym/{self.gym_id}/members")
        members = response.json()
        member_found = False
        for member in members:
            if member["phone"] == member_data["phone"]:
                member_found = True
                self.assertEqual(member["fee_status"], "paid", "Fee status should be paid")
                self.assertEqual(member["payment_method"], "cash", "Payment method should be cash")
                break
        
        self.assertTrue(member_found, "Test member not found in members list")
        print("Cash payment status verification successful")
        
        # Test with non-existent member
        fake_verify = {
            "phone": "9999999999",
            "name": "Non Existent Member"
        }
        response = requests.post(f"{API_BASE_URL}/verify-cash-payment/{self.gym_id}", params=fake_verify)
        self.assertEqual(response.status_code, 404, "Non-existent member should return 404")
        print("Non-existent member check passed")
    
    def test_08_delete_member(self):
        """Test delete member API"""
        print("\n--- Testing Delete Member ---")
        
        # Skip if previous tests haven't been run
        if not self.gym_id:
            self.test_01_gym_owner_registration()
        if not self.member_id:
            self.test_03_member_registration()
        
        # Test delete member
        response = requests.delete(f"{API_BASE_URL}/member/{self.gym_id}/{self.member_id}")
        self.assertEqual(response.status_code, 200, f"Failed to delete member: {response.text}")
        print(f"Successfully deleted member with ID: {self.member_id}")
        
        # Verify member was deleted
        response = requests.get(f"{API_BASE_URL}/gym/{self.gym_id}/members")
        data = response.json()
        for member in data:
            self.assertNotEqual(member["id"], self.member_id, "Member should have been deleted")
        
        print("Member deletion verification successful")
        
        # Test delete non-existent member
        response = requests.delete(f"{API_BASE_URL}/member/{self.gym_id}/{self.member_id}")
        self.assertEqual(response.status_code, 404, "Deleting already deleted member should return 404")
        print("Non-existent member deletion check passed")
    
    def _is_valid_base64_image(self, base64_string):
        """Helper method to validate base64 image"""
        try:
            # Decode base64
            image_data = base64.b64decode(base64_string)
            # Try to open as image
            image = Image.open(BytesIO(image_data))
            image.verify()
            return True
        except Exception as e:
            print(f"Invalid base64 image: {e}")
            return False


if __name__ == "__main__":
    # Run tests in order
    unittest.main(argv=['first-arg-is-ignored'], exit=False)