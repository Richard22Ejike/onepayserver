from django.db import models


class Transaction(models.Model):
    sender_account_number = models.CharField(max_length=20, default='')  # The recipient's account number
    bank = models.CharField(max_length=200, default='')
    bank_code = models.CharField(max_length=100, default='')  # The recipient's bank code
    reference = models.CharField(max_length=100, default='')
    account_id = models.CharField(max_length=100, default='')
    customer_id = models.CharField(max_length=100, default='')
    account_number = models.CharField(max_length=200, default='')  # The recipient's account number
    amount = models.IntegerField(default=0)  # The amount to be transferred
    currency = models.CharField(max_length=10, default='NGN')  # The currency of the transfer
    narration = models.TextField(default='')  # The narration for the transfer
    transaction_fee = models.IntegerField(default=0)
    receiver_name = models.CharField(default='', max_length=100)
    date_sent = models.DateTimeField(auto_now_add=True)
    credit = models.BooleanField(default=False)


    REQUIRED_FIELDS = ['sender_account_number', 'receiver_account_number']

    def __str__(self):
        return self.sender_account_number

    def tokens(self):
        pass


class PayBill(models.Model):
    account_id = models.CharField(max_length=15, default='')  # Customer identifier
    amount = models.IntegerField(default=0)  # Amount for the service
    operator_id = models.CharField(max_length=20, default='')  # Type of service
    product_id = models.CharField(max_length=10, default='ONCE')  # Recurrence type
    meter_type = models.CharField(max_length=50, default='')  # Unique reference
    device_number = models.CharField(max_length=100, blank=True,
                                     default='')  # Biller name (Only for Ghana Airtime bills)
    beneficiary_msisdn = models.DateTimeField(auto_now_add=True)
    bill_type = models.CharField(max_length=100, default='')
    REQUIRED_FIELDS = ['country', 'customer', 'amount', 'type']

    def __str__(self):
        return f"{self.account_id}"

    def tokens(self):
        pass


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

    def __str__(self):
        return f"{self.balance} - {self.card_number} - {self.email} - {self.tx_ref}"


class Notification(models.Model):
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
    link_id = models.CharField(max_length=8, default='')
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


class Escrow(models.Model):
    account_id = models.CharField(max_length=100, default='')
    customer_id = models.CharField(max_length=100, default='')
    organization_id = models.CharField(max_length=84, default='')
    environment = models.CharField(max_length=10, default='')
    escrow_description = models.CharField(max_length=255, default='')
    escrow_name = models.CharField(max_length=255, default='')
    receiver_name = models.CharField(max_length=100, default='')
    receiver_account_number = models.CharField(max_length=100, default='')
    receiver_bank_code = models.CharField(max_length=100, default='')
    sender_name = models.CharField(max_length=80, default='')
    receiver_email = models.EmailField(max_length=100, blank=True, default='')
    currency = models.CharField(max_length=10, default='NGN')
    link_url = models.URLField(default='')
    amount = models.IntegerField(default=0)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now=True)
    update_at = models.DateTimeField(auto_now=True)
    is_disabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Escrow"
        verbose_name_plural = "Escrow"

    def __str__(self):
        return self.sender_name
