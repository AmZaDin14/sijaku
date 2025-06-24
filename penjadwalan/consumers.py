import asyncio
import json

from channels.generic.websocket import AsyncWebsocketConsumer


class GenetikaProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "genetika_progress"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Optional: handle messages from client
        pass

    async def send_progress(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))
