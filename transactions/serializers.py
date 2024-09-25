from rest_framework.serializers import ModelSerializer

from transactions.models import Transaction, PayBill, Card, PaymentLink, Notifications, Escrow, ChatMessage


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


class PaymentLinkSerializer(ModelSerializer):
    class Meta:
        model = PaymentLink
        fields = '__all__'


class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'


class ChatSerializer(ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
