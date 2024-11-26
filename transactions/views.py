from datetime import date, datetime
from django.views.decorators.csrf import csrf_exempt
import onesignal
import requests
from decouple import config
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from onesignal.api import default_api
from onesignal.model.notification import Notification
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from transactions.models import Transaction, PayBill, PaymentDetails, Card, Notifications, Escrow, ChatMessage, \
    PaymentLink
from transactions.serializers import TransactionSerializer, PayBillSerializer, PaymentLinkSerializer, CardSerializer, \
    NotificationSerializer, EscrowSerializer, ChatSerializer
from users.models import User
from users.serializers import UserSerializer
from users.utils import send_email_to_user
from django.utils import timezone
import uuid
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from rest_framework.request import Request

from channels.generic.websocket import WebsocketConsumer
import json

from users.views import generate_random_id

configuration = onesignal.Configuration(
    app_key=config('APP_KEY'),
    api_key=config('API_KEY'),
    user_key=config('USER_KEY')
)

secret_key = config('SECRETKEY')


# Bill Payments
@api_view(['POST'])
def makeBillPayment(request, pk):
    try:
        data = request.data
        # Fetch the user by customer_id (pk)
        user = get_object_or_404(User, customer_id=pk)

        # Check if the bank_pin matches
        if data.get('pin') == user.bank_pin:
            url = f"https://api.flutterwave.com/v3/billers/{data['operator_id']}/items/{data['product_id']}/payment"

            # Prepare the payload as per Flutterwave's API structure
            payload = {
                "country": "NG",  # Adjust country if necessary
                "customer_id": data['device_number'],  # Customer identifier for the bill payment
                "amount": data['amount'],  # Bill payment amount
                "reference": generate_random_id(20),  # Unique reference for this transaction
                "callback_url": "https://your-callback-url.com",  # Replace with your callback URL
            }

            # Set headers with authorization token
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {secret_key}"  # Ensure to pass your Flutterwave secret key
            }

            # Make the POST request to Flutterwave API
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                print(response.status_code)
                print(response.json())
                # If the request was not successful, return an error response
                return Response({'error': response.json(), 'problem': response.status_code},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if response.status_code == 200:
                # Log the bill payment in your database
                print(response.json())
                user.balance -= data['amount']

                user.save()
                print(user.balance)
                bill = PayBill.objects.create(
                    amount=data['amount'],
                    product_id=data['product_id'],  # If needed
                    operator_id=data['operator_id'],  # If needed
                    account_id=data['account_id'],  # If needed
                    meter_type=data['meter_type'],  # If needed
                    bill_type=data['bill_type'],
                    device_number=data['device_number'],  # If needed
                    beneficiary_msisdn=data['beneficiary_msisdn'],  # If needed
                )
                Transaction.objects.create(
                    receiver_name=user.first_name,
                    amount=data['amount'],
                    bank_code=data['bank_code'],
                    account_number=data['device_number'],
                    narration='bill purchase',
                    account_id=data['account_id'],
                    bank=data['bank'],
                    credit=data['credit'],
                    customer_id=user.customer_id,
                    user_balance=user.balance
                )

                # Serialize the bill payment data and return the response
                serializer = PayBillSerializer(bill, many=False)
                return Response(serializer.data)
        else:
            return Response({"error": "Incorrect bank pin."}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Transfers
@api_view(['POST'])
def makeInternalTransfer(request, pk):
    try:
        data = request.data
        print(pk)
        user = get_object_or_404(User, customer_id=pk)

        if data.get('pin') != user.bank_pin:
            return Response({"error": "Incorrect bank pin."}, status=status.HTTP_400_BAD_REQUEST)

        amount = data['amount']
        to_account_number = data['account_number']
        print(to_account_number)

        # Fetch the receiving user by account number
        receiving_user = get_object_or_404(User, account_number=to_account_number)

        if user.id == receiving_user.id:
            return Response({"error": "Can not transfer to your own account."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure that the user has sufficient balance for the transfer
        if user.balance < amount:
            return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

        # Perform the transfer within a transaction to ensure atomicity
        try:
            with transaction.atomic():
                # Decrease the sender's balance
                user.balance -= amount
                user.notification_number += 1
                user.save()

                # Increase the receiver's balance
                receiving_user.balance += amount
                receiving_user.notification_number += 1
                receiving_user.save()

                # Create the transaction record
                bill = Transaction.objects.create(
                    receiver_name=f'{receiving_user.first_name} {receiving_user.last_name}',
                    amount=data['amount'],
                    reference=generate_random_id(20),
                    account_number=to_account_number,
                    narration=data['narration'],
                    account_id=user.account_id,
                    bank='OnePlug',
                    credit=data.get('credit', True),
                    customer_id=user.customer_id,
                    user_balance=user.balance
                )
                Transaction.objects.create(
                    receiver_name=f'{user.first_name} {user.last_name}',
                    amount=data['amount'],
                    reference=generate_random_id(20),
                    account_number=to_account_number,
                    narration=data['narration'],
                    account_id=receiving_user.account_id,
                    bank='OnePlug',
                    credit=False,
                    customer_id=receiving_user.customer_id,
                    user_balance=receiving_user.balance
                )

                # Serialize the transaction
                serializer = TransactionSerializer(bill, many=False)

                # Call SentNotifications endpoint for the receiving user
                url = "https://api.onesignal.com/notifications"

                # Payload to be sent in the POST request
                payload = {
                    "app_id": configuration.app_key,
                    "target_channel": "push",
                    "contents": {
                        "en": f'You have received {data["amount"]} from {user.first_name}{user.last_name}.'
                    },
                    "headings": {
                        "en": "Payment Made"
                    },

                    "data": {
                        "custom_key": "custom_value"
                    },
                    "priority": 10,
                    "isAndroid": True,
                    "include_subscription_ids": [receiving_user.device_id]  # Sending to subscribed users
                }
                print(receiving_user.device_id)

                # Headers for the POST request
                headers = {
                    "Authorization": f"Basic {configuration.api_key}",  # Include the API key
                    "accept": "application/json",  # Accept JSON responses
                    "content-type": "application/json"  # Send JSON request body
                }

                # Make the POST request to OneSignal
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                Notifications.objects.create(
                    device_id=receiving_user.device_id,
                    customer_id=receiving_user.customer_id,
                    topic='Transfer',
                    message=f'You have received {data["amount"]} from {user.first_name} {user.last_name}.',
                )
                # Output the response from OneSignal
                print(f"Status Code: {response.status_code}")
                print(f"Response Body: {response.json()}")
                # Call SentNotifications endpoint for the receiving user
                url = "https://api.onesignal.com/notifications"

                # Payload to be sent in the POST request
                payload = {
                    "app_id": configuration.app_key,
                    "target_channel": "push",
                    "contents": {
                        "en": f'You sent {data["amount"]} to {receiving_user.first_name} {receiving_user.last_name}.'
                    },
                    "headings": {
                        "en": "Payment made"
                    },

                    "data": {
                        "custom_key": "custom_value"
                    },
                    "priority": 10,
                    "isAndroid": True,
                    "include_subscription_ids": [user.device_id, ]  # Sending to subscribed users
                }
                print(user.device_id)

                # Headers for the POST request
                headers = {
                    "Authorization": f"Basic {configuration.api_key}",  # Include the API key
                    "accept": "application/json",  # Accept JSON responses
                    "content-type": "application/json"  # Send JSON request body
                }

                # Make the POST request to OneSignal
                response = requests.post(url, headers=headers, data=json.dumps(payload))

                Notifications.objects.create(
                    device_id=user.device_id,
                    customer_id=user.customer_id,
                    topic='Transfer',
                    message=f'You have received {data["amount"]} from {user.first_name}.',
                )
                # Output the response from OneSignal
                print(f"Status Code: {response.status_code}")
                print(f"Response Body: {response.json()}")
                return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"error": 'something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def makeExternalTransfer(request, pk):
    try:
        data = request.data
        user = get_object_or_404(User, customer_id=pk)
        amount = data['amount']
        if user.balance < amount:
            return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)
        # Check if the bank_pin matches
        if data.get('pin') == user.bank_pin:
            print(data["bank_code"])
            url = "https://api.flutterwave.com/v3/transfers"
            payload = {
                "account_bank": data['bank_code'],  # Flutterwave uses 'account_bank' for the bank code
                "account_number": data['account_number'],
                "amount": data['amount'],
                "narration": data['narration'],
                "currency": "NGN",  # Currency for Flutterwave is specified in this field
                "reference": generate_random_id(20),
                "callback_url": "https://www.flutterwave.com/ng/",  # Customize this if needed
                "debit_currency": "NGN"
            }
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {secret_key}"  # Ensure you have your Flutterwave secret key
            }
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                # If the request was not successful, return an error response
                print(response.text)
                return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            response_data = response.json()
            print(response.status_code)

            if response.status_code == 200 and response_data['status'] == 'success':
                # Perform the transfer within a transaction to ensure atomicity

                with transaction.atomic():
                    # Decrease the sender's balance
                    user.balance -= amount
                    user.save()
                transaction_data = response_data['data']
                bill = Transaction.objects.create(
                    receiver_name=data['receiver_name'],  # Receiver name needs to be passed as in the request
                    amount=transaction_data['amount'],  # Amount is already in the original currency
                    bank_code=transaction_data['bank_code'],
                    bank=transaction_data['bank_name'],  # Adjust field names based on response structure
                    account_number=transaction_data['account_number'],
                    customer_id=pk,
                    narration=data['narration'],
                    account_id=data['account_id'],
                    reference=transaction_data['reference'],
                    credit=data['credit'],
                    user_balance=user.balance
                )
                serializer = TransactionSerializer(bill, many=False)
                print(serializer.data)
                return Response(serializer.data)
        else:
            return Response({"error": "Incorrect bank pin."}, status=status.HTTP_400_BAD_REQUEST)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def getTransaction(request):
    transactions = Transaction.objects.all()
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getTransactions(request, pk):
    transactions = Transaction.objects.filter(customer_id=pk).order_by('-id')
    serializer = TransactionSerializer(transactions, many=True)
    print(serializer.data)
    return Response(serializer.data)


@api_view(['POST'])
def findAccountbyId(request, pk):
    data = request.data
    transactions = Transaction.objects.filter(account_id=pk)
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)


# Notifications
@api_view(['GET'])
def getNotifications(request, pk):
    notifications = Notifications.objects.filter(customer_id=pk)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def SentNotifications(request):
    data = request.data
    with onesignal.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        notification = Notifications(None)

        # example passing only required values which don't have defaults set
        try:
            # Create notification
            api_response = api_instance.create_notification(notification)
            print(api_response)
        except onesignal.ApiException as e:
            print("Exception when calling DefaultApi->create_notification: %s\n" % e)
    notification = Notifications.objects.create(
        device_id=data['device_id'],
        customer_id=data['customer_id'],
        topic=data['topic'],
        message=data['message'],
    )

    serializer = NotificationSerializer(notification, many=False)
    return Response(serializer.data)


# Escrows
@api_view(['GET'])
def getUserEscrows(request, pk):
    try:
        user = User.objects.get(email=pk)  # Assuming email is unique
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def CreateEscrow(request, pk):
    try:
        data = request.data
        print(data['customer_id'])

        # Fetch the user by customer_id (pk)
        user = get_object_or_404(User, customer_id=pk)
        make_payment = False
        # Check if the bank_pin matches
        if data.get('pin') != user.bank_pin:
            return Response({"error": "Incorrect bank pin."}, status=400)
        subject = "One time Passcode for email Verification"
        email_body = (f"<strong>hi thanks for Using OnePlug  \n {user.first_name} has created an escrow with you. please "
                      f"check your profile to accepted or cancel the request  </strong>")

        # # Send the OTP to the user via email
        send_email_to_user(data['receiver_email'], email_body, subject)

        # Check if role equals role_paying and if user has enough escrow_fund
        if data['role'] == data['role_paying']:
            print(user.balance)

            escrow_amount = data.get('amount')   # Assume escrow_amount is part of the request data

            if user.balance < escrow_amount:
                return Response({"error": "Insufficient balance."}, status=400)

            # Deduct the escrow amount from user's escrow fund

            user.balance -= escrow_amount
            user.escrow_fund += escrow_amount
            make_payment = True
            user.save()

        # Generate a unique reference number using a combination of timestamp and UUID
        reference = f"{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        # Create the escrow
        escrow = Escrow.objects.create(
            customer_id=data['customer_id'],
            escrow_description=data['escrow_description'],
            escrow_name=data['escrow_name'],
            escrow_Status=data['escrow_Status'],
            receiver_email=data['receiver_email'],
            payment_type=data['payment_type'],
            role=data['role'],
            amount=data['amount'],
            sender_name=data['sender_name'],
            account_id=data['account_id'],
            role_paying=data['role_paying'],
            estimated_days=data['estimated_days'],
            milestone=data['milestone'],
            number_milestone=data['number_milestone'],
            receiver_id=data['receiver_id'],
            make_payment=make_payment,
            reference=reference  # Assign the generated reference number
        )
        Transaction.objects.create(
            receiver_name=f"{user.first_name} {user.last_name}",
            amount=escrow.amount,
            bank_code='',  # add appropriate bank code
            account_number=user.account_number,
            narration='Escrow payment',
            account_id=user.account_id,
            bank=user.bank_name,  # add appropriate bank name
            credit=False,  # set as credit transaction
            customer_id=user.customer_id,
            user_balance=user.balance
        )

        serializer = EscrowSerializer(escrow, many=False)
        return Response(serializer.data,status=status.HTTP_200_OK)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def EditEscrow(request, pk):
    try:
        escrow = Escrow.objects.get(id=pk)
    except Escrow.DoesNotExist:
        return Response({'error': 'Escrow not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = EscrowSerializer(instance=escrow, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def EmailEscrow(request, pk):
    try:
        escrow = Escrow.objects.get(id=pk)
    except Escrow.DoesNotExist:
        return Response({'error': 'Escrow not found'}, status=status.HTTP_404_NOT_FOUND)

    send_email_to_user(escrow.receiver_email, '')
    serializer = EscrowSerializer(instance=escrow, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def getEscrows(request, pk):
    # Fetch the user's email based on the customer_id (pk)

    user = get_object_or_404(User, customer_id=pk)
    user_email = user.email

    # Filter escrows by customer_id
    escrows_by_customer_id = Escrow.objects.filter(customer_id=pk)

    # Filter escrows where receiver_email matches the user's email
    escrows_by_receiver_email = Escrow.objects.filter(receiver_email=user_email)

    # Combine both querysets
    combined_escrows = escrows_by_customer_id | escrows_by_receiver_email

    # Remove duplicates if any
    combined_escrows = combined_escrows.distinct()

    # Serialize the combined escrows
    serializer = EscrowSerializer(combined_escrows, many=True)

    return Response(serializer.data)


@api_view(['PUT'])
def updateEscrows(request, pk):
    escrow = Escrow.objects.get(id=pk)
    data = request.data
    user = User.objects.get(email=escrow.receiver_email)
    if data.get('escrow_status') == 'Accept Request':
        escrow.escrow_Status = 'Accept Request'
        escrow.accepted = True
        escrow.answered = True
    if data.get('escrow_status') == 'Reject Request':
        escrow.escrow_Status = 'Reject Request'
        escrow.accepted = False
        escrow.answered = True

    if data.get('escrow_status') == 'Cancel Request':
        escrow.escrow_Status = 'Cancel Request'
        escrow.accepted = False
        escrow.answered = True
        escrow.is_disabled = True

    if data.get('escrow_status') == 'Completed':
        escrow.escrow_Status = 'Completed'
        escrow.accepted = True
        escrow.answered = True

    escrow.save()
    serializer = EscrowSerializer(escrow, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
def disputeEscrows(request, pk):
    escrow = Escrow.objects.get(id=pk)
    data = request.data
    escrow.dispute = data.get('dispute')  # Add the dispute information here
    escrow.save()
    serializer = EscrowSerializer(escrow, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
def ReleaseEscrowsFund(request, pk):
    data = request.data

    # Fetch the escrow by customer_id
    print('escrow')
    escrow = Escrow.objects.get(id=pk)

    print('user')
    # Fetch the user by customer_id
    user = get_object_or_404(User, customer_id=escrow.customer_id)

    print('user')
    # Fetch the receiver by receiver_email
    receiver = get_object_or_404(User, email=escrow.receiver_email)
    print(user)
    print(receiver)
    print(user.escrow_fund)
    print(receiver.escrow_fund)
    # Determine the direction of the transaction
    if escrow.role == escrow.role_paying:
        # User sends amount to the receiver
        sender = user
        recipient = receiver
    else:
        # Receiver sends amount to the user
        sender = receiver
        recipient = user

    # Ensure sender has enough balance
    if sender.escrow_fund < escrow.amount:
        return Response({"error": "Insufficient balance."}, status=400)

    # Deduct the amount from the sender's balance
    print(sender.escrow_fund)
    sender.escrow_fund -= escrow.amount
    sender.save()
    print(sender.escrow_fund)

    # Add the amount to the recipient's balance
    print(sender.balance)
    recipient.balance += escrow.amount
    recipient.save()
    print(sender.balance)

    # Create a transaction record
    bill = Transaction.objects.create(
        receiver_name=recipient.first_name,
        amount=escrow.amount,
        bank_code='',  # add appropriate bank code
        account_number=recipient.account_id,
        narration=data.get('narration', ''),
        account_id=sender.account_id,
        bank=sender.bank_name,  # add appropriate bank name
        credit=True,  # set as credit transaction
        customer_id=recipient.customer_id,
        user_balance=recipient.balance
    )

    # Update the escrow status to 'Completed'
    escrow.escrow_Status = 'Completed'
    escrow.save()

    # Serialize and return the updated escrow object
    serializer = EscrowSerializer(escrow, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
def MakePaymentEscrows(request, pk):
    escrow_id = request.data.get('escrow_id')
    if not escrow_id:
        return Response({"error": "escrow_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        escrow = Escrow.objects.get(customer_id=pk, id=escrow_id)
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)
    except Escrow.MultipleObjectsReturned:
        return Response({"error": "Multiple escrows found for this user with the given ID"},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=escrow.receiver_email)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    if user.balance >= escrow.amount:
        user.balance -= escrow.amount
        user.escrow_fund += escrow.amount
        user.save()
        escrow.make_payment = True
        escrow.save()
    else:
        return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = EscrowSerializer(escrow, many=False)
    return Response(serializer.data)


# Cards
@api_view(['POST'])
def SaveCard(request):
    data = request.data
    card = Card.objects.create(
        customer_id=data['customer_id'],
        card_number=data['card_number'],
        account_id=data['account_id'],
        cvv=data['cvv'],
        expiry_month=data['expiry_month'],
        expiry_year=data['expiry_year'],
        pin=data['pin'],
    )

    serializer = CardSerializer(card, many=False)
    return Response(serializer.data)


@api_view(['GET'])
def getCards(request, pk):
    cards = Card.objects.filter(customer_id=pk)
    serializer = CardSerializer(cards, many=True)
    print(serializer.data)
    return Response(serializer.data)


@api_view(['GET'])
def getCards2(request, pk):
    card = Card.objects.get(customer_id=pk)
    url = f"https://api.blochq.io/v1/cards/secure-data/{card.card_id}"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {secret_key}"
    }

    cardresponse = requests.get(url, headers=headers)
    if cardresponse.status_code != 200:
        # If the request was not successful, return an error response
        return Response({'error': cardresponse.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if cardresponse.status_code == 200:
        cardresponse_data = cardresponse.json()
        card_data1 = cardresponse_data.get('data')
        card.pin = card_data1.get('pin', ''),
        card.card_number = card_data1.get('pan', ''),
        card.expiry_month = card_data1.get('expiry_month', ''),
        card.expiry_year = card_data1.get('expiry_year', ''),
        card.cvv = card_data1.get('cvv', ''),
    if not card.linked:
        url = "https://api.blochq.io/v1/cards/fixed-account/link"

        payload = {
            "card_id": card.card_id,
            "account_id": card.account_id
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

    cards = Card.objects.filter(customer_id=pk)
    serializer = CardSerializer(cards, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def IssueCard(request):
    try:
        data = request.data
        user = get_object_or_404(User, customer_id=data['customer_id'])


        url = "https://api.flutterwave.com/v3/virtual-cards"

        try:
            dob = user.date_of_birth  # This should be the string '19/09/1988'
            formatted_dob = datetime.strptime(dob, '%d/%m/%Y').strftime('%Y/%m/%d')
            print(formatted_dob)  # Output to check the formatted date
        except ValueError as e:
            return Response(
                {'error': f'Invalid date_of_birth format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Constructing the payload with additional fields
        payload = {
            "customer_id": data['customer_id'],
            "brand": data['brand'],
            "currency": "NGN",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_of_birth": formatted_dob,
            "email": user.email,
            "phone": user.phone_number,
            "title": data.get("title", "MR"),
            "gender": data.get("gender", "M"),
            "amount": data.get("amount", 100),
            "billing_name": f'{user.first_name} {user.last_name}',
            "billing_address": "Rumuewhara New Layout",
            "billing_city": "Port Harcourt",
            "billing_state": "PH",
            "billing_postal_code": "500101",
            "billing_country": "NG"
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {secret_key}"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            # If the request was not successful, return an error response
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response.status_code == 200:
            response_data = response.json()
            card_data = response_data.get('data')
            user.balance -= data.get("amount", 100)
            user.save()

            # Creating a Card object with the response data
            card = Card.objects.create(
                card_id=card_data.get('id', ''),
                customer_id=data['customer_id'],
                brand=data['brand'],
                name=f'{user.first_name} {user.last_name}',
                balance=card_data.get('amount', ''),
                pin=card_data.get('cvv', ''),  # Assuming the pin should be mapped to cvv
                card_number=card_data.get('card_pan', ''),
                account_id=card_data.get('account_id', ''),
                currency=card_data.get('currency', ''),
                expiry_month=card_data.get('expiration', '').split('-')[1],  # Extracting month from "YYYY-MM"
                expiry_year=card_data.get('expiration', '').split('-')[0],  # Extracting year from "YYYY-MM"
                cvv=card_data.get('cvv', ''),
                card_type=card_data.get('card_type', '')
            )

            serializer = CardSerializer(card, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def ChangePin(request, pk):
    data = request.data
    card = Card.objects.get(id=pk)
    serializer = CardSerializer(card, data=data)
    required_fields = ['card_id', 'old_pin', 'new_pin']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return Response({'error': f'Missing required fields: {", ".join(missing_fields)}'},
                        status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(['POST'])
def fundAccountWithCard(request, pk):
    try:
        data = request.data
        user = get_object_or_404(User, customer_id=pk)

        # URL to fund the card
        url = f"https://api.flutterwave.com/v3/virtual-cards/{data['card_id']}/fund"

        # Request payload for card funding
        payload = {
            "amount": data['amount'],
            "debit_currency": data.get("debit_currency", "NGN")
        }

        # Set authorization header
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {secret_key}"
        }

        # Make the POST request to Flutterwave
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            # If the funding request failed, return an error response
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Handle successful funding response
        response_data = response.json()
        if response_data['status'] == "success":
            # Create a transaction record
            bill = Transaction.objects.create(
                receiver_name=user.first_name,
                amount=data['amount'],
                credit=True,
                customer_id=user.customer_id,
                account_number=user.account_number,
                narration='Pay with Card',
                account_id=user.account_id,
                reference=response_data.get('data', {}).get('reference', ''),
                bank=user.bank_name,
            )

            # Serialize the transaction data and return it
            serializer = TransactionSerializer(bill, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Handle unexpected response
        return Response({'error': 'Failed to fund card'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def getCardDetails(request, pk):
    card = Card.objects.get(customer_id=pk)
    url = f"https://api.blochq.io/v1/cards/secure-data/{card.card_id}"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {secret_key}"
    }

    cardresponse = requests.get(url, headers=headers)
    if cardresponse.status_code != 200:
        # If the request was not successful, return an error response
        return Response({'error': cardresponse.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if cardresponse.status_code == 200:
        cardresponse_data = cardresponse.json()
        card_data1 = cardresponse_data.get('data')
        card.pin = card_data1.get('pin', ''),
        card.card_number = card_data1.get('pan', ''),
        card.expiry_month = card_data1.get('expiry_month', ''),
        card.expiry_year = card_data1.get('expiry_year', ''),
        card.cvv = card_data1.get('cvv', ''),

        serializer = CardSerializer(card, many=False)
        return Response(serializer.data)


@api_view(['POST'])
def WithDrawCard(request, pk):
    data = request.data
    card = Card.objects.get(id=pk)
    serializer = CardSerializer(card, data=data)
    required_fields = ['card_id', 'amount', 'account_id', 'currency']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return Response({'error': f'Missing required fields: {", ".join(missing_fields)}'},
                        status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


# PAYMENTLINK
@api_view(['GET'])
def getPaymentLinks(request, pk):
    payment_links = PaymentLink.objects.filter(customer_id=pk).prefetch_related('payment_details')
    serializer = PaymentLinkSerializer(payment_links, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getPaymentLink(request, pk):
    paymentLink = PaymentLink.objects.get(link_id=pk)
    serializer = PaymentLinkSerializer(paymentLink, many=False)
    return Response(serializer.data)


@api_view(['POST'])
def CreatePaymentLink(request):
    try:
        data = request.data
        links = generate_random_id(17)
        link = PaymentLink.objects.create(
            link_id=links,  # Transaction reference
            link_url=f'https://oneplugpay-payment-link.onrender.com/{links}',  # Redirect URL
            customer_id=data.get('customer_id', ''),  # Optionally store customer ID if needed
            name=data['name'],
            description=data.get('description', ''),  # Add description if needed
            amount=data['amount'],  # Payment amount
            currency='NGN',  # Currency
        )

        serializer = PaymentLinkSerializer(link, many=False)
        print(serializer.data)
        return Response(serializer.data)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def CreateCheckout(request):
    try:
        data = request.data
        url = "https://api.flutterwave.com/v3/payments"

        payload = {
            "tx_ref": generate_random_id(17),  # Replace with your transaction reference
            "amount": data['amount'],
            "currency": 'NGN',
            "redirect_url": 'https://flutterwave.com/ng',
            "customer": {
                "email": data['email'],
                "phone_number": data['phone_number'],
                "name": data['name']
            },
            "customizations": {
                "title": 'Oneplug',
                "logo": ''
            }
        }

        headers = {
            "Authorization": f"Bearer {secret_key}",  # Replace with your Flutterwave secret key
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response.status_code == 200:
            response_data = response.json()
            print(response_data)

            # Extract the link from the response data
            user_data = response_data.get('data', {})
            payment_link = user_data.get('link')

            if payment_link:
                return Response({'link': payment_link}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Payment link not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Default response in case of unknown errors
        return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def EditPaymentLink(request, pk):
    data = request.data
    card = PaymentLink.objects.get(id=pk)
    serializer = PaymentLinkSerializer(card, data=data)
    required_fields = ['name', 'description', 'amount', 'currency']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return Response({'error': f'Missing required fields: {", ".join(missing_fields)}'},
                        status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


# CHAT

@api_view(['GET'])
def getChats(request, pk):
    messages = ChatMessage.objects.filter(escrow_id=pk)
    serializer = ChatSerializer(messages, many=True)
    return Response(serializer.data)
