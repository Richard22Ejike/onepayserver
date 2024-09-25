import os
import random
import smtplib
import onesignal
import string
from datetime import timedelta, datetime
from decouple import config
import requests
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from onesignal.api.default_api import DefaultApi
from onesignal.model.notification import Notification
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.contrib.auth import authenticate
import json
import hmac
import hashlib

from transactions.models import Transaction, Notifications
from .keys import secret_key
from .serializers import UserSerializer
from .models import User, OneTimePassword, OneTimeOtp
from .utils import send_email_to_user, GenerateOtp, send_sms
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
configuration = onesignal.Configuration(
    app_key="56618190-490a-4dc6-af2e-71ea67697f99",
    user_key="MjczMDdjYzUtM2FkMy00Y2JhLThjY2QtMTEyNGZhNTdjZDYw"
)

@api_view(['GET'])
def getroutes(request):
    routes = [
        {
            'Endpoint': '/notes/',
            'method': 'GET',
            'body': None,
            'description': 'Return all Users'
        },
        {
            'Endpoint': '/notes/id/',
            'method': 'GET',
            'body': None,
            'description': 'Return one Users'
        },
        {
            'Endpoint': '/notes/create/',
            'method': 'PUT',
            'body': {'body': ""},
            'description': 'Creates an exiting note with data sent in'
        },
        {
            'Endpoint': '/notes/id/update/',
            'method': 'PUT',
            'body': {'body': ""},
            'description': 'Creates an exiting note with data sent in'
        },
        {
            'Endpoint': '/users/id/delete/',
            'method': 'DELETE',
            'body': None,
            'description': 'Deletes user accounts'
        },
    ]
    return Response(routes)


