from datetime import date

import requests
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from transactions.models import Transaction, PayBill, PaymentLink, Card, Notification, Escrow
from transactions.serializers import TransactionSerializer, PayBillSerializer, PaymentLinkSerializer, CardSerializer, \
    NotificationSerializer, EscrowSerializer
from users.keys import secret_key
from users.models import User
from users.utils import send_email_to_user


@api_view(['POST'])
def makeBillPayment(request, pk):
    data = request.data
    # Fetch the user by customer_id (pk)
    user = get_object_or_404(User, customer_id=pk)

    # Check if the bank_pin matches
    if data.get('pin') == user.bank_pin:
        payload = {
            "amount": data['amount'],
            "product_id": data['product_id'],
            "operator_id": data['operator_id'],
            "account_id": data['account_id'],
            "device_details": {
                "meter_type": data['meter_type'],
                "device_number": data['device_number'],
                "beneficiary_msisdn": data['beneficiary_msisdn'],
            }
        }

        url = f"https://api.blochq.io/v1/bills/payment?bill={data['bill_type']}"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {secret_key}"
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            # If the request was not successful, return an error response
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if response.status_code == 200:
            bill = PayBill.objects.create(
                amount=data['amount'],
                product_id=data['product_id'],
                operator_id=data['operator_id'],
                account_id=data['account_id'],
                meter_type=data['meter_type'],
                bill_type=data['bill_type'],
                device_number=data['device_number'],
                beneficiary_msisdn=data['beneficiary_msisdn'],
            )

            serializer = PayBillSerializer(bill, many=False)
            return Response(serializer.data)


