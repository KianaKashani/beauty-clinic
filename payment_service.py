import os
import requests
from config import Config
from dotenv import load_dotenv

load_dotenv()
# ZarinPal configuration
MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID")
ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_START_PAY_URL = "https://www.zarinpal.com/pg/StartPay/{}"
CALLBACK_URL = Config.ZARINPAL_CALLBACK_URL

def create_payment(amount, description, callback_url=None):
    """
    Create a payment request with ZarinPal
    Returns a tuple of (payment_url, authority)
    """
    if not MERCHANT_ID:
        print("Warning: ZARINPAL_MERCHANT_ID not set. Payment simulation enabled.")
        # For development without a real payment gateway
        # We'll redirect back to our verify route with success status
        redirect_url = CALLBACK_URL + "?Status=OK&Authority=dev-payment-simulation"
        return redirect_url, "dev-payment-simulation"
    
    callback = callback_url or CALLBACK_URL
    
    data = {
        "merchant_id": MERCHANT_ID,
        "amount": amount,
        "description": description,
        "callback_url": callback
    }
    
    try:
        response = requests.post(ZARINPAL_REQUEST_URL, json=data)
        result = response.json()
        
        if result['data']['code'] == 100:
            authority = result['data']['authority']
            payment_url = ZARINPAL_START_PAY_URL.format(authority)
            return payment_url, authority
        else:
            print(f"Error creating payment: {result['errors']['code']}")
            return None, None
    
    except Exception as e:
        print(f"Error in create_payment: {e}")
        return None, None

def verify_payment(authority, amount):
    """
    Verify a payment with ZarinPal
    Returns True if payment is verified, False otherwise
    """
    if not MERCHANT_ID:
        print("Warning: ZARINPAL_MERCHANT_ID not set. Payment simulation enabled.")
        # For development without a real payment gateway
        # Our dev-payment-simulation should always verify as valid
        if authority == "dev-payment-simulation":
            return True
        else:
            return False
    
    data = {
        "merchant_id": MERCHANT_ID,
        "amount": amount,
        "authority": authority
    }
    
    try:
        response = requests.post(ZARINPAL_VERIFY_URL, json=data)
        result = response.json()
        
        if result['data']['code'] == 100:
            # Payment verified
            ref_id = result['data']['ref_id']
            print(f"Payment verified with ref_id: {ref_id}")
            return True
        else:
            print(f"Payment verification failed: {result['errors']['code']}")
            return False
    
    except Exception as e:
        print(f"Error in verify_payment: {e}")
        return False
