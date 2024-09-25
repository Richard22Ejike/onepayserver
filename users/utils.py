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


def send_sms(to, sms, api_key, from_="OnePlugPay", type_="plain", channel="generic", media_url=None, media_caption=None):
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
    print(response.text)