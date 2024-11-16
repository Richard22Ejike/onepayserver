from rest_framework.serializers import ModelSerializer

from transactions.models import Transaction, PayBill, Card, PaymentDetails, Notifications, Escrow, ChatMessage, \
    PaymentLink


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class PayBillSerializer(ModelSerializer):
    class Meta:
        model = PayBill
        fields = '__all__'


class CardSerializer(ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'


class EscrowSerializer(ModelSerializer):
    class Meta:
        model = Escrow
        fields = '__all__'


class PaymentDetailsSerializer(ModelSerializer):
    class Meta:
        model = PaymentDetails
        fields = '__all__'


class PaymentLinkSerializer(ModelSerializer):
    payment_details = PaymentDetailsSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentLink
        fields = ['id', 'account_id', 'customer_id', 'organization_id', 'environment', 'description',
                  'name', 'link_id', 'country', 'currency', 'link_url', 'amount', 'created_at',
                  'update_at', 'is_disabled', 'payment_details']


class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'


class ChatSerializer(ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
