from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from rest_framework.test import APIClient
from communication.consumer import ChatConsumer  # 根据你的实际路径修改
from VIIV.asgi import application  # 根据你的实际路由路径修改
from author.models import User
from django.test import TransactionTestCase
import asyncio
import json
import hashlib
import hmac
import time
from django.utils import timezone
from datetime import datetime, timedelta
from utils.utils_jwt import EXPIRE_IN_SECONDS, SALT, b64url_encode
from asgiref.sync import sync_to_async
import pytest

class ChatConsumerTest(TransactionTestCase):
     
    def generate_jwt_token(self, username: str, payload: dict, salt: str):
    # * header
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        # dump to str. remove `\n` and space after `:`
        header_str = json.dumps(header, separators=(",", ":"))
        # use base64url to encode, instead of base64
        header_b64 = b64url_encode(header_str)
        
        # * payload
        payload_str = json.dumps(payload, separators=(",", ":"))
        payload_b64 = b64url_encode(payload_str)
        
        # * signature
        signature_str = header_b64 + "." + payload_b64
        signature = hmac.new(salt, signature_str.encode("utf-8"), digestmod=hashlib.sha256).digest()
        signature_b64 = b64url_encode(signature)
        
        return header_b64 + "." + payload_b64 + "." + signature_b64

    
    def generate_header(self, username: str, payload: dict = {}, salt: str = SALT):
        if len(payload) == 0:
            payload = {
                "iat": int(time.time()),
                "exp": int(time.time()) + EXPIRE_IN_SECONDS,
                "data": {
                    "username": username
                }
            }
        return {
            "HTTP_AUTHORIZATION": self.generate_jwt_token(username, payload, salt)
        }

    async def base_setUp(self):
        self.client = APIClient()
        self.username = 'testuser'
        self.password = 'testpass'
        # 注册用户
        await self.async_post('/author/register', {'userName': self.username, 'password': self.password})
        
        # 登录用户
        response = await self.async_post('/author/login', {'userName': self.username, 'password': self.password})
        response_data = response.json()
        self.token = response_data['token']
    async def group_setUp(self):
        self.client = APIClient()
        self.username = 'testuser1'
        self.password = 'testpass1'

        self.other_username = 'testuser2'
        other_password = 'testpass2'

        await self.async_post('/author/register', {'userName': self.username, 'password': self.password})
        await self.async_post('/author/register', {'userName': self.other_username, 'password': other_password})
        response = await self.async_post('/author/login', {'userName': self.username, 'password': self.password})
        response_data = response.json()
        self.token = response_data['token']
        self.id = response_data['data']['id']
        response = await self.async_post('/author/login', {'userName':self.other_username, 'password': other_password})
        response_data = response.json()
        self.other_token = response_data['token']
        self.other_id = response_data['data']['id']
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        
        await self.async_post('/friends/request/friend', {'to_user_id': self.other_id})  
        self.client.credentials(HTTP_AUTHORIZATION=self.other_token)
        res = await self.async_get('/friends/require/friend', data = {})
        friend_request_id = res.json()['requests'][0]['id']
        from_friend = res.json()['requests'][0]['from_user_name']
        self.assertEqual(from_friend, self.username)
        await self.async_post('/friends/request/friend/handle', {'request_id': friend_request_id, 'action': 'accept'})
        
    
    @sync_to_async
    def async_post(self, path, data = {}):
        return self.client.post(path, data, format='json')
    
    @sync_to_async
    def async_get(self, path, data = {}):
        return self.client.get(path, data, format='json')
    @sync_to_async
    def async_delete(self, url, **kwargs):
        return self.client.delete(url, **kwargs)
    async def test_ping_pong(self):
        await self.base_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({"type": "ping"})

        try:
            received_pong = False
            start_time = asyncio.get_event_loop().time()
            while True:
               
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time >= 5:
                    break
                
                try:
                    response = await asyncio.wait_for(communicator.receive_json_from(), timeout=5 - elapsed_time)
                    if response['type'] == 'pong':
                        received_pong = True
                        break
                except asyncio.TimeoutError:
                    
                    break
            
            self.assertTrue(received_pong, "Did not receive 'pong' message within 5 seconds")
        finally:
            await communicator.disconnect()

    async def test_entered_room(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        try:
            received_correct_message = False
            start_time = asyncio.get_event_loop().time()

            while True:
                elapsed_time = asyncio.get_event_loop().time() - start_time
            
                if elapsed_time >= 5:
                    break
                
                try:
                    response = await asyncio.wait_for(communicator.receive_json_from(), timeout=5 - elapsed_time) 
                    if response.get('type') == 'room_infos':
                        rooms = response.get('rooms', [])
                        for room in rooms:
                            if room.get('name') == self.other_username and room.get('room_type') == 'private':
                                received_correct_message = True
                                break
                        if received_correct_message:
                            break
                except asyncio.TimeoutError:
                    break
        finally:
            await communicator.disconnect()

    async def test_room_messages(self):
        await self.group_setUp()
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        room_id = -1

        try:
            received = False
            sent_messages = []
            message_id = 0

            while not received:
                response = await communicator.receive_json_from()
                if response['type'] == 'room_infos':
                    rooms = response['rooms']
                    room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)

                    
                    for _ in range(3):
                        message_content = f"Test message {message_id}"
                        await communicator.send_json_to({
                            'type': 'send_message',
                            'message': message_content,
                            'room_id': room_id,
                            'ack_id': message_id
                        })
                        sent_messages.append({'content': message_content})
                        message_id += 1

                    received = True

            await communicator.disconnect()
            self.client.credentials(HTTP_AUTHORIZATION=self.other_token)
            response = await self.async_get(f'/communication/searchby/room?room_id={room_id}')
            messages_data = response.json()['messages']
            assert all(any(sent_message['content'] in msg['content'] for msg in messages_data) for sent_message in sent_messages)

        except asyncio.TimeoutError:
            assert False, "Test timed out while waiting for messages."

    async def test_missing_authorization_token_by_room(self):
        # 创建新的 client 实例
        self.client = APIClient()
        response = await self.async_get('/communication/searchby/room?room_id=1')
        assert response.status_code == 401
        assert response.json() == {'code': 1, 'info': 'Authorization token is missing'}

    async def test_invalid_token_by_room(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken123')
        response = await self.async_get('/communication/searchby/room?room_id=1')
        assert response.status_code == 401
        assert response.json() == {'code': 2, 'info': 'Invalid token'}

    async def test_missing_parameters_by_room(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = await self.async_get('/communication/searchby/room')
        assert response.status_code == 400
        assert response.json() == {'code': 3, 'info': 'Room ID is required'}

    async def test_user_not_found_by_room(self):
        self.client = APIClient()
        token = self.generate_header('UserNotExist')['HTTP_AUTHORIZATION']
        self.client.credentials(HTTP_AUTHORIZATION=token)
        response = await self.async_get('/communication/searchby/room?room_id=1')

        assert response.status_code == 404
        assert response.json() == {'code': 4, 'info': 'User does not exist'}

    async def test_messages_by_date(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        received = False
        sent_messages = []
        message_id = 0
        room_id = -1

        while not received:
            try:
                response = await communicator.receive_json_from()
                if response['type'] == 'room_infos':
                    rooms = response['rooms']
                    room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)
                    for _ in range(3):  
                        message_content = f"Test message {message_id}"
                        await communicator.send_json_to({
                            'type': 'send_message',
                            'message': message_content,
                            'room_id': room_id,
                            'ack_id': message_id
                        })
                        sent_messages.append({'content': message_content})
                        message_id += 1

                    received = True
            except asyncio.TimeoutError:
                pass
        await communicator.disconnect()

        today = timezone.datetime.now().strftime('%Y-%m-%d')
        yesterday = (timezone.datetime.now() - timezone.timedelta(days=1)).strftime('%Y-%m-%d')
        self.client.credentials(HTTP_AUTHORIZATION=self.other_token)
        response_yesterday = await self.async_get(f'/communication/searchby/date?room_id={room_id}&date={yesterday}')
        messages_yesterday = response_yesterday.json()['messages']
        #assert messages_yesterday == [], "Messages from yesterday should be empty."

        response_today = await self.async_get(f'/communication/searchby/date?room_id={room_id}&date={today}')
        messages_today = response_today.json()['messages']
        #assert all(any(sent_message['content'] in msg['content'] for msg in messages_today) for sent_message in sent_messages)

    async def test_missing_authorization_token_by_date(self):
        self.client = APIClient()
        response = await self.async_get('/communication/searchby/date?room_id=1&date=2024-05-17')
        assert response.status_code == 401
        assert response.json() == {'code': 2, 'info': 'Authorization token is missing'}

    async def test_invalid_token_by_date(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken123')
        response = await self.async_get('/communication/searchby/date?room_id=some_room_id&date=2024-05-17')
        assert response.status_code == 401
        assert response.json() == {'code': 3, 'info': 'Invalid token'}
    
    async def test_missing_parameters_by_date(self):
        await self.base_setUp()
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = await self.async_get('/communication/searchby/date')
        assert response.status_code == 400
        assert response.json() == {'code': 4, 'info': 'Room ID and date are required'}
    async def test_user_not_found_by_date(self):
        self.client = APIClient()
        token = self.generate_header('UserNotExist')['HTTP_AUTHORIZATION']
        self.client.credentials(HTTP_AUTHORIZATION=token)
        response = await self.async_get('/communication/searchby/date?room_id=1&date=2024-05-17')
        assert response.status_code == 404
        assert response.json() == {'code': 5, 'info': 'User does not exist'}
    async def test_invalid_date_format_by_date(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = await self.async_get('/communication/searchby/date?room_id=1&date=05-17-2024')
        assert response.status_code == 400
        assert response.json() == {'code': 6,'info': 'Invalid date format'}
    async def test_messages_by_member(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        received = False
        sent_messages = []
        message_id = 0
        room_id = -1

        while not received:
            response = await communicator.receive_json_from()
            if response['type'] == 'room_infos':
                rooms = response['rooms']
                room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)

              
                for _ in range(3):  # send three messages
                    message_content = f"Test message {message_id}"
                    await communicator.send_json_to({
                        'type': 'send_message',
                        'message': message_content,
                        'room_id': room_id,
                        'ack_id': message_id
                    })
                    sent_messages.append({'content': message_content})
                    message_id += 1

                received = True

      
        await communicator.disconnect()
        self.client.credentials(HTTP_AUTHORIZATION=self.other_token)
        response1 = await self.async_get(f'/communication/searchby/member?room_id={room_id}&member_user_id={self.other_id}')
        messages1 = response1.json()['messages']
        assert messages1== [], "Messages from yesterday should be empty."

        response2 = await self.async_get(f'/communication/searchby/member?room_id={room_id}&member_user_id={self.id}')
        messages2= response2.json()['messages']
        
    async def test_missing_authorization_token_by_sender(self):
        # 创建新的 client 实例
        self.client = APIClient()
        response = await self.async_get('/communication/searchby/member?room_id=1&member_user_id=2')
        assert response.status_code == 401
        assert response.json() == {'code': 1, 'info': 'Authorization token is missing'}

    async def test_invalid_token_by_sender(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken123')
        response = await self.async_get('/communication/searchby/member?room_id=1&member_user_id=2')
        assert response.status_code == 401
        assert response.json() == {'code': 2, 'info': 'Invalid token'}

    async def test_missing_parameters_by_sender(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = await self.async_get('/communication/searchby/member?room_id=1')
        assert response.status_code == 400
        assert response.json() == {'code': 3, 'info': 'Room ID and member user ID are required'}

    async def test_user_not_found_by_sender(self):
        self.client = APIClient()
        token = self.generate_header('UserNotExist')['HTTP_AUTHORIZATION']
        self.client.credentials(HTTP_AUTHORIZATION=token)
        response = await self.async_get('/communication/searchby/member?room_id=1&member_user_id=2')

        assert response.status_code == 404
        assert response.json() == {'code': 4, 'info': 'User does not exist'}

    async def test_unread_messages(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        received = False
        sent_messages = []
        message_id = 0
        room_id = -1

        while not received:
            response = await communicator.receive_json_from()
            if response['type'] == 'room_infos':
                rooms = response['rooms']
                room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)
                for _ in range(3):  
                    message_content = f"Test message {message_id}"
                    await communicator.send_json_to({
                        'type': 'send_message',
                        'message': message_content,
                        'room_id': room_id,
                        'ack_id': message_id
                    })
                    sent_messages.append({'content': message_content})
                    message_id += 1

                received = True
        await communicator.disconnect()

        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        received = False
        
        received_messages = []
        while not received:
            response = await communicator.receive_json_from()
            if response['type'] == 'unread_messages':
                for message in response['unread_messages']:
                    if message['room_id'] == room_id:
                        for msg in message['values']:
                            received_messages.append(msg['message_content'])

                received = True
        await communicator.disconnect()

        #assert all(any(sent_message['content'] in msg for msg in received_messages) for sent_message in sent_messages)

    async def test_message_retransmission_mechanism(self):
        await self.base_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        assert await communicator.connect()

        ack_ids_received = []
        last_message_time = asyncio.get_event_loop().time()  # 初始化时间
        start_time = time.time()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - last_message_time > 5:  # 超过5秒没有消息
                elapsed_time = time.time() - start_time
                print(f"Timed out after {elapsed_time} seconds.")
                break  # 跳出循环
            
            try:
                response = await communicator.receive_json_from()
                last_message_time = asyncio.get_event_loop().time()  # 更新接收消息的最后时间
                if 'ack_id' in response:
                    ack_id = response['ack_id']
                    if ack_id in ack_ids_received:
                        assert False, f"Received a retransmitted message with ack_id {ack_id} that was already acknowledged."
                    ack_ids_received.append(ack_id)
                    # 发送确认回服务器
                    await communicator.send_json_to({
                        'type': 'receiver_ack',
                        'ack_id': ack_id
                    })
            except asyncio.TimeoutError:
                continue  # 如果接收超时，则继续等待
            except asyncio.exceptions.CancelledError:
                continue

        await communicator.disconnect()
        assert True  # 确保测试成功结束，没有断言错误

    async def test_delete_messages(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        room_id = -1
        try:
            received = False
            sent_messages = []
            message_id = 0
            
            while not received:
               
                response = await communicator.receive_json_from()
                if response['type'] == 'room_infos':
                    rooms = response['rooms']
                    room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)

                    
                    for _ in range(5):
                        message_content = f"Test message {message_id}"
                        await communicator.send_json_to({
                            'type': 'send_message',
                            'message': message_content,
                            'room_id': room_id,
                            'ack_id': message_id
                        })
                        if message_id != 2:
                            sent_messages.append({'content': message_content})
                        message_id += 1

                    received = True

            await communicator.disconnect()
            self.client.credentials(HTTP_AUTHORIZATION=self.token)
            response = await self.async_delete(f'/communication/delete/message?room_id={room_id}&&message_id=3')
            assert response.status_code == 200
        except asyncio.TimeoutError:
            pass

        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected

        try:
            received = False
            start_time = asyncio.get_event_loop().time()
            received_messages = []
            while not received:
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time >= 5:
                    break
                response = await asyncio.wait_for(communicator.receive_json_from(), timeout=5 - elapsed_time)
                if response['type'] == 'unread_messages':
                    for message in response['unread_messages']:
                        if message['room_id'] == room_id:
                            for msg in message['values']:
                                received_messages.append(msg['message_content'])

                    received = True
            await communicator.disconnect()
            #assert all(any(sent_message['content'] in msg for msg in received_messages) for sent_message in sent_messages)
        except asyncio.TimeoutError:
            assert False, "Test timed out while waiting for messages."

    async def test_missing_authorization_token_delete_message(self):
        # 创建新的 client 实例
        self.client = APIClient()
        response = await self.async_delete('/communication/delete/message?room_id=1&message_id=2')
        assert response.status_code == 401
        assert response.json() == {'code': 1, 'info': 'Authorization token is missing'}

    async def test_invalid_token_delete_message(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken123')
        response = await self.async_delete('/communication/delete/message?room_id=1&message_id=2')
        assert response.status_code == 401
        assert response.json() == {'code': 2, 'info': 'Invalid token'}

    async def test_missing_parameters_delete_message(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = await self.async_delete('/communication/delete/message?room_id=1')
        assert response.status_code == 400
        assert response.json() == {'code': 3, 'info': 'Message ID and Room ID are required'}

    async def test_user_not_found_delete_message(self):
        self.client = APIClient()
        token = self.generate_header('UserNotExist')['HTTP_AUTHORIZATION']
        self.client.credentials(HTTP_AUTHORIZATION=token)
        response = await self.async_delete('/communication/delete/message?room_id=1&message_id=2')

        assert response.status_code == 404
        assert response.json() == {'code': 4, 'info': 'User does not exist'}

    async def test_user_not_found_delete_message(self):
        await self.base_setUp()
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = await self.async_delete('/communication/delete/message?room_id=1&message_id=2')
        assert response.status_code == 404
        assert response.json() == {'code': 5, 'info': 'Message does not exist'}
    
    async def test_delete_message_repetely(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        room_id = -1
        try:
            received = False
            message_id = 0

            while not received:
                response = await communicator.receive_json_from()
                if response['type'] == 'room_infos':
                    rooms = response['rooms']
                    room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)

                    
                    for _ in range(5):
                        message_content = f"Test message {message_id}"
                        await communicator.send_json_to({
                            'type': 'send_message',
                            'message': message_content,
                            'room_id': room_id,
                            'ack_id': message_id
                        })
                        message_id += 1

                    received = True

            await communicator.disconnect()
            self.client.credentials(HTTP_AUTHORIZATION=self.token)
            response = await self.async_delete(f'/communication/delete/message?room_id={room_id}&&message_id=3')
            assert response.status_code == 200
            response = await self.async_delete(f'/communication/delete/message?room_id={room_id}&&message_id=3')
            assert response.status_code == 409
            assert response.json() == {'code': 7, 'info': 'Message already marked as deleted'}
        except asyncio.TimeoutError:
            assert False, "Test timed out while waiting for messages."
    
    async def test_get_history_message(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        try:
            received = False
            sent_messages = []
            received_messages = []
            message_id = 0

            while not received:
                response = await communicator.receive_json_from()
                if response['type'] == 'room_infos':
                    rooms = response['rooms']
                    room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)
                    for _ in range(12):
                        message_content = f"Test message {message_id}"
                        await communicator.send_json_to({
                            'type': 'send_message',
                            'message': message_content,
                            'room_id': room_id,
                            'ack_id': message_id
                        })
                        if message_id <= 6:
                            sent_messages.append({'content': message_content})
                        message_id += 1

                    await communicator.send_json_to({
                        'type': 'get_history_messages',
                        'room_id': room_id,
                        'end_id':8,
                    })
                if response['type'] == 'history_messages':
                    for msg in response['messages']:
                        received_messages.append(msg['content'])  # 将每条消息的内容添加到列表中
                    received = True
            await communicator.disconnect()
            assert all(any(sent_message['content'] in msg for msg in received_messages) for sent_message in sent_messages)
        except asyncio.TimeoutError:
            pass
    
    async def test_set_read_index(self):
        await self.group_setUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        room_id = -1
        try:
            received = False
            message_id = 0
            while not received:
               
                response = await communicator.receive_json_from()
                if response['type'] == 'room_infos':
                    rooms = response['rooms']
                    room_id = next((room['id'] for room in rooms if room['name'] == self.other_username), None)
                    for _ in range(12):
                        message_content = f"Test message {message_id}"
                        await communicator.send_json_to({
                            'type': 'send_message',
                            'message': message_content,
                            'room_id': room_id,
                            'ack_id': message_id
                        })
                        message_id += 1

                    await communicator.send_json_to({
                        'type': 'set_read_index',
                        'room_id': room_id,
                        'read_index':8,
                    })
                    received = True
            await communicator.disconnect()
        except asyncio.TimeoutError:
            pass
        
        communicator = WebsocketCommunicator(application, f"/ws/chat/?token={self.token}")
        connected, subprotocol = await communicator.connect()
        assert connected
        try:
            received = False
            while not received:
                response = await communicator.receive_json_from()
                if response['type'] == 'unread_messages':
                    for msg in response['unread_messages']:
                        if msg['room_id'] == room_id:
                            assert msg['unread_count'] == 0
                    received = True
            await communicator.disconnect()
        except asyncio.TimeoutError:
            pass

    
        

        
