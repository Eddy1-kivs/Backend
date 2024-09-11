import requests
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Fetch IntaSend credentials from environment variables
INTASEND_API_URL = "https://api.intasend.com/api/v1/checkout/"
INTASEND_SECRET_KEY = os.getenv('INTASEND_SECRET_KEY')
INTASEND_PUBLIC_KEY = os.getenv('INTASEND_PUBLIC_KEY')

def initiate_payment(user, amount):
    headers = {
        "Authorization": f"Bearer {INTASEND_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "public_key": INTASEND_PUBLIC_KEY,
        "amount": amount,
        "currency": "USD",
        "payment_type": "card",  # or "mobile"
        "email": user.email,
        "tx_ref": f"JobPayment_{user.id}_{amount}",
        "redirect_url": "https://yourdomain.com/payment-success",
    }

    response = requests.post(f"{INTASEND_API_URL}request", json=data, headers=headers)
    response_data = response.json()

    logger.debug("IntaSend API Response: %s", response_data)

    if response.status_code == 201:
        return {
            "status": "success",
            "transaction_id": response_data.get("transaction_id"),
            "payment_url": response_data.get("url"),
        }
    else:
        logger.error("Payment initiation failed: %s", response_data)
        return {
            "status": "failed",
            "message": response_data.get("message", "Payment initiation failed"),
        }


def verify_payment(transaction_id):
    """
    Verifies a payment status with IntaSend.
    """
    headers = {
        "Authorization": f"Bearer {INTASEND_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(f"{INTASEND_API_URL}status/{transaction_id}", headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data["status"] == "completed":
            return "completed"
        else:
            logger.error("Payment verification failed: %s", response_data)
            return "failed"
    except Exception as e:
        logger.exception("Exception during payment verification: %s", e)
        return "failed"
