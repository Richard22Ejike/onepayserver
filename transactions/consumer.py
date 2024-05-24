import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from transactions.models import ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.roomGroupName = 'group'
        self.room_group_name = 'group'

    async def connect(self):
        self.room_group_name = "group_chat_gfg"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_layer
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json["username"]

        # Wrap the synchronous database operation in sync_to_async
        await sync_to_async(ChatMessage.objects.create)(
            escrow_id=text_data_json["escrow_id"],
            sender=text_data_json["sender_id"],
            receiver=text_data_json["receiver_id"],
            message=message
        )

        try:
            # Broadcast the message to all clients in the group
            await self.channel_layer.group_send(
                self.room_group_name, {
                    "type": "send_message",
                    "message": message,
                    "username": username,
                })
            print("Message sent successfully")
        except Exception as e:
            print(f"Error sending message: {e}")

    async def send_message(self, event):
        message = event["message"]
        username = event["username"]
        await self.send(text_data=json.dumps({"message": message, "username": username}))
