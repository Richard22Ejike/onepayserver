from datetime import timedelta

import requests
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
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
from .keys import secret_key, WEBHOOK_SECRET_KEY
from .serializers import UserSerializer
from .models import User, OneTimePassword, OneTimeOtp
from .utils import send_email_to_user, GenerateOtp
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password


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
            "id": 143,
            "password": "pbkdf2_sha256$390000$gUKq6vkgVx8pdNEH0XzuOG$JOrPAwSOXLK0gzXF96WaSSRMFBYpt4P8sb0cJQI7iow=",
            "last_login": "2024-04-08T00:30:33.927046Z",
            "username": "sgsdgdggsfgdg",  # Set default value here
            "email": "richard.ekene22@outlook.com",
            "first_name": "Richard",
            "last_name": "Ejike",
            "phone_number": "09055444489",
            "is_staff": False,
            "is_superuser": False,
            "is_active": False,
            "is_verified": False,
            "status": False,
            "customer_id": "661d07649e2f2a169cffd536",
            "account_id": "661d1dc19e2f2a169cffd64f",
            "organization_id": "65eedccca40a63e818c6cc59",
            "customer_type": "Personal",
            "bvn": "22398644895",
            "account_number": "8548030507",
            "escrow_fund": 0.0,
            "bank_name": "WEMA BANK",
            "updated": "2024-05-05T10:55:51.988586Z",
            "created": "2024-04-15T11:48:23.475051Z",
            "bank_pin": "sgdsfgs",  # Set default value here
            "balance": 0.0,
            "street": "sfgdfgsg",  # Set default value here
            "city": "sgfsdx",  # Set default value here
            "state": "sgfsgdf",  # Set default value here
            "country": "dsfsgs",  # Set default value here
            "postal_code": "sgsgdsff",  # Set default value here
            "access_token": "gdasdgdf",  # Set default value here
            "refresh_token": "hvhmfj",  # Set default value here
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


