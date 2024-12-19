from rest_framework.serializers import ModelSerializer

from nearme.models import NearMeProduct, ChatNearMeRoom


class NearMeProductSerializer(ModelSerializer):
    class Meta:
        model = NearMeProduct
        fields = '__all__'


class ChatNearMeRoomSerializer(ModelSerializer):
    class Meta:
        model = ChatNearMeRoom
        fields = '__all__'