@api_view(['GET'])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def addUsers(request):
    data = [
    {
        "id": 145,
        "password": "pbkdf2_sha256$600000$R63OvhatyRl2Cd1YuQmxaI$LGeU84YLtn91NHUZg22j1q/UFGxGtuH2c3V5vbESuuc=",
        "last_login": None,
        "username": "",
        "email": "ekene@mail.com",
        "first_name": "richard",
        "last_name": "ekeve",
        "phone_number": "09055555549",
        "image": "",
        "is_staff": False,
        "is_superuser": False,
        "is_active": False,
        "is_verified": False,
        "status": False,
        "customer_id": "aklbtmcc1v98o57ot",
        "account_id": "p7v49tstxphkm102x",
        "organization_id": "",
        "customer_type": "Personal",
        "bvn": "213278980998",
        "account_number": "2201302678",
        "escrow_fund": 0.0,
        "bank_name": "GTBank",
        "updated": "2024-07-19T19:57:20.996714Z",
        "created": "2024-07-16T16:18:02.930931Z",
        "bank_pin": "555555",
        "balance": 2055000.0,
        "device_id": "da09401e-c403-49f7-a6fe-bfa58aacb326",
        "street": "",
        "city": "",
        "state": "",
        "country": "",
        "postal_code": "",
        "access_token": "",
        "refresh_token": "",
        "notification_number": 0,
        "kyc_tier": 0,
        "groups": [],
        "user_permissions": []
    },
    {
        "id": 144,
        "password": "pbkdf2_sha256$600000$MFQDfO4rnPzKJN5baYPmPB$DnkeHGAyRJPXvKsFy6VpbRzvhLzURyLVet1jvSb2+38=",
        "last_login": None,
        "username": "",
        "email": "richard.ekene22@oulook.com",
        "first_name": "richard",
        "last_name": "ejike",
        "phone_number": "08055444489",
        "image": "",
        "is_staff": False,
        "is_superuser": False,
        "is_active": False,
        "is_verified": False,
        "status": False,
        "customer_id": "ubfhbks1axy4uy7y1",
        "account_id": "nt9kpdi28ynndkhfi",
        "organization_id": "",
        "customer_type": "Personal",
        "bvn": "2201309224",
        "account_number": "2201302456",
        "escrow_fund": 0.0,
        "bank_name": "GTBank",
        "updated": "2024-07-27T08:18:40.010371Z",
        "created": "2024-07-16T15:31:14.502190Z",
        "bank_pin": "555555",
        "balance": 1945000.0,
        "device_id": "e312410a-f6d5-4f95-b177-c0c2204edbc0",
        "street": "",
        "city": "",
        "state": "",
        "country": "",
        "postal_code": "",
        "access_token": "",
        "refresh_token": "",
        "notification_number": 0,
        "kyc_tier": 0,
        "groups": [],
        "user_permissions": []
    },
    {
        "id": 146,
        "password": "pbkdf2_sha256$600000$0AohaqTz5val3xIab1AyYg$2rWN5P/H7v+od6Pz3AZPD2wjz86SPQdRi9kaRVKsBjM=",
        "last_login": None,
        "username": "",
        "email": "richard.ekene22@outlook.co",
        "first_name": "richard",
        "last_name": "Ejike",
        "phone_number": "09055444488",
        "image": "",
        "is_staff": False,
        "is_superuser": False,
        "is_active": False,
        "is_verified": False,
        "status": False,
        "customer_id": "GTBT6JB3K",
        "account_id": "qc2tpbtwkris8jeys",
        "organization_id": "",
        "customer_type": "Personal",
        "bvn": "22398644894",
        "account_number": "0714152896",
        "escrow_fund": 0.0,
        "bank_name": "GTBank",
        "updated": "2024-08-14T16:34:48.525901Z",
        "created": "2024-08-14T16:34:48.525901Z",
        "bank_pin": "555555",
        "balance": 0.0,
        "device_id": "",
        "street": "",
        "city": "",
        "state": "",
        "country": "",
        "postal_code": "",
        "access_token": "",
        "refresh_token": "",
        "notification_number": 0,
        "kyc_tier": 0,
        "groups": [],
        "user_permissions": []
    },
    {
        "id": 147,
        "password": "pbkdf2_sha256$600000$nTyilMYPZk1Ak2ZJG93DDI$d3HSv7uRkOOSIXMDYHXSnSNCtBfsOgq3JKFH/xoiCmY=",
        "last_login": None,
        "username": "",
        "email": "richard.ekene22@outlook.c",
        "first_name": "richard",
        "last_name": "Ejike",
        "phone_number": "09055444480",
        "image": "",
        "is_staff": False,
        "is_superuser": False,
        "is_active": False,
        "is_verified": False,
        "status": False,
        "customer_id": "GTBT6JB3K",
        "account_id": "rkuhuef7g3uuwofbw",
        "organization_id": "",
        "customer_type": "Personal",
        "bvn": "22398644800",
        "account_number": "0714152896",
        "escrow_fund": 0.0,
        "bank_name": "GTBank",
        "updated": "2024-08-14T16:48:56.445999Z",
        "created": "2024-08-14T16:48:56.445999Z",
        "bank_pin": "555555",
        "balance": 0.0,
        "device_id": "",
        "street": "",
        "city": "",
        "state": "",
        "country": "",
        "postal_code": "",
        "access_token": "",
        "refresh_token": "",
        "notification_number": 0,
        "kyc_tier": 0,
        "groups": [],
        "user_permissions": []
    },
    {
        "id": 148,
        "password": "pbkdf2_sha256$600000$7qMDojYLEswsial4E4gUWX$hHskGFvLPgxcAtTEy24DhuD4/xkLVRhWQ4McG7MN+Yo=",
        "last_login": None,
        "username": "",
        "email": "richard.ekene22@outlook.com",
        "first_name": "Example",
        "last_name": "Ejike",
        "phone_number": "09055444489",
        "image": "",
        "is_staff": False,
        "is_superuser": False,
        "is_active": False,
        "is_verified": False,
        "status": False,
        "customer_id": "FLW-f75719ff079f4b7684fe7e2238829771",
        "account_id": "vcr4btssh2px4j4nz",
        "organization_id": "",
        "customer_type": "personal",
        "bvn": "22398644895",
        "account_number": "8548510800",
        "escrow_fund": 0.0,
        "bank_name": "WEMA BANK",
        "updated": "2024-09-23T14:50:28.505760Z",
        "created": "2024-09-23T14:50:28.505760Z",
        "bank_pin": "555555",
        "balance": 0.0,
        "device_id": "",
        "street": "",
        "city": "",
        "state": "",
        "country": "",
        "postal_code": "",
        "access_token": "",
        "refresh_token": "",
        "notification_number": 0,
        "kyc_tier": 0,
        "groups": [],
        "user_permissions": []
    }
]

    added_users = []
    for user_data in data:
        serializer = UserSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            added_users.append(user)
        else:
            print(serializer.errors)

    return Response({"message": "Users added successfully"})


