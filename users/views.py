import os
import random
import smtplib
import onesignal
import string
from datetime import timedelta, datetime
from decouple import config
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.contrib.auth import authenticate
import json
import hmac
import hashlib

from nearme.serializers import NearMeProductSerializer
from transactions.models import Transaction, Notifications, PaymentDetails
from transactions.serializers import EscrowSerializer, PaymentLinkSerializer, PaymentDetailsSerializer, \
    TransactionSerializer, PayBillSerializer, CardSerializer
from .serializers import UserSerializer
from .models import User, OneTimePassword, OneTimeOtp
from .utils import send_email_to_user, GenerateOtp, send_sms, send_otp, send_fcm_notification
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password

configuration = onesignal.Configuration(
    app_key=config('APP_KEY'),
    api_key=config('API_KEY'),
    user_key=config('USER_KEY')
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
    print('good3')
    serializer = UserSerializer(users, many=True)
    print(serializer.data)
    return Response(serializer.data)


@api_view(['GET'])
def addUsers(request):
    card = [
  {
    "card_id": "card001",
    "account_id": "acc001",
    "customer_id": "cust001",
    "name": "John Visa",
    "brand": "Visa",
    "balance": 12000.0,
    "card_number": "4111111111111111",
    "cvv": "123",
    "expiry_month": "12",
    "expiry_year": "2026",
    "email": "john@example.com",
    "pin": "1234",
    "currency": "NGN",
    "tx_ref": "TXREF001"
  },
  {
    "card_id": "card002",
    "account_id": "acc002",
    "customer_id": "cust002",
    "name": "Jane MasterCard",
    "brand": "MasterCard",
    "balance": 7500.0,
    "card_number": "5500000000000004",
    "cvv": "456",
    "expiry_month": "10",
    "expiry_year": "2025",
    "email": "jane@example.com",
    "pin": "5678",
    "currency": "NGN",
    "tx_ref": "TXREF002"
  },
  {
    "card_id": "card003",
    "account_id": "acc003",
    "customer_id": "cust003",
    "name": "Alice Verve",
    "brand": "Verve",
    "balance": 3000.0,
    "card_number": "5060990000000000",
    "cvv": "789",
    "expiry_month": "08",
    "expiry_year": "2024",
    "email": "alice@example.com",
    "pin": "0000",
    "currency": "NGN",
    "tx_ref": "TXREF003"
  }
]
    paybills = [
  {
    "name": "Electricity Bill",
    "customer_id": "cust001",
    "account_id": "acc001",
    "amount": 1500.50,
    "operator_id": "IKEDC",
    "order_id": "ORD001",
    "meter_type": "Prepaid",
    "device_number": "1234567890",
    "status": "Successful",
    "remark": "Power purchase",
    "order_type": "Electricity",
    "service_type": "Utility"
  },
  {
    "name": "DSTV Subscription",
    "customer_id": "cust002",
    "account_id": "acc002",
    "amount": 6800.00,
    "operator_id": "DSTV",
    "order_id": "ORD002",
    "meter_type": "N/A",
    "device_number": "smart1234",
    "status": "Pending",
    "remark": "Monthly DSTV",
    "order_type": "Cable",
    "service_type": "Entertainment"
  },
  {
    "name": "Airtime Recharge",
    "customer_id": "cust003",
    "account_id": "acc003",
    "amount": 500.00,
    "operator_id": "MTN",
    "order_id": "ORD003",
    "meter_type": "N/A",
    "device_number": "08012345678",
    "status": "Successful",
    "remark": "Top-up",
    "order_type": "Airtime",
    "service_type": "Mobile"
  }
]
    Transactions = [
      {
        "sender_account_number": "1234567890",
        "bank": "First Bank",
        "bank_code": "011",
        "reference": "TXN123456A",
        "account_id": "acc001",
        "customer_id": "cust001",
        "account_number": "9876543210",
        "amount": 5000,
        "currency": "NGN",
        "narration": "Transfer for goods",
        "transaction_fee": 50,
        "user_balance": 9500,
        "receiver_name": "John Doe"
      },
      {
        "sender_account_number": "1234567891",
        "bank": "GTBank",
        "bank_code": "058",
        "reference": "TXN123456B",
        "account_id": "acc002",
        "customer_id": "cust002",
        "account_number": "9876543211",
        "amount": 10000,
        "currency": "NGN",
        "narration": "Transfer for rent",
        "transaction_fee": 100,
        "user_balance": 20000,
        "receiver_name": "Jane Smith"
      },
      {
        "sender_account_number": "1234567892",
        "bank": "Access Bank",
        "bank_code": "044",
        "reference": "TXN123456C",
        "account_id": "acc003",
        "customer_id": "cust003",
        "account_number": "9876543212",
        "amount": 7500,
        "currency": "NGN",
        "narration": "Loan repayment",
        "transaction_fee": 75,
        "user_balance": 5000,
        "receiver_name": "Alice Brown"
      }
    ]
    paymentdetails = [
  {
    "customer_id": "cust101",
    "name": "Daniel Okoro",
    "email": "daniel.okoro@example.com",
    "phone_number": 8012345678,
    "link": 1,
    "narration": "Course enrollment",
    "amount": 10000,
    "payment_type": "Card"
  },
  {
    "customer_id": "cust102",
    "name": "Ifeoma Eze",
    "email": "ifeoma.eze@example.com",
    "phone_number": 8098765432,
    "link": 2,
    "narration": "E-book payment",
    "amount": 2500,
    "payment_type": "USSD"
  },
  {
    "customer_id": "cust103",
    "name": "Mike Ajayi",
    "email": "mike.ajayi@example.com",
    "phone_number": 8081122334,
    "link": 3,
    "narration": "Freelance job payment",
    "amount": 50000,
    "payment_type": "Bank Transfer"
  }
]
    Escrow = [
      {
        "account_id": "acc201",
        "customer_id": "cust201",
        "escrow_description": "Web design project",
        "escrow_name": "Website Redesign",
        "escrow_Status": "Pending",
        "payment_type": "Card",
        "role": "Client",
        "role_paying": "Client",
        "estimated_days": "5",
        "number_milestone": "2",
        "milestone": "Initial deposit",
        "reference": "ESCROW001",
        "sender_name": "Chinedu Obasi",
        "receiver_email": "uche@example.com",
        "receiver_id": 501,
        "currency": "NGN",
        "link_url": "https://escrow.example.com/escrow001",
        "make_payment": True,
        "accepted": True,
        "answered": True,
        "amount": 70000,
        "transaction_fee": 1000,
        "dispute": "",
        "is_disabled": False
      },
      {
        "account_id": "acc202",
        "customer_id": "cust202",
        "escrow_description": "App development project",
        "escrow_name": "Mobile App Phase 1",
        "escrow_Status": "Completed",
        "payment_type": "Bank Transfer",
        "role": "Developer",
        "role_paying": "Client",
        "estimated_days": "14",
        "number_milestone": "3",
        "milestone": "Final milestone",
        "reference": "ESCROW002",
        "sender_name": "Amina Bello",
        "receiver_email": "dev@example.com",
        "receiver_id": 502,
        "currency": "NGN",
        "link_url": "https://escrow.example.com/escrow002",
        "make_payment": True,
        "accepted": True,
        "answered": True,
        "amount": 150000,
        "transaction_fee": 2500,
        "dispute": "None",
        "is_disabled": False
      },
      {
        "account_id": "acc203",
        "customer_id": "cust203",
        "escrow_description": "Logo Design",
        "escrow_name": "Design Contract",
        "escrow_Status": "Disputed",
        "payment_type": "USSD",
        "role": "Client",
        "role_paying": "Client",
        "estimated_days": "3",
        "number_milestone": "1",
        "milestone": "Single delivery",
        "reference": "ESCROW003",
        "sender_name": "Tunde Bakare",
        "receiver_email": "logoartist@example.com",
        "receiver_id": 503,
        "currency": "NGN",
        "link_url": "https://escrow.example.com/escrow003",
        "make_payment": True,
        "accepted": False,
        "answered": True,
        "amount": 20000,
        "transaction_fee": 300,
        "dispute": "Late delivery",
        "is_disabled": False
      }
    ]

    paymentlink = [
          {
        "account_id": "acc101",
        "customer_id": "cust101",
        "organization_id": "org001",
        "environment": "live",
        "description": "Payment for online course",
        "name": "Online Course Fee",
        "link_id": "plink001",
        "country": "NG",
        "currency": "NGN",
        "link_url": "https://pay.example.com/plink001",
        "amount": 10000,
        "is_disabled": False
      },
      {
        "account_id": "acc102",
        "customer_id": "cust102",
        "organization_id": "org002",
        "environment": "test",
        "description": "E-book purchase",
        "name": "E-book Store",
        "link_id": "plink002",
        "country": "NG",
        "currency": "NGN",
        "link_url": "https://pay.example.com/plink002",
        "amount": 2500,
        "is_disabled": False
      },
      {
        "account_id": "acc103",
        "customer_id": "cust103",
        "organization_id": "org003",
        "environment": "live",
        "description": "Freelance service payment",
        "name": "Freelance Invoice",
        "link_id": "plink003",
        "country": "NG",
        "currency": "NGN",
        "link_url": "https://pay.example.com/plink003",
        "amount": 50000,
        "is_disabled": True
          }
        ]
    Nearme = [
      {
        "product_id": "prod001",
        "product_category": "Electronics",
        "product_name": "Samsung TV",
        "product_images": ["tv_front.jpg", "tv_side.jpg"],
        "customer_id": "cust301",
        "video": "tv_demo.mp4",
        "title": "43 inch Smart TV",
        "location": "Lagos",
        "lat": "6.5244",
        "long": "3.3792",
        "brand": "Samsung",
        "type": "LED",
        "condition": "New",
        "description": "Smart TV with Wi-Fi and HDMI",
        "price": "250000",
        "delivery": "Available",
        "status": "Available",
        "chat_id": [],
        "seller_name": "Emeka Obi",
        "seller_image": "emeka.jpg",
        "seller_phone_number": "08031234567",
        "seller_email": "emeka@example.com",
        "seller_id": "seller001"
      },
      {
        "product_id": "prod002",
        "product_category": "Fashion",
        "product_name": "Leather Handbag",
        "product_images": ["bag1.jpg", "bag2.jpg"],
        "customer_id": "cust302",
        "video": "",
        "title": "Ladies Leather Bag",
        "location": "Abuja",
        "lat": "9.0578",
        "long": "7.4951",
        "brand": "Gucci",
        "type": "Handbag",
        "condition": "New",
        "description": "Stylish brown leather handbag",
        "price": "55000",
        "delivery": "Pickup only",
        "status": "Available",
        "chat_id": [],
        "seller_name": "Ada Nwoke",
        "seller_image": "ada.jpg",
        "seller_phone_number": "08123456789",
        "seller_email": "ada@example.com",
        "seller_id": "seller002"
      },
      {
        "product_id": "prod003",
        "product_category": "Automobile",
        "product_name": "Used Toyota Corolla",
        "product_images": ["car_front.jpg", "car_interior.jpg"],
        "customer_id": "cust303",
        "video": "car_tour.mp4",
        "title": "2010 Toyota Corolla",
        "location": "Port Harcourt",
        "lat": "4.8156",
        "long": "7.0498",
        "brand": "Toyota",
        "type": "Sedan",
        "condition": "Used",
        "description": "Well maintained, 4 doors, automatic",
        "price": "1800000",
        "delivery": "Not Available",
        "status": "Sold",
        "chat_id": [],
        "seller_name": "Ibrahim Musa",
        "seller_image": "ibrahim.jpg",
        "seller_phone_number": "08099887766",
        "seller_email": "ibrahim@example.com",
        "seller_id": "seller003"
      }
    ]


    data = [
        {'id': 6,
         'password': 'pbkdf2_sha256$600000$gYkImkwZuuSLzyNQLWJIIe$77BhpJwZjgiv53sdoJJvN///suomDaZNLMs3b1CReIc=',
         'last_login': None,
         'username': 'joshua johnson',
         'email': 'am.joshuajohnson@gmail.com',
         'first_name': 'Joshua',
         'last_name': 'Johnson',
         'phone_number': '07034534116',
         'image': 'https://res.cloudinary.com/donpd3pem/image/upload/v1729853868/JGCP95921729800783244239920/qlmcli9obqecxzt8tbnf.jpg',
         'is_staff': False,
         'is_superuser': False,
         'is_active': False,
         'is_verified': False,
         'status': False,
         'customer_id': 'JGCP95921729800783244239920',
         'account_id': '5dijuhwqw3mewbt7n',
         'organization_id': '5dijuhwqw',
         'customer_type': 'Personal',
         'bvn': '22167494876',
         'account_number': '9917158241',
         'escrow_fund': 0.0,
         'bank_name': 'Cashconnect Microfinance Bank',
         'updated': '2024-10-25T14:04:23.484552Z',
         'created': '2024-10-24T20:13:04.830740Z',
         'bank_pin': '555555',
         'balance': 2407.0,
         'device_id': '7cc8cb05-d486-4932-9a69-908e98a510f9',
         'street': '5dijuhwqw',
         'city': '5dijuhwqw',
         'state': '5dijuhwqw',
         'country': '5dijuhwqw',
         'postal_code': '5dijuhwqw',
         'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI5ODY1MzYzLCJp'
                         'YXQiOjE3Mjk4NjUwNjMsImp0aSI6IjM1ZDcxZTg5ZTIwMTRkZmZiNjdlOWY3NjkwNTgwNmJlIiwidXNlcl9pZCI6Nn0.'
                         'F1Pkp7FW_Uy_YHl5sjfpXDACdemCFBZnVmwNB2bOlnU',
         'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyOTk1MTQ2My'
                          'wiaWF0IjoxNzI5ODY1MDYzLCJqdGkiOiJiNDZmYTY4ZjVkMmY0NDUwYjIwZmJmYTJjNTY1OGZiNiIsInVzZXJfaWQiOj'
                          'Z9.jZitoxHraIeIyAMgAydRyXjR2rDjN7IHt-ExXdjZPGg',
         'notification_number': 0,
         'kyc_tier': 0,
         'groups': [],
         'date_of_birth': '1998/06/19',
         'user_permissions': []},
        {
            "id": 148,
            "password": "pbkdf2_sha256$600000$7qMDojYLEswsial4E4gUWX$hHskGFvLPgxcAtTEy24DhuD4/xkLVRhWQ4McG7MN+Yo=",
            "last_login": None,
            "username": "richard",
            "email": "richard.ekene22@outlook.com",
            "first_name": "Example",
            "last_name": "Ejike",
            "phone_number": "09055444489",
            "image": "richard",
            "is_staff": False,
            "is_superuser": False,
            "is_active": False,
            "is_verified": False,
            "status": False,
            "customer_id": "FLW-f75719ff079f4b7684fe7e22388296891",
            "account_id": "vcr4btssh2px4j4nz",
            "organization_id": "fgdfggadff",
            "customer_type": "personal",
            "bvn": "22398644895",
            "account_number": "8548510800",
            "escrow_fund": 0.0,
            "bank_name": "WEMA BANK",
            "updated": "2024-09-23T14:50:28.505760Z",
            "created": "2024-09-23T14:50:28.505760Z",
            "bank_pin": "555555",
            "balance": 0.0,
            "device_id": " gfdgf",
            "street": "dgs",
            "city": "gs",
            "state": "sg",
            "country": "sfg",
            "postal_code": "sfg",
            "access_token": "c xv",
            "refresh_token": " vvsvsfv",
            "notification_number": 0,
            "kyc_tier": 0,
            'date_of_birth': '1998/06/19',
            "groups": [],
            "user_permissions": []
        },
        {
            "id": 149,
            "password": "pbkdf2_sha256$600000$7qMDojYLEswsial4E4gUWX$hHskGFvLPgxcAtTEy24DhuD4/xkLVRhWQ4McG7MN+Yo=",
            "last_login": None,
            "username": "richard",
            "email": "richard.ekene@aun.edu.ng",
            "first_name": "Richard Ekene",
            "last_name": "Ejike",
            "phone_number": "09044444889",
            "image": "richard",
            "is_staff": False,
            "is_superuser": False,
            "is_active": False,
            "is_verified": False,
            "status": False,
            "customer_id": "FLW-f75719ff079f4b7684fe7e2238829771",
            "account_id": "vcr4btssh2px4j4nz",
            "organization_id": "fgdfggadff",
            "customer_type": "personal",
            "bvn": "22398644895",
            "account_number": "8548510800",
            "escrow_fund": 0.0,
            "bank_name": "WEMA BANK",
            "updated": "2024-09-23T14:50:28.505760Z",
            "created": "2024-09-23T14:50:28.505760Z",
            "bank_pin": "555555",
            "balance": 50000.0,
            "device_id": " gfdgf",
            "street": "dgs",
            "city": "gs",
            "state": "sg",
            "country": "sfg",
            "postal_code": "sfg",
            "access_token": "c xv",
            "refresh_token": " vvsvsfv",
            "notification_number": 0,
            "kyc_tier": 0,
            'date_of_birth': '1998/06/19',
            "groups": [],
            "user_permissions": []
        }
    ]
    data_vars = {
        "users": data,
        "cards": card,
        "paybills": paybills,
        "transactions": Transactions,
        # "paymentdetails": paymentdetails,
        "escrows": Escrow,
        "paymentlinks": paymentlink,
        'nearme': Nearme

    }

    serializers = {
        "users": UserSerializer,
        "cards": CardSerializer,
        "paybills": PayBillSerializer,
        "transactions": TransactionSerializer,
        # "paymentdetails": PaymentDetailsSerializer,
        "escrows": EscrowSerializer,
        "paymentlinks": PaymentLinkSerializer,
        "nearme": NearMeProductSerializer
    }

    # Create entries
    for key, items in data_vars.items():
        for item in items:
            serializer = serializers[key](data=item)
            if serializer.is_valid():
                serializer.save()
            else:
                print(f"Error in {key} data:", serializer.errors)

    return Response({'status': 'All data added successfully'})




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
            "narration": f"{data['first_name']},{data['last_name']}"  # You can modify the narration as needed
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
            date_of_birth=data['dob'],
            referral_code=generate_random_id(9)
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
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
    try:
        print('signing in')
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
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def SignInAdmin(request):
    try:
        data = request.data
        phone_number = data.get('phone_number')
        password = data.get('password')

        # Authenticate admin manually
        user = User.objects.filter(phone_number=phone_number).first()
        if password == 'oneplug22':  # Replace with real password check if needed
            serializer = UserSerializer(user)
            return Response({'user': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid phone number or password.'}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def forget_password(request):
    try:
        print('email')
        data = request.data
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate an OTP (One-Time Passcode)
        # otp_code = GenerateOtp()
        # print(otp_code)
        # subject = "One time Passcode for email Verification"
        # email_body = f"<strong>hi {user.first_name} thanks for Using OnePlug  your \n one time token {otp_code} </strong>"
        otp_response = send_otp(customer_email=email, medium=['email'], customer_phone='')

        if otp_response:
            # Extract the OTP for the 'email' medium
            otp_code = None
            for entry in otp_response:
                if entry['medium'] == 'email':
                    otp_code = entry['otp']
                    break

            try:
                # Try to create a new OTP entry for the user
                OneTimePassword.objects.create(user=user, code=otp_code)
            except IntegrityError:
                # If an entry already exists, update the existing entry with the new OTP
                otp_entry = OneTimePassword.objects.get(user=user)
                otp_entry.code = otp_code
                otp_entry.save()

        # # Send the OTP to the user via email
        # send_email_to_user(email, email_body, subject)

        return Response({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def reset_password(request):
    try:
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
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_otp_to_email(request):
    try:
        data = request.data
        email = data.get('email')

        # Check if a user with the provided email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate an OTP (One-Time Passcode)
        # otp_code = GenerateOtp()
        # subject = "One time Passcode for email Verification"
        # email_body = f"<strong>hi {user.first_name} thanks for Using OnePlug  your \n one time token {otp_code} </strong>"
        otp_response = send_otp(customer_email=email, medium=['email'], customer_phone='')
        print('two')

        if otp_response:
            # Extract the OTP for the 'email' medium
            otp_code = None
            for entry in otp_response:
                if entry['medium'] == 'email':
                    otp_code = entry['otp']
                    break

            try:
                # Try to create a new OTP entry for the user
                OneTimePassword.objects.create(user=user, code=otp_code)
            except IntegrityError:
                # If an entry already exists, update the existing entry with the new OTP
                otp_entry = OneTimePassword.objects.get(user=user)
                otp_entry.code = otp_code
                otp_entry.save()

        # # Send the OTP to the user via email
        # send_email_to_user(email, email_body, subject)

        return Response({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_otp_to_phone(request):
    try:
        data = request.data
        phone_number = data.get('phone_number')

        # Generate an OTP (One-Time Passcode)
        otp_code = GenerateOtp()

        # Send the OTP via SMS
        # send_sms(sms=f'Dear Customer, $ is the One Time Password ( OTP ) for your login.', to=phone_number,
        #          api_key=config('SECRET_SMS'))
        otp_response = send_otp(customer_email='', medium=['sms', 'whatsapp'], customer_phone=phone_number)

        if otp_response:
            # Extract the OTP for the 'email' medium
            otp_code = None
            for entry in otp_response:
                if entry['medium'] == 'sms' or entry['medium'] == 'whatsapp':
                    otp_code = entry['otp']
                    break

        # Update the OTP if the phone number already exists, otherwise create a new entry
        OneTimeOtp.objects.update_or_create(
            key=phone_number,
            defaults={'code': otp_code, 'created_at': timezone.now()}
        )

        print(otp_code)
        return Response({'message': 'OTP sent to your phone'}, status=status.HTTP_200_OK)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def updateUser(request, pk):
    try:
        data = request.data
        user = User.objects.get(customer_id=pk)
        key = data.get('key', '')

        # Update fields based on 'key' value
        if key == '1':
            user.first_name = data.get('firstName', user.first_name)
            user.last_name = data.get('lastName', user.last_name)
            user.image = data.get('image', user.image)
        else:
            # Update email and phone_number only if they are not null
            if data.get('email') is not None:
                user.email = data['email']
            if data.get('phone_number') is not None:
                user.phone_number = data['phone_number']

        # Prepare a dictionary of fields to pass to the serializer for validation
        update_data = {}
        if 'firstName' in data:
            update_data['first_name'] = data['firstName']
        if 'lastName' in data:
            update_data['last_name'] = data['lastName']
        if 'image' in data:
            update_data['image'] = data['image']
        if 'email' in data and data['email'] is not None:
            update_data['email'] = data['email']
        if 'phone_number' in data and data['phone_number'] is not None:
            update_data['phone_number'] = data['phone_number']

        serializer = UserSerializer(user, data=update_data, partial=True)

        if serializer.is_valid():
            user.save()
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
@permission_classes([IsAuthenticated])
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

@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def SetPin(request, pk):
    data = request.data
    new_pin = data.get('new_pin')

    # Validate new_pin for non-empty and exactly 6 characters
    if not new_pin or len(new_pin) != 6:
        return Response(
            {"error": "The PIN must be a 6-digit number."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(customer_id=pk)

        user.bank_pin = new_pin
        user.save()
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
    except ObjectDoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND
        )


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

    # Extract phone number and charged amount from the customer data
    customer_phone = data.get("customer", {}).get("phone_number")
    customer_name = data.get("customer", {}).get("name")
    customer_email = data.get("customer", {}).get("email")
    narration = data.get("narration")
    amount = data.get("charged_amount")
    flw_ref = data.get("flw_ref")
    payment_type = data.get("payment_type")
    if customer_phone and amount:
        try:
            if ':::' in customer_phone:
                # Extract payment link ID from the customer phone number
                payment_link_id = customer_phone.split(":::")[1].strip()

                # Find the payment link using the payment link ID
                payment_link = PaymentDetails.objects.get(link_id=payment_link_id)

                # Find the user using the customer_id from the payment link
                user = User.objects.get(customer_id=payment_link.customer_id)

                # Add the charged amount to the user's account balance
                user.balance += amount
                user.save()
                print(f"Updated {user.first_name}'s balance to {user.balance}")
                send_fcm_notification(user.device_id,
                                      'Charge Completed',
                                      f'You have received {amount} NGN from {user.first_name} {user.last_name}.')

                # Log the notification in the database
                Notifications.objects.create(
                    device_id=user.device_id,
                    customer_id=user.customer_id,
                    topic='Charge Completed',
                    message=f'You have received {amount} NGN from {user.first_name} {user.last_name}.'
                )
                PaymentDetails.objects.create(
                    customer_id=user.customer_id,
                    name=customer_name,
                    email=customer_email,
                    phone_number=customer_phone,
                    link=payment_link,
                    narration=narration,
                    amount=amount,
                    payment_type=payment_type

                )
                Transaction.objects.create(

                    receiver_name=f'{user.first_name}, {user.last_name}',
                    # Receiver name needs to be passed as in the request
                    amount=amount,  # Amount is already in the original currency
                    bank_code='000',
                    bank=user.bank_name,  # Adjust field names based on response structure
                    account_number=user.account_number,
                    customer_id=user.customer_id,
                    narration=f'Name = {customer_name}, '
                              f'Phone = {customer_phone.split(":::")[0].strip()},'
                              f' Email = {customer_email}',
                    account_id=user.customer_id,
                    user_balance=user.balance,
                    reference=generate_random_id(20),
                    credit=True,
                )
            else:
                # Original logic: Find user by phone number
                user = User.objects.get(phone_number=customer_phone)

                # Add the charged amount to the user's account balance
                user.balance += amount - 35
                user.save()
                Transaction.objects.create(

                    receiver_name=narration,
                    # Receiver name needs to be passed as in the request
                    amount=amount,  # Amount is already in the original currency
                    bank_code='000',
                    bank=user.bank_name,  # Adjust field names based on response structure
                    account_number=user.account_number,
                    customer_id=user.customer_id,
                    narration=f'',
                    account_id=user.customer_id,
                    reference=flw_ref,
                    user_balance=user.balance,
                    credit=True,
                )
                print(f"Updated {user.first_name}'s balance to {user.balance}")

                send_fcm_notification(user.device_id,
                                      'Charge Completed',
                                      f'You have received {amount} NGN from {user.first_name} {user.last_name}.')

                # Log the notification in the database
                Notifications.objects.create(
                    device_id=user.device_id,
                    customer_id=user.customer_id,
                    topic='Charge Completed',
                    message=f'You have received {amount} NGN from {user.first_name} {user.last_name}.'
                )
        except User.DoesNotExist:
            print(f"User with phone number or customer_id does not exist.")
        except PaymentDetails.DoesNotExist:
            print(f"Payment link with ID {payment_link_id} does not exist.")
    else:
        print("Phone number or amount missing in the webhook data.")





def handle_transfer_success(data):
    # Process a successful transfer
    print(f"Transfer Successful: {data}")
    # You can save the transaction to your database or perform other actions here


def handle_transfer_failed(data):
    # Process a failed transfer
    print(f"Transfer Failed: {data}")
    # You can notify the user or log the failure