@api_view(['POST'])
def createUser(request):
    try:
        data = request.data
        secret_key = "sk_live_65eedccca40a63e818c6cc5a65eedccca40a63e818c6cc5b"

        # Check if the user already exists locally
        existing_user = User.objects.filter(
            Q(phone_number=data['phone_number']) | Q(email=data['email']) | Q(bvn=data['bvn'])
        ).first()

        if existing_user:
            return Response({'error': 'User with the provided phone number, email, or BVN already exists.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Make a request to the Blochq API to register the customer
        url = "https://api.blochq.io/v1/customers"
        payload = {
            "email": data['email'],
            "phone_number": data['phone_number'],
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "bvn": data['bvn'],
            "customer_type": data['customer_type']
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {secret_key}"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            error_message = response.json().get('message')
            if error_message in [
                'customer phone number already exist',
                'customer bvn already exist',
                'customer email already exist'
            ]:
                # If the customer already exists in Blochq, retrieve all customers
                customer_url = "https://api.blochq.io/v1/customers"
                customer_response = requests.get(customer_url, headers=headers)

                if customer_response.status_code != 200:
                    return Response({'error': customer_response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                customers_data = customer_response.json().get('data')
                # Filter the customer based on provided data
                customer_data = next((customer for customer in customers_data if
                                      customer['phone_number'] == data['phone_number'] or customer['email'] == data[
                                          'email'] or customer['bvn'] == data['bvn']), None)

                if not customer_data:
                    return Response({'error': 'Customer exists in Blochq but could not be found.'},
                                    status=status.HTTP_404_NOT_FOUND)

                # Retrieve account details
                account_url = f"https://api.blochq.io/v1/accounts?customer_id={customer_data['id']}"
                account_response = requests.get(account_url, headers=headers)
                account_response_data = account_response.json()

                if not account_response_data['data']:
                    return Response({'error': 'Customer exists but no account found.'},
                                    status=status.HTTP_404_NOT_FOUND)

                user_account_data = account_response_data['data'][0]

                # Create the user locally
                user = User.objects.create_user(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    phone_number=data['phone_number'],
                    password=data['password'],
                    email=data['email'],
                    customer_type=data['customer_type'],
                    bvn=data['bvn'],
                    organization_id=customer_data.get('organization_id', ''),
                    customer_id=customer_data.get('id', ''),
                    account_id=user_account_data.get('id', ''),
                    account_number=user_account_data.get('account_number', ''),
                    bank_name=user_account_data.get('bank_name', '')
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
                    'refresh_token': str(user_tokens.get('refresh'))
                })

            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = response.json()
        user_data = response_data.get('data')

        # Check if the user has an account in Blochq
        account_url = f"https://api.blochq.io/v1/accounts?customer_id={user_data['id']}"
        account_response = requests.get(account_url, headers=headers)
        account_response_data = account_response.json()

        if not account_response_data['data']:
            # Create an account if not exists
            account_payload = {
                "customer_id": user_data['id'],
                "alias": "business",
                "collection_rules": {
                    "amount": 30000,
                    "frequency": 2
                }
            }

            account_response = requests.post(account_url, json=account_payload, headers=headers)
            if account_response.status_code != 200:
                return Response({'error': account_response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            account_response_data = account_response.json()
            user_account_data = account_response_data.get('data')

        else:
            user_account_data = account_response_data['data'][0]

        # Create the user locally
        user = User.objects.create_user(
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            password=data['password'],
            email=data['email'],
            customer_type=data['customer_type'],
            bvn=data['bvn'],
            organization_id=user_data.get('organization_id', ''),
            customer_id=user_data.get('id', ''),
            account_id=user_account_data.get('id', ''),
            account_number=user_account_data.get('account_number', ''),
            bank_name=user_account_data.get('bank_name', '')
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
            'refresh_token': str(user_tokens.get('refresh'))
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
    print(user.customer_id)
    url = f"https://api.blochq.io/v1/customers/{user.customer_id}"

    payload = {"email": user.email}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {secret_key}"
    }

    response = requests.put(url, json=payload, headers=headers)
    if response.status_code != 200:
        # If the request was not successful, return an error response
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200:
        response_data = response.json()
        user_data = response_data.get('data')
        print(response_data.get('data'))
        print(user_data.get('customer_id', ''))
        account_url = f"https://api.blochq.io/v1/accounts/customers/accounts/{user_data.get('id', '')}"
        account_payload = {"accountID": "661d1dc19e2f2a169cffd64f"}
        account_headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {secret_key}"  # Replace with your actual secret key
        }
        account_response = requests.get(account_url, json=account_payload, headers=account_headers)
        if account_response.status_code != 200:
            return Response({'error': account_response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if account_response.status_code == 200:
            account_response_data = account_response.json()
            print(account_response_data.get('data', [{}])[0].get('balance', ''))
            print(account_response_data.get('data', [{}])[0].get('account_number', ''))
            print(account_response_data.get('data', [{}])[0].get('id', ''))
            user.account_id = account_response_data.get('data', [{}])[0].get('id', '')
            user.account_number = account_response_data.get('data', [{}])[0].get('account_number', '')
            user.bank_name = account_response_data.get('data', [{}])[0].get('bank_name', '')
            user.balance = account_response_data.get('data', [{}])[0].get('balance', '')
            user.kyc_tier = account_response_data.get('data', [{}])[0].get('kyc_tier', '')
            user.group = user_data.get('group', '')
            user.customer_id = user_data.get('id', '')
            user.organization_id = user_data.get('organization_id', '')
            user.save()
        # Authenticate user
        if not check_password(password, user.password):
            return Response({'message': 'bad credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            token, _ = Token.objects.get_or_create(user=user)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user_tokens = user.tokens()
        user.access_token = str(user_tokens.get('access'))
        user.refresh_token = str(user_tokens.get('refresh'))

        serializer = UserSerializer(user, many=False)
        print(serializer.data)
        return Response({'user': serializer.data,
                         })


@api_view(['POST'])
def forgetpassword(request):
    data = request.data
    email = data.get('email')

    # Check if a user with the provided email exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Generate an OTP (One-Time Passcode)
    otp_code = GenerateOtp()

    # Save the OTP in the OneTimePassword model
    OneTimePassword.objects.create(user=user, code=otp_code)

    # Send the OTP to the user via email
    send_email_to_user(email, otp_code)

    return Response({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def reset_password(request):
    data = request.data
    email = data.get('email')
    otp = data.get('otp')  # OTP entered by the user
    new_password = data.get('new_password')

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
def send_otp_to_phone(request):
    data = request.data
    phone_number = data.get('phone_number')

    # Generate an OTP (One-Time Passcode)
    otp_code = GenerateOtp()

    # Save the OTP in the OneTimePassword model
    OneTimeOtp.objects.create(key=phone_number, code=otp_code)

    print(otp_code)

    # Send the OTP to the user via SMS (you need to implement this)
    # Example: send_sms_to_user(phone_number, otp_code)

    return Response({'message': 'OTP sent to your phone'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def send_otp_to_email(request):
    data = request.data
    email = data.get('email')

    # Generate an OTP (One-Time Passcode)
    otp_code = GenerateOtp()

    # Save the OTP in the OneTimePassword model
    OneTimeOtp.objects.create(key=email, code=otp_code)

    # Send the OTP to the user via email
    send_email_to_user(email, otp_code)

    return Response({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def otp_verified(request):
    otpcode = request.data.get('otp')
    key = request.data.get('key')
    try:
        otp_code_objs = OneTimeOtp.objects.filter(key=key)

        for otp_code_obj in otp_code_objs:
            print(otpcode)
            otp = otp_code_obj.code
            print(otp)
            if otp == otpcode:
                return Response({
                    'message': 'account email verified successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'message': 'code is invalid user already verified'
            }, status=status.HTTP_204_NO_CONTENT)

        return Response({
            'message': 'passcode not provided'
        }, status=status.HTTP_404_NOT_FOUND)

    except OneTimeOtp.DoesNotExist:
        return Response({'message': "passcode not provided"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def password_reset_otp_verified(request):
    otpcode = request.data.get('otp')
    try:
        user_code_obj = OneTimePassword.objects.get(code=otpcode)
        user = user_code_obj.user
        if not user.is_verified:
            user.is_verified = True
            user.save()
            return Response({
                'message': 'account email verified successfully'
            }, status=status.HTTP_200_OK)
        return Response({
            'message': 'code is invalid user already verified'
        }, status=status.HTTP_204_NO_CONTENT)
    except OneTimePassword.DoesNotExist:
        return Response({'message': "passcode not provided"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])  # Require token authentication
@permission_classes([IsAuthenticated])  # Require authentication for permission
def updateUser(request, pk):
    data = request.data
    user = User.objects.get(customer_id=pk)
    serializer = UserSerializer(user, data=data)
    try:

        if pk is None:
            if serializer.is_valid():
                serializer.save()
            return Response({
                serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'message': 'code is invalid user already verified'
        }, status=status.HTTP_204_NO_CONTENT)
    except OneTimePassword.DoesNotExist:
        return Response({'message': "passcode not provided"}, status=status.HTTP_404_NOT_FOUND)


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
        # If the request was not successful, return an error response
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200:
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
        # If the request was not successful, return an error response
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200:
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
        # If the request was not successful, return an error response
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200:
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
    # Retrieve the X-Bloc-Webhook signature from the request headers
    signature = request.headers.get('X-Bloc-Webhook')

    # Compute the expected signature using your webhook secret and the request body
    expected_signature = hmac.new(WEBHOOK_SECRET_KEY.encode('utf-8'), request.body, hashlib.sha256).hexdigest()

    # Compare the computed signature with the provided signature
    if signature != expected_signature:
        return Response({'error': 'Invalid signature'}, status=401)

    # Parse the request data
    try:
        event = request.data.get('event')
        data = request.data.get('data')
    except json.JSONDecodeError:
        return Response({'error': 'Invalid payload'}, status=400)

    # Process the event
    if event == 'transaction.new':
        handle_transaction_new(data)
    elif event == 'transaction.updated':
        handle_transaction_updated(data)
    elif event == 'account.created':
        handle_account_created(data)
    # Add additional event handlers as needed
    else:
        return Response({'error': 'Unhandled event'}, status=400)

    return Response({'status': 'success'}, status=200)


def handle_transaction_new(data):
    # Process the transaction.new event
    print(f"Transaction New: {data}")


def handle_transaction_updated(data):
    # Process the transaction.updated event
    print(f"Transaction Updated: {data}")


def handle_account_created(data):
    # Process the account.created event
    print(f"Account Created: {data}")
