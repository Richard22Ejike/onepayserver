import os
import random
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from decouple import config
from users.models import User, OneTimePassword


def GenerateOtp():
    otp = ""
    for i in range(6):
        otp += str(random.randint(1, 9))
    return otp


def send_email_to_user(email, message, subject):
    message = Mail(
        from_email='support@oneplug.ng ',
        to_emails=email,
        subject=subject,
        html_content=message)
    try:
        print('the email')
        sg = SendGridAPIClient(config('EMAIL_HOST_PASSWORD'), )
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
    except Exception as e:
        print(f"An error occurred: {e}")


api_key_otp = config('SECRETKEY')


def send_otp(customer_email, medium,
             customer_phone, sender="OneplugPay", expiry=5, send_=True,
             length=6, customer_name="Oneplug", ):
    url = "https://api.flutterwave.com/v3/otps"

    payload = {
        "length": length,
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone
        },
        "sender": sender,
        "send": send_,
        "medium": medium,
        "expiry": expiry
    }

    headers = {
        'Authorization': f'Bearer {api_key_otp}',
        'Content-Type': 'application/json',
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        response_data = response.json()
        print("OTP generated successfully:")

        # Loop through each medium and print the OTP
        for item in response_data.get("data", []):
            medium_type = item.get("medium")
            otp = item.get("otp")
            expiry = item.get("expiry")
            print(f"Medium: {medium_type}, OTP: {otp}, Expiry: {expiry}")

        return response_data.get("data")  # Returning the list of OTPs for different mediums
    else:
        print(f"Error sending OTP: {response.text}")
        return None


def send_sms(to, sms, api_key, from_="OnePlugPay", type_="plain", channel="generic", media_url=None,
             media_caption=None):
    url = "https://api.ng.termii.com/api/sms/send"
    payload = {
        "to": f"+234${to}",
        "from": from_,
        "sms": sms,
        "type": type_,
        "channel": channel,
        "api_key": api_key,
    }

    if media_url and media_caption:
        payload["media"] = {
            "url": media_url,
            "caption": media_caption
        }

    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f'the phone {response.text}')
