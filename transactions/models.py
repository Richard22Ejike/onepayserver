from django.db import models
from users.models import User


class Transaction(models.Model):
    sender_account_number = models.CharField(max_length=20, default='')  # The recipient's account number
    bank = models.CharField(max_length=200, default='')
    bank_code = models.CharField(max_length=100, default='')  # The recipient's bank code
    reference = models.CharField(max_length=100, default='')
    account_id = models.CharField(max_length=100, default='')
    customer_id = models.CharField(max_length=100, default='')
    account_number = models.CharField(max_length=200, default='')  # The recipient's account number
    amount = models.IntegerField(default=0)  # The amount to be transferred
    currency = models.CharField(max_length=100, default='NGN')  # The currency of the transfer
    narration = models.TextField(default='')  # The narration for the transfer
    transaction_fee = models.IntegerField(default=0)
    user_balance = models.IntegerField(default=0)
    receiver_name = models.CharField(default='', max_length=100)
    date_sent = models.DateTimeField(auto_now_add=True)
    credit = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['sender_account_number', 'receiver_account_number']

    def __str__(self):
        return self.sender_account_number

    def tokens(self):
        pass


class PayBill(models.Model):
    name = models.CharField(max_length=200, default='')
    customer_id = models.CharField(max_length=1000, default='')
    account_id = models.CharField(max_length=1050, default='')  # Customer identifier
    amount = models.DecimalField(max_digits=100, decimal_places=2, default=0)  # Amount for the service
    operator_id = models.CharField(max_length=2000, default='')  # Type of service
    order_id = models.CharField(max_length=5000, default='')  # Unique order identifier
    meter_type = models.CharField(max_length=5000, default='')  # Meter type (if applicable)
    device_number = models.CharField(max_length=1000, blank=True, default='')  # Device number or smart card number
    order_date = models.DateTimeField(auto_now_add=True)  # Order date
    status = models.CharField(max_length=500, default='')  # Status of the transaction
    remark = models.TextField(blank=True, default='')  # Additional remarks about the transaction
    order_type = models.CharField(max_length=100, default='')  # Type of order/service
    service_type = models.CharField(max_length=100, default='')  # Type of order/service
    mobile_network = models.CharField(max_length=500, blank=True, default='')  # Mobile network (if applicable)
    mobile_number = models.CharField(max_length=150, blank=True, default='')  # Beneficiary mobile number
    meter_token = models.TextField(blank=True, default='')  # Meter token (if applicable)
    wallet_balance = models.DecimalField(max_digits=150, decimal_places=4, default=0)  # Wallet balance

    REQUIRED_FIELDS = ['account_id', 'amount', 'order_id', 'status']

    def __str__(self):
        return f"{self.order_id} - {self.status}"

    def tokens(self):
        return self.meter_token


class Card(models.Model):
    card_id = models.CharField(max_length=100, default='')
    account_id = models.CharField(max_length=100, default='')
    customer_id = models.CharField(max_length=100, default='')
    name = models.CharField(max_length=100, default='')
    brand = models.CharField(max_length=100, default='')
    balance = models.FloatField(default=0.0)  # Amount to be charged for the transaction
    card_number = models.CharField(max_length=160)  # Number on the cardholder's card
    cvv = models.CharField(max_length=40)  # Card security code
    expiry_month = models.CharField(max_length=20)  # Expiration month of the card
    expiry_year = models.CharField(max_length=20)  # Expiration year of the card
    email = models.EmailField()  # Customer's email address
    pin = models.CharField(default='', max_length=20)
    currency = models.CharField(default='', max_length=10)
    tx_ref = models.CharField(max_length=50)  # Unique reference for the transaction
    linked = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    card_type = models.CharField(default='')

    def __str__(self):
        return f"{self.balance} - {self.card_number} - {self.email} - {self.tx_ref}"


class Notifications(models.Model):
    device_id = models.CharField(max_length=800, default='')
    customer_id = models.CharField(max_length=100, default='')
    topic = models.CharField(max_length=100, default='')
    message = models.CharField(max_length=500, )

    def __str__(self):
        return f"{self.customer_id} - {self.topic} - {self.message} "


class PaymentLink(models.Model):
    account_id = models.CharField(max_length=100, default='')
    customer_id = models.CharField(max_length=100, default='')
    organization_id = models.CharField(max_length=24, default='')
    environment = models.CharField(max_length=10, default='')
    description = models.CharField(max_length=255, default='')
    name = models.CharField(max_length=255, default='')
    link_id = models.CharField(max_length=255, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    currency = models.CharField(max_length=10, default='')
    link_url = models.URLField(default='')
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)
    update_at = models.DateTimeField(auto_now=True)
    is_disabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Payment Link"
        verbose_name_plural = "Payment Links"

    def __str__(self):
        return self.name


class PaymentDetails(models.Model):
    customer_id = models.CharField(max_length=100, default='')
    name = models.CharField(max_length=255, default='')
    email = models.EmailField(max_length=255)
    phone_number = models.IntegerField( default=0)
    link = models.ForeignKey(PaymentLink, related_name="payment_details", on_delete=models.CASCADE)
    narration = models.CharField(default='')
    amount = models.IntegerField(default=0)
    payment_type = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Detail"
        verbose_name_plural = "Payment Details"

    def __str__(self):
        return self.name


class Escrow(models.Model):
    account_id = models.CharField(max_length=100, default='')
    customer_id = models.CharField(max_length=100, default='')
    escrow_description = models.CharField(max_length=255, default='')
    escrow_name = models.CharField(max_length=255, default='')
    escrow_Status = models.CharField(max_length=100, default='')
    payment_type = models.CharField(max_length=100, default='')
    role = models.CharField(max_length=100, default='')
    role_paying = models.CharField(max_length=100, default='')
    estimated_days = models.CharField(max_length=100, default='')
    number_milestone = models.CharField(max_length=100, default='')
    milestone = models.CharField(max_length=100, default='')
    reference = models.CharField(max_length=100, default='')
    sender_name = models.CharField(max_length=80, default='')
    receiver_email = models.EmailField(max_length=100, blank=True, default='')
    receiver_id = models.IntegerField(default=0)
    currency = models.CharField(max_length=10, default='NGN')
    link_url = models.URLField(default='')
    make_payment = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    answered = models.BooleanField(default=False)
    amount = models.IntegerField(default=0)
    transaction_fee = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)
    update_at = models.DateTimeField(auto_now=True)
    dispute = models.CharField(max_length=80, default='')
    is_disabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Escrow"
        verbose_name_plural = "Escrow"

    def __str__(self):
        return self.sender_name


class ChatMessage(models.Model):
    escrow_id = models.IntegerField(default=0)
    chat_id = models.CharField(default='')
    sender_by = models.IntegerField(default=0)
    sender = models.ForeignKey(User, related_name='sent_message', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_message', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