@api_view(['GET'])
def getUser(request, pk):
    user = User.objects.get(account_number=pk)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)


def generate_random_id(length, prefix=''):
    characters = string.ascii_lowercase + string.digits
    random_id = ''.join(random.choice(characters) for _ in range(length - len(prefix)))
    return prefix + random_id


@api_view(['POST'])
def createUser(request):
    try:
        data = request.data

        # Fetch Flutterwave secret key from environment variables
        secret_key = config('SECRETKEY')  # Using the environment variable SECRETKEY
        print(secret_key)
        print(secret_key)
        # Convert DOB from dd/MM/yyyy to MM/dd/yyyy format
        dob_str = data['dob']
        try:
            dob_obj = datetime.strptime(dob_str, '%d/%m/%Y')
            dob = dob_obj.strftime('%m/%d/%Y')
        except ValueError:
            return Response({
                'error': 'Invalid date format for DOB. Please use dd/MM/yyyy format.'},
                status=status.HTTP_400_BAD_REQUEST)

        # Check if the user already exists locally
        existing_user = User.objects.filter(
            Q(phone_number=data['phone_number']) | Q(email=data['email']) | Q(bvn=data['bvn'])
        ).first()

        if existing_user:
            matched_fields = []
            if existing_user.phone_number == data['phone_number']:
                matched_fields.append(f"phone_number: {data['phone_number']}")
            if existing_user.email == data['email']:
                matched_fields.append(f"email: {data['email']}")
            if existing_user.bvn == data['bvn']:
                matched_fields.append(f"bvn: {data['bvn']}")
            matched_fields_str = ", ".join(matched_fields)
            return Response({
                'error': f'User with the provided phone number, email, or BVN already exists. Matches: {matched_fields_str}'},
                status=status.HTTP_400_BAD_REQUEST)

        # Call to register the virtual account using Flutterwave API
        payload = {
            "email": data['email'],
            "is_permanent": True,
            "bvn": data['bvn'],
            "tx_ref": generate_random_id(17),  # You can generate or pass a unique reference
            "phonenumber": data['phone_number'],
            "firstname": data['first_name'],
            "lastname": data['last_name'],
            "narration": "Richard Ejike"  # You can modify the narration as needed
        }

        flutterwave_response = requests.post(
            'https://api.flutterwave.com/v3/virtual-account-numbers',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {secret_key}'  # Using the secret key from the environment variable
            },
            json=payload
        )

        if flutterwave_response.status_code != 200:
            return Response({'error': f'{flutterwave_response.json()}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        flutterwave_data = flutterwave_response.json()


        # Create new user
        user = User.objects.create_user(
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            password=data['password'],
            email=data['email'],
            customer_type=data['customer_type'],
            bvn=data['bvn'],
            bank_name=flutterwave_data['data']['bank_name'],
            bank_pin='555555',
            account_id=generate_random_id(17),
            account_number=flutterwave_data['data']['account_number'],
            customer_id=flutterwave_data['data']['flw_ref'],
        )

        # Generate or get existing token for the user
        token, created = Token.objects.get_or_create(user=user)

        user_tokens = user.tokens()
        user.access_token = str(user_tokens.get('access'))
        user.refresh_token = str(user_tokens.get('refresh'))

        serializer = UserSerializer(user, many=False)
        return Response({
            'user': serializer.data,
            'token': token.key,
            'access_token': str(user_tokens.get('access')),
            'refresh_token': str(user_tokens.get('refresh')),
            'virtual_account_data': flutterwave_data['data']
        })

    except KeyError as e:
        error_message = f"Missing required field: {str(e)}"
        return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

    except IntegrityError as e:
        error_message = str(e)
        if 'phone_number' in error_message:
            return Response({'error': "Phone number already exists."}, status=status.HTTP_400_BAD_REQUEST)
        elif 'email' in error_message:
            return Response({'error': "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)
        elif 'bvn' in error_message:
            return Response({'error': "BVN already exists."}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        error_message = str(e)
        return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def SignInUser(request):
    data = request.data
    phone_number = data.get('phone_number')  # Assuming the phone_number is provided in the request data
    password = data.get('password')
    user = User.objects.get(phone_number=phone_number)

    # Authenticate user
    if not check_password(password, user.password):
        return Response({'message': 'bad credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token, _ = Token.objects.get_or_create(user=user)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    user_tokens = user.tokens()
    user.device_id = data.get('device_id')
    user.save()
    user.access_token = str(user_tokens.get('access'))
    user.refresh_token = str(user_tokens.get('refresh'))

    serializer = UserSerializer(user, many=False)
    print(serializer.data)
    return Response({'user': serializer.data,
                     })


@api_view(['POST'])
def forget_password(request):
    print('email')
    data = request.data
    email = data.get('email')
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Generate an OTP (One-Time Passcode)
    otp_code = GenerateOtp()
    print(otp_code)
    subject = "One time Passcode for email Verification"
    email_body = f"<strong>hi {user.first_name} thanks for Using OnePlug  your \n one time token {otp_code} </strong>"

    try:
        # Try to create a new OTP entry for the user
        OneTimePassword.objects.create(user=user, code=otp_code)
    except IntegrityError:
        # If an entry already exists, update the existing entry with the new OTP
        otp_entry = OneTimePassword.objects.get(user=user)
        otp_entry.code = otp_code
        otp_entry.save()

    # # Send the OTP to the user via email
    send_email_to_user(email, email_body, subject)

    return Response({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def reset_password(request):
    data = request.data
    email = data.get('email')
    otp = data.get('otp')  # OTP entered by the user
    new_password = data.get('new_password')
    print(email)
    print(otp)  # OTP entered by the user
    print(new_password)

    # Check if a user with the provided email exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the OTP exists and is not expired
    try:
        otp_obj = OneTimePassword.objects.get(user=user, code=otp)
    except OneTimePassword.DoesNotExist:
        return Response({'message': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the OTP has expired (e.g., expires after 5 minutes)
    if otp_obj.created_at < timezone.now() - timedelta(minutes=5):
        otp_obj.delete()
        return Response({'message': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
    # Update the user's password
    user.set_password(new_password)
    user.save()

    # Delete the OTP object after successful password reset
    otp_obj.delete()

    return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def send_otp_to_email(request):
    data = request.data
    email = data.get('email')

    # Check if a user with the provided email exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Generate an OTP (One-Time Passcode)
    otp_code = GenerateOtp()
    subject = "One time Passcode for email Verification"
    email_body = f"<strong>hi {user.first_name} thanks for Using OnePlug  your \n one time token {otp_code} </strong>"

    try:
        # Try to create a new OTP entry for the user
        OneTimePassword.objects.create(user=user, code=otp_code)
    except IntegrityError:
        # If an entry already exists, update the existing entry with the new OTP
        otp_entry = OneTimePassword.objects.get(user=user)
        otp_entry.code = otp_code
        otp_entry.save()

    # # Send the OTP to the user via email
    send_email_to_user(email, email_body, subject)

    return Response({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def send_otp_to_phone(request):
    data = request.data
    phone_number = data.get('phone_number')

    # Generate an OTP (One-Time Passcode)
    otp_code = GenerateOtp()

    # Send the OTP via SMS
    send_sms(sms=f'Dear Customer, ${otp_code} is the One Time Password ( OTP ) for your login.', to=phone_number,
             api_key='TLkdeoFa2SDh2gElzd2AG7r0Lua4KDigbS7Q9EPm9Vt5VO6zdLDWT7a5k0DaU7')

    # Update the OTP if the phone number already exists, otherwise create a new entry
    OneTimeOtp.objects.update_or_create(
        key=phone_number,
        defaults={'code': otp_code, 'created_at': timezone.now()}
    )

    print(otp_code)

    return Response({'message': 'OTP sent to your phone'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def otp_verified(request):
    otpcode = request.data.get('otp')
    key = request.data.get('key')
    try:
        otp_code_objs = OneTimeOtp.objects.filter(key=key)

        if not otp_code_objs.exists():
            return Response({
                'message': 'passcode not provided'
            }, status=status.HTTP_404_NOT_FOUND)

        for otp_code_obj in otp_code_objs:
            otp = otp_code_obj.code
            created_time = otp_code_obj.created_at  # assuming you have a created_at field

            # Check if the OTP was created within the last 10 minutes
            if timezone.now() - created_time > timedelta(minutes=10):
                return Response({
                    'message': 'OTP code has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            if otp == otpcode:
                return Response({
                    'message': 'account phone number verified successfully'
                }, status=status.HTTP_200_OK)

        return Response({
            'message': 'code is invalid'
        }, status=status.HTTP_400_BAD_REQUEST)

    except OneTimeOtp.DoesNotExist:
        return Response({'message': "passcode not provided"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def password_reset_otp_verified(request):
    otpcode = request.data.get('otp')
    email = request.data.get('email')
    print(email)
    try:
        print(otpcode)
        user_code_obj = OneTimePassword.objects.get(code=otpcode)
        print(email)
        user = user_code_obj.user
        print(user.email)
        if user.email == email:
            return Response({
                'message': 'reset password otp verified successfully'
            }, status=status.HTTP_200_OK)
        return Response({
            'message': 'code is invalid'
        }, status=status.HTTP_204_NO_CONTENT)
    except OneTimePassword.DoesNotExist:
        return Response({'message': "passcode not in database"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
def updateUser(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)
    key = data.get('key', '')

    if key == '1':
        user.first_name = data.get('firstName', user.first_name)
        user.last_name = data.get('lastName', user.last_name)
        user.image = data.get('image', user.image)
    else:
        user.email = data.get('email', user.email)

    serializer = UserSerializer(user, data=data, partial=True)  # Use partial to allow partial updates

    if serializer.is_valid():
        user.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def updateUserToKYC1(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)

    url = f"https://api.blochq.io/v1/customers/upgrade/t1/{user.customer_id}"

    payload = {
        "address": {
            "street": data['street'],
            "city": data['city'],
            "state": data['state'],
            "country": data['country'],
            "postal_code": data['postal_code']
        },
        "place_of_birth": data['place_of_birth'],
        "dob": data['dob'],
        "gender": data['gender'],
        "country": data['country'],
        "image": data['image']
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {secret_key}"
    }

    response = requests.put(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(response.json())
        # If the request was not successful, return an error response
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200:
        print(response.json())
        user.kyc_tier = 1
        user.save()
        serializer = UserSerializer(user, many=False)

        # Check if all required fields are present

        # Validate the serializer
        return Response({
            'user': serializer.data,
        })


@api_view(['PUT'])
def updateUserToKYC2(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)
    serializer = UserSerializer(user, data=data)

    # Check if all required fields are present
    required_fields = ['means_of_id', 'image', ]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return Response({'error': f'Missing required fields: {", ".join(missing_fields)}'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Validate the serializer
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def updateUserToKYC2v2(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)
    serializer = UserSerializer(user, data=data)

    url = f"https://api.blochq.io/v1/customers/upgrade/t2/v2/{user.customer_id}"

    payload = {
        "means_of_id": data['means_of_id'],
        "image": data['image'],
        "document_number": data['document_number']
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {secret_key}"
    }

    response = requests.put(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(response.json())
        # If the request was not successful, return an error response
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200:
        print(response.json())
        user.kyc_tier = 2
        user.save()
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def updateUserToKYC3(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)
    serializer = UserSerializer(user, data=data)

    url = f"https://api.blochq.io/v1/customers/upgrade/t3/{user.customer_id}"

    payload = {"image": data['image']}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {secret_key}"
    }

    response = requests.put(url, json=payload, headers=headers)

    if response.status_code != 200:
        print(response.json())
        # If the request was not successful, return an error response
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200:
        print(response.json())
        user.kyc_tier = 3
        user.save()
        # Validate the serializer
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def deleteUser(request, pk):
    user = User.objects.get(id=pk)
    user.delete()
    return Response('User was deleted')


# Create your views here.
@api_view(['PUT'])
def ChangePin(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)
    serializer = UserSerializer(user, data=data)
    required_fields = ['old_pin', 'new_pin']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return Response({'error': f'Missing required fields: {", ".join(missing_fields)}'},
                        status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(['PUT'])
def SetPin(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)
    user.bank_pin = data.get('new_pin')
    user.save()
    serializer = UserSerializer(user, many=False)

    print(serializer.data)
    return Response(serializer.data)


@csrf_exempt
@api_view(['POST'])
def webhook_listener(request):
    print('connected')
    print(f"Request Headers: {request.headers}")
    # Retrieve the Flutterwave secret hash from the environment variables
    secret_hash = config("FLW_SECRET_HASH")
    print(f"Secret Hash: {secret_hash}")

    # Retrieve the 'verifi-hash' signature from the request headers
    signature = request.headers.get("Verif-Hash")
    print(f"Received Signature: {signature}")

    # Check if the signature is valid
    if signature is None or (signature != secret_hash):
        # If the request isn't from Flutterwave, return a 401 Unauthorized response
        return Response(status=401)

    # Parse the request payload
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({'error': 'Invalid payload'}, status=400)

    # It's a good idea to log the received events
    log_event(payload)
    print('connected')
    print(payload)
    # Retrieve the event type from the payload
    event = payload.get("event")
    data = payload.get("data")
    print('connected')
    # Handle different event types
    if event == 'charge.completed':
        handle_charge_completed(data)
    elif event == 'transfer.success':
        handle_transfer_success(data)
    elif event == 'transfer.failed':
        handle_transfer_failed(data)
    else:
        # Unhandled event type
        return Response({'error': 'Unhandled event'}, status=400)
    print('connected')
    # Return a success response to Flutterwave
    return Response(status=200)


def log_event(payload):
    # Log the event for debugging or future reference
    print(f"Received webhook payload: {payload}")


def handle_charge_completed(data):
    # Process a successful charge (e.g., payment)
    print(f"Charge Completed: {data}")

    # Extract phone number from the customer data
    customer_phone = data.get("customer", {}).get("phone_number")
    amount = data.get("charged_amount")

    if customer_phone and amount:
        try:
            # Find the user with the given phone number
            user = User.objects.get(phone_number=customer_phone)

            # Add the charged amount to the user's account balance
            user.balance += amount
            user.save()
            print(f"Updated {user.first_name}'s balance to {user.balance}")

            # Send a notification to the user using OneSignal
            send_notification(user, amount, data)

            # Log the notification in the database
            Notifications.objects.create(
                device_id=user.device_id,
                customer_id=user.customer_id,
                topic='Charge Completed',
                message=f'You have received {amount} NGN from {user.first_name}.'
            )
        except User.DoesNotExist:
            print(f"User with phone number {customer_phone} does not exist.")
    else:
        print("Phone number or amount missing in the webhook data.")


def send_notification(receiving_user, amount, data):
    # OneSignal Configuration
 # Ensure this is set in your Django settings

    # Initialize the OneSignal API client
    with onesignal.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = DefaultApi(api_client)
        notification = Notification(
            app_id='56618190-490a-4dc6-af2e-71ea67697f99',
            include_player_ids=[receiving_user.device_id],  # Make sure the user has a device ID
            contents={"en": f'You have received {amount} NGN from {data.get("narration", "someone")}.'}
        )

        try:
            # Send notification
            api_response = api_instance.create_notification(notification)
            print(api_response)
        except onesignal.ApiException as e:
            print(f"Exception when calling DefaultApi->create_notification: {e}")


def handle_transfer_success(data):
    # Process a successful transfer
    print(f"Transfer Successful: {data}")
    # You can save the transaction to your database or perform other actions here


def handle_transfer_failed(data):
    # Process a failed transfer
    print(f"Transfer Failed: {data}")
    # You can notify the user or log the failure