@api_view(['POST'])
def makeInternelTransfer(request, pk):
    data = request.data
    # Fetch the user by customer_id (pk)
    user = get_object_or_404(User, customer_id=pk)
    # Check if the bank_pin matches
    if data.get('pin') == user.bank_pin:
        url = "https://api.blochq.io/v1/transfers/internal"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {secret_key}"
        }
        payload = {
            "amount": data['amount'],
            "to_account_id": data['account_number'],
            "narration": data['narration'],
            "from_account_id": data['account_id'],
            "reference": data['reference'],
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            # If the request was not successful, return an error response
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if response.status_code == 200:
            bill = Transaction.objects.create(
                receiver_name=data['receiver_name'],
                amount=data['amount'],
                bank_code=data['bank_code'],
                account_number=data['account_number'],
                narration=data['narration'],
                account_id=data['account_id'],
                bank=data['bank'],
                credit=data['credit'],
                customer_id=user.customer_id
            )

            # Serialize the transaction
            serializer = TransactionSerializer(bill, many=False)
            return Response(serializer.data)
    else:
        return Response({"error": "Incorrect bank pin."}, status=400)


@api_view(['POST'])
def makeExternalTransfer(request, pk):
    data = request.data
    user = get_object_or_404(User, customer_id=pk)
    # Check if the bank_pin matches
    if data.get('pin') == user.bank_pin:
        url = "https://api.blochq.io/v1/transfers"
        payload = {
            "amount": data['amount'],
            "bank_code": data['bank_code'],
            "account_number": data['account_number'],
            "narration": data['narration'],
            "account_id": data['account_id'],
            "reference": data['reference'],
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {secret_key}"
        }
        # Check the user's KYC tier and apply corresponding limits
        if user.kyc_tier == 0:
            # Tier 0 limits
            max_deposit = 50000
            max_transfer_withdrawal = 3000
            max_balance = 300000
            max_daily_debit = 30000
        elif user.kyc_tier == 1:
            # Tier 1 limits
            max_deposit = 200000
            max_transfer_withdrawal = 10000
            max_balance = 500000
            max_daily_debit = 30000
        elif user.kyc_tier == 2:
            # Tier 2 limits
            max_deposit = 5000000
            max_transfer_withdrawal = 1000000
            max_balance = None  # No balance limit
            max_daily_debit = 30000
        else:
            # Default to Tier 3 limits
            max_deposit = 5000000
            max_transfer_withdrawal = 1000000
            max_balance = None  # No balance limit
            max_daily_debit = 30000

        # Check if the transaction exceeds the limits
        if data['amount'] > max_deposit:
            return Response({'error': 'Amount exceeds maximum deposit limit'}, status=status.HTTP_400_BAD_REQUEST)
        if data['amount'] > max_transfer_withdrawal:
            return Response({'error': 'Amount exceeds maximum transfer/withdrawal limit'},
                            status=status.HTTP_400_BAD_REQUEST)
        if max_balance is not None and (user.balance + data['amount']) > max_balance:
            return Response({'error': 'Transaction exceeds maximum balance limit'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the cumulative daily debit amount exceeds the limit
        today_debit_total = \
            Transaction.objects.filter(customer_id=user.customer_id,
                                       created__date=date.today(),
                                       credit=False).aggregate(Sum('amount'))[
                'amount__sum'] or 0
        if today_debit_total + data['amount'] > max_daily_debit:
            return Response({'error': 'Transaction exceeds maximum daily cumulative debit amount limit'},
                            status=status.HTTP_400_BAD_REQUEST)

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            # If the request was not successful, return an error response
            return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if response.status_code == 200:
            bill = Transaction.objects.create(
                receiver_name=data['receiver_name'],
                amount=data['amount'],
                bank_code=data['bank_code'],
                bank=data['bank'],
                account_number=data['account_number'],
                narration=data['narration'],
                account_id=data['account_id'],
                reference=data['reference'],
                credit=data['credit'],
            )
            serializer = PayBillSerializer(bill, many=False)
            return Response(serializer.data)
    else:
        return Response({"error": "Incorrect bank pin."}, status=400)


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
def getTransactions(request, pk):
    transactions = Transaction.objects.filter(customer_id=pk).order_by('-id')
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def findAccountbyId(request, pk):
    data = request.data
    transactions = Transaction.objects.filter(account_id=pk)
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getNotifications(request, pk):
    notifications = Notification.objects.filter(account_id=pk)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def SentNotifications(request):
    data = request.data
    notification = Notification.objects.create(
        customer_id=data['customer_id'],
        topic=data['topic'],
        message=data['message'],
    )

    serializer = NotificationSerializer(notification, many=False)
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
def CreateEscrow(request, pk):
    data = request.data
    print(data['customer_id'])

    # Fetch the user by customer_id (pk)
    user = get_object_or_404(User, customer_id=pk)
    # Check if the bank_pin matches
    if data.get('pin') == user.bank_pin:
        escrow = Escrow.objects.create(
            customer_id=data['customer_id'],
            escrow_description=data['escrow_description'],
            escrow_name=data['escrow_name'],
            receiver_name=data['receiver_name'],
            receiver_email=data['receiver_email'],
            receiver_account_number=data['receiver_account_number'],
            receiver_bank_code=data['receiver_bank_code'],
            sender_name=data['sender_name'],
            account_id=data['account_id'],
            start_time=data['start_time'],
            end_time=data['end_time'],
        )

        serializer = EscrowSerializer(escrow, many=False)
        return Response(serializer.data)
    else:
        return Response({"error": "Incorrect bank pin."}, status=400)


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
    escrows = Escrow.objects.filter(customer_id=pk)
    serializer = EscrowSerializer(escrows, many=True)
    return Response(serializer.data)


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
def linkCard(request, pk):
    data = request.data
    card = Card.objects.get(customer_id=pk)
    url = "https://api.blochq.io/v1/cards/fixed-account/link"

    payload = {
        "card_id": card.card_id,
        "account_id": data.get('account_id')
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


@api_view(['GET'])
def getPaymentLinks(request, pk):
    paymentLinks = PaymentLink.objects.filter(customer_id=pk)
    serializer = PaymentLinkSerializer(paymentLinks, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def CreatePaymentLink(request):
    data = request.data
    url = "https://api.blochq.io/v1/paymentlinks"

    payload = {
        "name": data['name'],
        "description": data['description'],
        "amount": data['amount'],
        "currency": "NGN"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {secret_key}"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        return Response({'error': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if response.status_code == 200:
        response_data = response.json()
        print(response_data)
        user_data = response_data.get('data')
        link = PaymentLink.objects.create(
            link_id=user_data.get('link_id', ''),
            link_url=user_data.get('link_url', ''),
            customer_id=data['customer_id'],
            name=data['name'],
            description=data['description'],
            amount=data['amount'],
            currency=data['currency'],

        )

        serializer = PaymentLinkSerializer(link, many=False)
        print(serializer.data)
        return Response(serializer.data)


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

# Create your views here.
