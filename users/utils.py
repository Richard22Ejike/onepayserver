import random

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail

from users.models import User, OneTimePassword


def GenerateOtp():
    otp = ""
    for i in range(6):
        otp += str(random.randint(1, 9))
    return otp


def send_email_to_user(email, otpCode):
    Subject = "One time Passcode for email Verification"
    otp_code = GenerateOtp()
    print(otp_code)
    user = User.objects.get(email=email)
    current_site = 'myAuth.com'
    email_body = f"hi {user.first_name} thanks for  signing up your \n one time token {otpCode}"
    send_mail(Subject, email_body, 'settings.EMAIL_HOST_USER', ['richard.ekene22@outlook.com'])
    from_email = settings.DEFAULT_FROM_EMAIL

    OneTimePassword.objects.create(user=user, code=otp_code)
    # send_email = EmailMessage(subject=Subject, body=email_body, from_email=from_email, to=[email])
    # send_email.send(fail_silently=True)
