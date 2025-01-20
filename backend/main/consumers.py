import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 当 WebSocket 连接时被调用
        self.room_name = "some_room"  # 房间名，可以根据需要修改
        self.room_group_name = f"chat_{self.room_name}"
        print("try to connect")
        # 加入房间
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # # 向房间内的所有用户发送消息，通知有人加入
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'chat_message',  # 调用 chat_message 方法
        #         'message': f"Player1 has joined the room {self.room_name}",
        #     }
        # )
        await self.accept()

    async def disconnect(self, close_code):
        # 当 WebSocket 断开连接时被调用
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # 处理从客户端接收到的消息
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']
        data = text_data_json['data']

        # 向房间内的所有用户广播消息
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # 调用 chat_message 方法
                'message_type': message_type,
                'data': data,
            }
        )

    # 处理从 group_send 发来的消息
    async def chat_message(self, event):
        # 发送消息到 WebSocket
        await self.send(text_data=json.dumps({
            'type': event['message_type'],
            'data': event['data'],
        }))
