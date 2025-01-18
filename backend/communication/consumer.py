import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import django
django.setup()

from author.models import User
from communication.models import MessageStatus,ConversationMember  
from group.models import ChatRoom
from utils.utils_jwt import  check_jwt_token
from asgiref.sync import sync_to_async
from django.db.models import  F
from urllib.parse import parse_qs
import asyncio
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # 根据需要配置级别


# 定义最大重试次数
MAX_RETRIES = 3
# 定义重试间隔时间（例如5秒）
RETRY_INTERVAL = 5  # in seconds


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_ids = {} # 使用实例变量存储已处理的 IDs
        self.message_send_status = {}  # 使用实例变量跟踪消息发送状态
        self.message_counter = 0  # 初始化消息计数器，用于生成唯一的 ack_id

    async def connect(self):
        self.user = None
        self.rooms = []
        token = self._extract_token()
        if not token:
            logger.info("Connection closed: No token provided")
            await self.close(code=4000)  # Token is mandatory
            return

        self.user = await self.get_user_by_token(token)
        
        if not self.user:
            logger.info(f"Connection closed: Invalid token {token}")
            await self.close(code=4000)  # Authentication failed
            return

        await self.accept()
        await self.process_rooms()

    def _extract_token(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token_list = query_params.get('token')
        return token_list[0] if token_list else None

    async def process_rooms(self):
        self.rooms = await self.get_user_rooms()
        room_infos = await self.collect_room_infos()
        await self.send(text_data=json.dumps({
            'type': 'room_infos',
            'rooms': room_infos
        }))
        for room in self.rooms:
            await self.channel_layer.group_add(
                f"chat_{room.id}",
                self.channel_name
            )
        await self.send_unread_messages()

    async def collect_room_infos(self):
        room_infos = []
        for room in self.rooms:
            avatar = await self.get_room_avatar(room, self.user)
            name = await self.get_room_name(room, self.user)
            room_infos.append({
                'id': room.id,
                'name': name,
                'avatar': avatar,
                "room_type":room.type
            })
        return room_infos

    async def disconnect(self, close_code):
        # 遍历用户加入的所有聊天室，并从中移除用户
        for room in self.rooms:
            await self.channel_layer.group_discard(
                f'chat_{room.id}',
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data["type"]
        if not message_type:
            logger.error("Message type not provided")
            await self.close(code=4001)  # 发送错误代码给客户端
            return
        
        if message_type == 'ping':
            await self.send(json.dumps({"type": "pong"}))
            return  
        elif message_type == 'receiver_ack':
            await self.handle_receiver_ack(data['ack_id'])
            return
        
        room_id = data.get('room_id')
        if not room_id:
            logger.error("Room ID not provided")
            await self.close(code=4002)  # 发送错误代码给客户端
            return
        
        room = await self.get_room_by_name(room_id)
        if not room:
            logger.error("ChatRoom not found")
            await self.close(code=4003)  # 发送错误代码给客户端
            return
        
        # 通过调度方法处理不同类型的消息
        await self.dispatch_message(room, message_type, data)

    async def dispatch_message(self, room, type, data):
        # 根据不同的消息类型执行不同的操作
        if type == "send_message":
            await self.handle_send_message(room, data)
        elif type == "get_history_messages":
            await self.handle_history_messages(room, data)
        elif type == "get_message_detail":
            await self.handle_message_detail(room, data)
        elif type == "get_reply_message":
            await self.handle_get_reply_message(room, data)
        elif type == "set_read_index":
            await self.set_read_index(room.id, data['read_index'])
            await self.send(json.dumps({"set read index success":data['read_index']}))
       

    async def handle_send_message(self, room, data):

        ack_id = data['ack_id']  # 客户端生成的唯一消息 ID
        if self.already_processed(ack_id):
             await self.send_ack(ack_id,self.processed_ids[ack_id])
             return
        reply_id = data.get('reply_id', -1)
        message_content = data['message']
        sender_id = self.user.id
        message_payload = await self.save_message_content(message_content, room.id, sender_id, reply_id)
        await self.channel_layer.group_send(f'chat_{room.id}', message_payload)
        
        self.processed_ids[ack_id] = message_payload['message_id']
        await self.send_ack(ack_id,self.processed_ids[ack_id])

        
    ## 发送 ack 到客户端
    async def send_ack(self, ack_id,message_id):
        # 发送 ack 到客户端
        await self.send(text_data=json.dumps({
            'type': 'acknowledge',
            'ack_id': ack_id,
            'message_id':message_id,
        }))

    def already_processed(self, message_id):
        # 检查消息 ID 是否已处理
        return message_id in self.processed_ids
    async def handle_history_messages(self, room, data):
        end_id = data["end_id"]
        messages = await self.get_certain_before_messages(room.id, end_id)
        content = {
            'ack_id': self.message_counter,
            'type': 'history_messages',
            'messages': messages
        }
        self.message_counter += 1
        await self.send_message_with_retry(content)
    
    async def handle_message_detail(self, room, data):
        query_message_id = data["query_message_id"]
        room_type = data["room_type"]
        if room_type == 'group':
            result = await self.get_read_users_and_message_info(room.id, query_message_id)
        else:
            result = await self.get_is_read_and_message_info(room.id, query_message_id)
        result['type'] = 'message_detail'
        result['ack_id'] = self.message_counter
        self.message_counter += 1
        await self.send_message_with_retry(result)
    async def handle_get_reply_message(self, room, data):
        reply_message_id = data["reply_message_id"]
        end_id = data["end_id"]
        reply_message = await self.get_reply_context_messages(reply_message_id,end_id,room.id)
        reply_message['ack_id'] = self.message_counter
        self.message_counter += 1
        await self.send_message_with_retry(reply_message)

    async def handle_receiver_ack(self, ack_id):
        
        if ack_id in self.message_send_status:
            
            self.message_send_status[ack_id]['ack_received'] = True

    async def chat_message(self, event):
        # 将消息发送给WebSocket客户端
        event['type'] = 'chat_message'
        event['ack_id'] = self.message_counter
        self.message_counter += 1
        await self.send_message_with_retry(event)
       

    async def get_replied_number(self, room_id,msg_id):
    
        reply_count = await self.get_replied_number_count(room_id, msg_id)
        
        # 将回复数量发送回客户端
        await self.send(text_data=json.dumps({
            'type': 'reply_count',
            'reply_count': reply_count,
        }))

    async def send_message_with_retry(self, message_payload):
        ack_id = message_payload['ack_id']
        self.message_send_status[ack_id] = {
            'ack_received': False,
            'retries': 0
        }
        # 发送JSON字符串数据到WebSocket客户端
        await self.send(text_data=json.dumps(message_payload,ensure_ascii=False))
        # 设置一个计时器等待ACK
        asyncio.create_task(self.start_retry_timer(message_payload))
        #await self.start_retry_timer(message_payload)


    # 设置一个计时器来等待ACK，如果未收到ACK则重发消息
    async def start_retry_timer(self, message_payload):
        ack_id = message_payload['ack_id']
        await asyncio.sleep(RETRY_INTERVAL)
        if not self.message_send_status[ack_id]['ack_received']:
            if self.message_send_status[ack_id]['retries'] < MAX_RETRIES:
                # 重发消息
                self.message_send_status[ack_id]['retries'] += 1
                await self.send(text_data=json.dumps(message_payload,ensure_ascii=False))
                # 重新启动计时器
                await self.start_retry_timer(message_payload)
            else:
                # 达到最大重试次数，放弃重发
                await self.send(text_data=json.dumps({'type':'retry_failed',"message":"Failed to send message"}))
                del self.message_send_status[ack_id]
        else :
            await self.send(text_data = json.dumps({'type':'retry_success',"message":"ack received"}))
            print('ack received')


   
    
    @database_sync_to_async
    def get_reply_context_messages(self, reply_id, end_id,room_id):
        conversation_member = ConversationMember.objects.filter(
        conversation_id=room_id,
        member_user_id=self.user.id
    ).first()

        if conversation_member and reply_id in conversation_member.deleted_messages.all().values_list('msg_id', flat=True):
            return {
                'type': 'reply_message_context',
                'error': 'true'
            }
        
        start_id = max(reply_id - 6, 1)
    
        # 查询条件现在需要确保msg_id在start_id和end_id之间
        messages = MessageStatus.objects.filter(
            conversation_id=room_id,
            msg_id__gte=start_id,  
            msg_id__lt=end_id     
        ).order_by('-msg_id')  
        
        messages_info = []
        for message in messages:
            message_data = {
                'msg_id': message.msg_id,
                'message_content': message.content,
                'sender_id': message.sender.id,
                'sender_name': message.sender.name,
                'sender_avatar': message.sender.avatar,
                'send_time': timezone.localtime(message.create_time).strftime('%Y-%m-%d %H:%M:%S'),
                'reply_id': message.reply_id if message.reply_id is not None else -1
            }
            
            # 对于每条消息，如果reply_id存在，查询被回复的消息详情
            if message.reply_id :
                replied_message = MessageStatus.objects.filter(msg_id=message.reply_id, conversation_id=room_id).first()
                if replied_message:
                    message_data['replied_message'] = {
                        'sender_name': replied_message.sender.name,
                        'content': replied_message.content
                    }

            messages_info.append(message_data)

        response = {
            'messages': messages_info,
            'type': 'reply_message_context',
            'error':'false'
        }
        return response
    
    @database_sync_to_async
    def save_message_content(self, content, room_id, sender_id,reply_id):
        # 创建并保存消息内容，返回消息载荷
        last_message = MessageStatus.objects.filter(conversation_id=room_id).order_by('-msg_id').first()
        next_sequence_number = 1 if last_message is None else last_message.msg_id + 1
        sender = User.objects.get(id=sender_id)
        new_message = MessageStatus.objects.create(
            content=content,
            msg_id=next_sequence_number,
            conversation_id=room_id,
            sender=sender,
        )

        if reply_id != -1:
            new_message.reply_id = reply_id
            new_message.save()
        # 更新已读索引
        memberstatus = ConversationMember.objects.get(conversation_id=room_id, member_user_id=sender_id)
        memberstatus.read_front_index = next_sequence_number
        memberstatus.save()
        # 创建消息有效载荷
        message_data = {
            'type': 'chat_message',
            'message_id': new_message.msg_id,
            'room_id': room_id,
            'message_content': content,
            'sender_id': sender_id,
            'sender_name': sender.name,
            'sender_avatar': sender.avatar,
            'reply_id': reply_id,
            'send_time': timezone.localtime(new_message.create_time).strftime('%Y-%m-%d %H:%M:%S')
        }
        if reply_id != -1:
            try:
                replied_message = MessageStatus.objects.get(conversation_id=room_id, msg_id=reply_id)
                message_data['replied_message'] = {
                    'content': replied_message.content,
                    'sender_name': replied_message.sender.name
                }
            except MessageStatus.DoesNotExist:
                # 如果没有找到回复的消息，返回一个错误消息
                return {
                    'type': 'error',
                    'error_message': 'The message you are replying to does not exist.',
                    'room_id': room_id,
                    'sender_id': sender_id
                }
        return message_data
    
    @database_sync_to_async
    def set_read_index(self, room_id, read_index):
        
        member = ConversationMember.objects.get(conversation_id=room_id, member_user_id=self.user.id)
        
        if read_index > member.read_front_index:
            member.read_front_index = read_index
            member.save()
        

        
    @database_sync_to_async
    def get_user_by_token(self, token):
        try:
            username = check_jwt_token(token)
            
            if username is None:
                return None
            username = username['username']
            with transaction.atomic():
                return User.objects.get(name=username)
        except User.DoesNotExist:
            return None
        except Exception as e:
            pass
        
    @sync_to_async
    def is_member_of_room(self, room_id, user_id):
        # 检查用户是否属于聊天室
        return ChatRoom.objects.filter(id=room_id, members__id=user_id).exists()
    

    @database_sync_to_async
    def get_is_read_and_message_info(self, room_id, query_message_id):
        try:

            room = ChatRoom.objects.get(id=room_id)

            other_member_id = room.members.exclude(id=self.user.id).values_list('id', flat=True).first()

            conversation_member = ConversationMember.objects.get(
                conversation_id=room_id,
                member_user_id=other_member_id
            )

            message = MessageStatus.objects.get(msg_id=query_message_id,conversation_id=room_id)
            is_read = conversation_member.read_front_index >= query_message_id
            reply_count = MessageStatus.objects.filter(conversation_id=room_id, reply_id=query_message_id).count()
            return {
                "count":reply_count,
                "is_read": is_read,
                "send_time": timezone.localtime(message.create_time).strftime('%Y-%m-%d %H:%M:%S')
            }
        except (ChatRoom.DoesNotExist, ConversationMember.DoesNotExist, MessageStatus.DoesNotExist) as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}
    @database_sync_to_async
    def get_read_users_and_message_info(self, room_id, query_message_id):
        message_info = MessageStatus.objects.filter(msg_id=query_message_id, conversation_id=room_id).first()

        read_members = ConversationMember.objects.filter(
            conversation_id=room_id,
            read_front_index__gte=query_message_id
        )
        
        read_users_info = [
            {
                'name': User.objects.get(id=member.member_user_id).name,
                'avatar': User.objects.get(id=member.member_user_id).avatar
            } for member in read_members
        ]

        reply_count = MessageStatus.objects.filter(conversation_id=room_id, reply_id=query_message_id).count()
        return {
            'count': reply_count,
            'users_info': read_users_info,
            'send_time': timezone.localtime(message_info.create_time).strftime('%Y-%m-%d %H:%M:%S') if message_info else None
        }
    @database_sync_to_async
    def get_room_avatar(self, room, user):
        avatar = room.avatar
        if room.type == ChatRoom.PRIVATE:
            other_member = room.members.exclude(id=user.id).first()
            if other_member and other_member.avatar:
                avatar = other_member.avatar  
        return avatar
    
    @database_sync_to_async
    def get_room_name(self, room, user):
        name = room.name
        if room.type == ChatRoom.PRIVATE:
            other_member = room.members.exclude(id=user.id).first()
            name = other_member.name
        return name
    
    @database_sync_to_async
    def get_certain_before_messages(self, room_id,end_msg_id):
        messages = MessageStatus.objects.filter(conversation_id=room_id, msg_id__lt=end_msg_id).select_related('sender').order_by('-msg_id')[:12]
        
        messages_with_sender_and_reply_info = []

        for message in messages:
            message_info = {
                'message_id': message.msg_id,
                'content': message.content,
                'sender_id': message.sender.id,
                'sender_name': message.sender.name,  
                'sender_avatar': message.sender.avatar,
                'send_time': timezone.localtime(message.create_time).strftime('%Y-%m-%d %H:%M:%S'),
                'reply_id': message.reply_id if message.reply_id is not None else -1
            }

            if message.reply_id is not None:
                try:
                    replied_message = MessageStatus.objects.get(conversation_id=room_id, msg_id=message.reply_id)
                    message_info['replied_message'] = {
                        'content': replied_message.content,
                        'sender_name': replied_message.sender.name
                    }
                except MessageStatus.DoesNotExist:
                    message_info['replied_message'] = {
                        'content': 'Replied message not found',
                        'sender_name': 'Unknown'
                    }
            
            messages_with_sender_and_reply_info.append(message_info)
    
        return  messages_with_sender_and_reply_info
    
    @database_sync_to_async
    def get_all_unread_messages(self):
        chatrooms = ChatRoom.objects.filter(members=self.user)
        unread_messages_summary = []

        for room in chatrooms:

            member_record = ConversationMember.objects.filter(
                conversation_id=room.id,
                member_user_id=self.user.id
            ).first()
            
            if not member_record:
                continue
            
            read_index = member_record.read_front_index
            
            deleted_msgs_ids = member_record.deleted_messages.values_list('msg_id', flat=True)

            unread_messages = MessageStatus.objects.filter(
                conversation_id=room.id,
                msg_id__gt=read_index
            ).exclude(
                msg_id__in=deleted_msgs_ids
            ).order_by('-create_time')

            # Get the count of unread messages
            unread_count = unread_messages.count()

            # Ensure latest messages also exclude deleted messages
            message_details = MessageStatus.objects.filter(
                conversation_id=room.id
            ).exclude(
                msg_id__in=deleted_msgs_ids
            ).order_by('-create_time')[:8]

           
            details_list = []
            for detail in message_details:
                reply_id = detail.reply_id
                message_info = {
                    'message_id': detail.msg_id,
                    'message_content': detail.content,
                    'room_id': room.id,
                    'sender_id': detail.sender.id,
                    'sender_name': detail.sender.name,
                    'sender_avatar': detail.sender.avatar,
                    'send_time': timezone.localtime(detail.create_time).strftime('%Y-%m-%d %H:%M:%S'),
                    'reply_id': reply_id if reply_id is not None else -1
                }

                # Check and append replied message details if reply_id is not None
                if detail.reply_id is not None:
                    try:
                        replied_message = MessageStatus.objects.get(conversation_id=room.id, msg_id=detail.reply_id)
                        message_info['replied_message'] = {
                            'content': replied_message.content,
                            'sender_name': replied_message.sender.name
                        }
                    except MessageStatus.DoesNotExist:
                        message_info['replied_message'] = {
                            'content': 'Replied message not found',
                            'sender_name': 'Unknown'
                        }

                details_list.append(message_info)

            unread_messages_summary.append({
            'room_id': room.id,
            'unread_count': unread_count,
            'values': details_list
        })

        return unread_messages_summary
    
    async def send_unread_messages(self):
        unread_messages = await self.get_all_unread_messages()
        message = {}
        message['type'] = 'unread_messages'
        message['ack_id'] = self.message_counter
        message['unread_messages'] = unread_messages
        self.message_counter += 1
        await self.send_message_with_retry(message)


    

    async def get_user_rooms(self):
        # 将查询包装在sync_to_async中以允许异步调用
        @sync_to_async
        def get_rooms():
            member_rooms = ChatRoom.objects.filter(members=self.user)
            return list(member_rooms)
        return await get_rooms()
    
    @sync_to_async
    def get_room_by_name(self, room_id):
        # 尝试根据room_name获取ChatRoom实例，并检查self.user是否为聊天室成员
        try:
            # 这里使用filter().first()而不是get()，
            # 因为get()在找不到对象或找到多个对象时会抛出异常，
            # 而filter().first()会在没有匹配的记录时返回None
            room = ChatRoom.objects.filter(id=room_id, members=self.user).first()
            return room
        except ChatRoom.DoesNotExist:
            return None
