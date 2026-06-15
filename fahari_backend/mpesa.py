import base64
import logging
from datetime import datetime

import requests
from decouple import config
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

SANDBOX_URL = "https://sandbox.safaricom.co.ke"
PRODUCTION_URL = "https://api.safaricom.co.ke"


def _setting(name, default=""):
    return config(name, default=default).strip()


def get_base_url():
    env = _setting("MPESA_ENV", "sandbox").lower()
    return PRODUCTION_URL if env == "production" else SANDBOX_URL


def get_access_token():
    url = f"{get_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    consumer_key = _setting("MPESA_CONSUMER_KEY")
    consumer_secret = _setting("MPESA_CONSUMER_SECRET")

    if not consumer_key or not consumer_secret:
        raise ValueError("MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set.")

    response = requests.get(
        url,
        auth=HTTPBasicAuth(consumer_key, consumer_secret),
        timeout=30,
    )

    if not response.ok:
        logger.error(
            "M-Pesa OAuth failed: status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise requests.HTTPError(
            f"M-Pesa authentication failed ({response.status_code}). "
            "Verify MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET in your .env file.",
            response=response,
        )

    return response.json()["access_token"]


def _build_stk_password():
    shortcode = _setting("MPESA_SHORTCODE")
    passkey = _setting("MPESA_PASSKEY")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()
    return shortcode, timestamp, password


def _format_phone(phone_number):
    phone = str(phone_number).strip().replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone
    return phone


def _mpesa_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def stk_push(phone_number, amount, booking_reference):
    try:
        access_token = get_access_token()
    except (requests.HTTPError, ValueError, KeyError) as exc:
        return {"error": True, "detail": str(exc)}

    shortcode, timestamp, password = _build_stk_password()
    phone = _format_phone(phone_number)
    callback_url = _setting("MPESA_CALLBACK_URL")

    if not callback_url:
        return {"error": True, "detail": "MPESA_CALLBACK_URL is not configured."}

    url = f"{get_base_url()}/mpesa/stkpush/v1/processrequest"
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": str(booking_reference)[:12],
        "TransactionDesc": f"Booking {str(booking_reference)[:10]}",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=_mpesa_headers(access_token),
            timeout=30,
        )
        data = response.json()
    except requests.RequestException as exc:
        logger.exception("STK push request failed")
        return {"error": True, "detail": str(exc)}
    except ValueError:
        logger.error("STK push returned non-JSON response: %s", response.text)
        return {"error": True, "detail": "Invalid response from M-Pesa.", "raw": response.text}

    logger.info("STK push response: %s - %s", response.status_code, data)
    return data


def stk_query(checkout_request_id):
    try:
        access_token = get_access_token()
    except (requests.HTTPError, ValueError, KeyError) as exc:
        return {"error": True, "detail": str(exc)}

    shortcode, timestamp, password = _build_stk_password()
    url = f"{get_base_url()}/mpesa/stkpushquery/v1/query"
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=_mpesa_headers(access_token),
            timeout=30,
        )
        data = response.json()
    except requests.RequestException as exc:
        logger.exception("STK query request failed")
        return {"error": True, "detail": str(exc)}
    except ValueError:
        logger.error("STK query returned non-JSON response: %s", response.text)
        return {"error": True, "detail": "Invalid response from M-Pesa.", "raw": response.text}

    logger.info("STK query response: %s - %s", response.status_code, data)
    return data


def mpesa_success_code(result_code):
    return int(result_code) == 0
