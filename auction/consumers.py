import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Define the group name for all audience members
        self.auction_group_name = 'auction_updates'

        # Join the auction group
        await self.channel_layer.group_add(
            self.auction_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the auction group on disconnect
        await self.channel_layer.group_discard(
            self.auction_group_name,
            self.channel_name
        )

    # Method called by the channel layer to push updates
    # The name 'auction_update' MUST match the 'type' key used in channel_layer.group_send
    async def auction_update(self, event):
        # Unpack the action and data sent from views.py (or admin control logic)

        # Send data back to the WebSocket connection in JSON format
        await self.send(text_data=json.dumps({
            'action': event['action'],
            'data': event['data']
        }))