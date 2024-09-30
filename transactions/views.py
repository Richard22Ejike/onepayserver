from datetime import date
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
from transactions.models import Transaction, PayBill, PaymentLink, Card, Notifications, Escrow, ChatMessage
from transactions.serializers import TransactionSerializer, PayBillSerializer, PaymentLinkSerializer, CardSerializer, \
    NotificationSerializer, EscrowSerializer, ChatSerializer
from users.models import User
from users.serializers import UserSerializer
from users.utils import send_email_to_user
from django.utils import timezone
import uuid
from django.http import HttpRequest
from rest_framework.request import Request

from channels.generic.websocket import WebsocketConsumer
import json

from users.views import generate_random_id

configuration = onesignal.Configuration(
    app_key="56618190-490a-4dc6-af2e-71ea67697f99",
    user_key="MjczMDdjYzUtM2FkMy00Y2JhLThjY2QtMTEyNGZhNTdjZDYw"
)

secret_key = config('SECRETKEY')


# Bill Payments
@api_view(['POST'])
def makeBillPayment(request, pk):
    data = request.data
    # Fetch the user by customer_id (pk)
    user = get_object_or_404(User, customer_id=pk)

    # Check if the bank_pin matches
    if data.get('pin') == user.bank_pin:
        url = f"https://api.flutterwave.com/v3/billers/{data['operator_id']}/items/{data['product_id']}/payment"

        # Prepare the payload as per Flutterwave's API structure
        payload = {
            "country": "NG",  # Adjust country if necessary
            "customer_id": data['customer_id'],  # Customer identifier for the bill payment
            "amount": data['amount'],  # Bill payment amount
            "reference": data['reference'],  # Unique reference for this transaction
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
            # If the request was not successful, return an error response
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response.status_code == 200:
            # Log the bill payment in your database
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

            # Serialize the bill payment data and return the response
            serializer = PayBillSerializer(bill, many=False)
            return Response(serializer.data)
    else:
        return Response({"error": "Incorrect bank pin."}, status=status.HTTP_400_BAD_REQUEST)


# Transfers
@api_view(['POST'])
def makeInternalTransfer(request, pk):
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
        return Response({"error": "Can transfer to your own account."}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure that the user has sufficient balance for the transfer
    if user.balance < amount:
        return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

    # Perform the transfer within a transaction to ensure atomicity
    try:
        with transaction.atomic():
            # Decrease the sender's balance
            user.balance -= amount
            user.save()

            # Increase the receiver's balance
            receiving_user.balance += amount
            receiving_user.save()

            # Create the transaction record
            bill = Transaction.objects.create(
                receiver_name=receiving_user.first_name,
                amount=data['amount'],
                bank_code=data['bank_code'],
                account_number=to_account_number,
                narration=data['narration'],
                account_id=data['account_id'],
                bank=data['bank'],
                credit=data['credit'],
                customer_id=user.customer_id
            )

            # Serialize the transaction
            serializer = TransactionSerializer(bill, many=False)

            # Call SentNotifications endpoint for the receiving user
            #
            # with onesignal.ApiClient(configuration) as api_client:
            #     # Create an instance of the API class
            #     api_instance = default_api.DefaultApi(api_client)
            #     notification = Notification(
            #         app_id='56618190-490a-4dc6-af2e-71ea67697f99',
            #         include_player_ids=[receiving_user.device_id],
            #         contents={"en": f'You have received {data["amount"]} from {user.first_name}.'}
            #     )
            #
            #     # example passing only required values which don't have defaults set
            #     try:
            #         # Create notification
            #         api_response = api_instance.create_notification(notification)
            #         print(api_response)
            #     except onesignal.ApiException as e:
            #         print("Exception when calling DefaultApi->create_notification: %s\n" % e)
            # Notifications.objects.create(
            #     device_id=receiving_user.device_id,
            #     customer_id=receiving_user.customer_id,
            #     topic='Transfer',
            #     message=f'You have received {data["amount"]} from {user.first_name}.',
            # )
            #
            # # Call SentNotifications endpoint for the sending user
            # with onesignal.ApiClient(configuration) as api_client:
            #     # Create an instance of the API class
            #     api_instance = default_api.DefaultApi(api_client)
            #     notification = Notification(
            #         app_id='56618190-490a-4dc6-af2e-71ea67697f99',
            #         include_player_ids=[user.device_id],
            #         contents={"en": f'You have sent {data["amount"]} to {receiving_user.first_name}.'}
            #     )
            #
            #     # example passing only required values which don't have defaults set
            #     try:
            #         # Create notification
            #         api_response = api_instance.create_notification(notification)
            #         print(api_response)
            #     except onesignal.ApiException as e:
            #         print("Exception when calling DefaultApi->create_notification: %s\n" % e)
            # Notifications.objects.create(
            #     device_id=user.device_id,
            #     customer_id=user.customer_id,
            #     topic='Transfer',
            #     message=f'You have sent {data["amount"]} to {receiving_user.first_name}.',
            # )

            return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        return Response({"error": 'something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def makeExternalTransfer(request, pk):
    data = request.data
    user = get_object_or_404(User, customer_id=pk)

    # Check if the bank_pin matches
    if data.get('pin') == user.bank_pin:
        url = "https://api.flutterwave.com/v3/transfers"
        payload = {
            "account_bank": data['bank_code'],  # Flutterwave uses 'account_bank' for the bank code
            "account_number": data['account_number'],
            "amount": data['amount'],
            "narration": data['narration'],
            "currency": "NGN",  # Currency for Flutterwave is specified in this field
            "reference": data['reference'],
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
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = response.json()
        print(response.status_code)
        if response.status_code == 200 and response_data['status'] == 'success':
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
            )
            serializer = TransactionSerializer(bill, many=False)
            print(serializer.data)
            return Response(serializer.data)
    else:
        return Response({"error": "Incorrect bank pin."}, status=status.HTTP_400_BAD_REQUEST)


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
    notifications = Notifications.objects.filter(account_id=pk)
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

        escrow_amount = data.get('amount') * 100  # Assume escrow_amount is part of the request data
        print(escrow_amount)
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
        amount=data['amount'] * 100,
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

    serializer = EscrowSerializer(escrow, many=False)
    return Response(serializer.data)


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
        customer_id=sender.customer_id
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
    data = request.data

    url = "https://api.blochq.io/v1/cards"

    payload = {
        "customer_id": data['customer_id'],
        "brand": data['brand'],
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
        url = f"https://api.blochq.io/v1/cards/secure-data/{card_data.get('id', '')}"

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
            card = Card.objects.create(
                card_id=card_data1.get('id', ''),
                customer_id=data['customer_id'],
                brand=data['brand'],
                pin=card_data1.get('pin', ''),
                card_number=card_data1.get('pan', ''),
                narration=data['narration'],
                account_id=data['account_id'],
                reference=data['reference'],
                currency=data['currency'],
                expiry_month=card_data1.get('expiry_month', ''),
                expiry_year=card_data1.get('expiry_year', ''),
                cvv=card_data1.get('cvv', ''),

            )

            serializer = CardSerializer(card, many=False)
            return Response(serializer.data)


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
    data = request.data

    # Fetch the user by customer_id (pk)
    user = get_object_or_404(User, customer_id=pk)

    bill = Transaction.objects.create(
        receiver_name=user.first_name,
        amount=data['amount'],
        credit=True,
        customer_id=user.customer_id,
        account_number=user.account_number,
        narration='Pay with Card',
        account_id=user.account_id,
        reference='',
        bank=user.bank_name,
    )

    # Serialize the transaction
    serializer = TransactionSerializer(bill, many=False)
    return Response(serializer.data)


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
    paymentLinks = PaymentLink.objects.filter(customer_id=pk)
    serializer = PaymentLinkSerializer(paymentLinks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getPaymentLink(request, pk):
    paymentLink = PaymentLink.objects.get(link_id=pk)
    serializer = PaymentLinkSerializer(paymentLink, many=False)
    return Response(serializer.data)


@api_view(['POST'])
def CreatePaymentLink(request):
    data = request.data
    # url = "https://api.flutterwave.com/v3/payments"
    #
    # payload = {
    #     "tx_ref": generate_random_id(17),  # Replace with your transaction reference
    #     "amount": data['amount'],
    #     "currency": 'NGN',
    #     "redirect_url": 'https://flutterwave.com/ng',
    #     "customer": {
    #         "email": data['email'],
    #         "phone_number": data['phone_number'],
    #         "name": data['name']
    #     },
    #     "customizations": {
    #         "title": 'Oneplug',
    #         "logo": ''
    #     }
    # }
    #
    # headers = {
    #     "Authorization": f"Bearer {secret_key}",  # Replace with your Flutterwave secret key
    #     "Content-Type": "application/json"
    # }
    #
    # response = requests.post(url, json=payload, headers=headers)
    #
    # if response.status_code != 200:
    #     return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #
    # if response.status_code == 200:
    #     response_data = response.json()
    #     print(response_data)
    #     user_data = response_data.get('data')
    #
    #     # Assuming PaymentLink is a Django model where you store payment link details
    link = PaymentLink.objects.create(
        link_id=generate_random_id(17),  # Transaction reference
        link_url='',  # Redirect URL
        customer_id=data.get('customer_id', ''),  # Optionally store customer ID if needed
        name=data['name'],
        description=data.get('description', ''),  # Add description if needed
        amount=data['amount'],  # Payment amount
        currency='NGN',  # Currency
    )


    serializer = PaymentLinkSerializer(link, many=False)
    print(serializer.data)
    return Response(serializer.data)


@api_view(['POST'])
def CreateCheckout(request):
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
