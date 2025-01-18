from utils.utils_jwt import  check_jwt_token
from django.http import HttpRequest
from utils.utils_request import BAD_METHOD,request_failed, request_success
from django.views.decorators.http import require_http_methods
from communication.models import MessageStatus,ConversationMember
from author.models import User
from django.utils import timezone



@require_http_methods(["GET"])
def filter_messages_by_date_in_room(req: HttpRequest):
    
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    room_id = req.GET.get('room_id')
    date_str = req.GET.get('date')

    if not room_id or not date_str:
        return request_failed(4, 'Room ID and date are required', 400)
    
    try :
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(5, 'User does not exist', 404)
    
    try:
        date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
        start_of_day = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.max.time()))
        if date is None:
            raise ValueError
    except ValueError as e:
        return request_failed(6,'Invalid date format' , 400)
    
    deleted_message_ids = ConversationMember.objects.get(
        member_user_id=user.id, conversation_id=room_id
    ).deleted_messages.values_list('id', flat=True)
    messages = MessageStatus.objects.filter(
        conversation_id=room_id,
    )
    
    messages = MessageStatus.objects.filter(
        conversation_id=room_id, 
        create_time__gte=start_of_day,
        create_time__lte=end_of_day
    ).exclude(id__in=deleted_message_ids)
   
    messages_data = [{
    'msg_id': msg.msg_id,
    'sender__avatar': msg.sender.avatar,  
    'sender__name': msg.sender.name, 
    'content': msg.content,
    'create_time': timezone.localtime(msg.create_time).strftime('%Y-%m-%d %H:%M:%S')  # 格式化日期时间
} for msg in messages]
    
    return request_success({"messages": messages_data})


@require_http_methods(["GET"])
def filter_messages_by_sender_in_room(req: HttpRequest):
    
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    if username is None:
        return request_failed(2, 'Invalid token', 401)
    
    room_id = req.GET.get('room_id')
    member_user_id = req.GET.get('member_user_id')
    if not room_id or not member_user_id:
        return request_failed(3, 'Room ID and member user ID are required', 400)
    
    try :
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4, 'User does not exist', 404)
    

    deleted_message_ids = ConversationMember.objects.get(
        member_user_id=user.id, conversation_id=room_id
    ).deleted_messages.values_list('id', flat=True)
    
    messages = MessageStatus.objects.filter(
        conversation_id=room_id, 
        sender__id=member_user_id
    ).exclude(id__in=deleted_message_ids)

    messages_data = [{
    'msg_id': msg.msg_id,
    'sender__avatar': msg.sender.avatar,  
    'sender__name': msg.sender.name, 
    'content': msg.content,
    'create_time': timezone.localtime(msg.create_time).strftime('%Y-%m-%d %H:%M:%S')  # 格式化日期时间
} for msg in messages]
    
    # 直接返回消息数据，如果没有找到消息，messages_data将是一个空列表
    return request_success({"messages": messages_data})

@require_http_methods(["GET"])
def filter_messages_by_room(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    if username is None:
        return request_failed(2, 'Invalid token', 401)
    
    room_id = req.GET.get('room_id')
    if not room_id:
        return request_failed(3, 'Room ID is required', 400)
    
    try :
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4, 'User does not exist', 404)
    
    deleted_message_ids = ConversationMember.objects.get(
        member_user_id=user.id, conversation_id=room_id
    ).deleted_messages.values_list('id', flat=True)
    
    messages = MessageStatus.objects.filter(
        conversation_id=room_id
    ).exclude(id__in=deleted_message_ids)

    messages_data = [{
    'msg_id': msg.msg_id,
    'sender__avatar': msg.sender.avatar,  
    'sender__name': msg.sender.name, 
    'content': msg.content,
    'create_time': timezone.localtime(msg.create_time).strftime('%Y-%m-%d %H:%M:%S')  # 格式化日期时间
} for msg in messages]
    
    return request_success({"messages": messages_data})

@require_http_methods(['DELETE'])
def delete_message(req: HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)

    username = check_jwt_token(token)
    if username is None:
        return request_failed(2, 'Invalid token', 401)

    message_id = req.GET.get('message_id')
    room_id = req.GET.get('room_id')
    if not message_id or not room_id:
        return request_failed(3, 'Message ID and Room ID are required', 400)

    try:
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4, 'User does not exist', 404)

    try:
        message = MessageStatus.objects.get(msg_id=message_id, conversation_id=room_id)
    except MessageStatus.DoesNotExist:
        return request_failed(5, 'Message does not exist', 404)

    try:
        member = ConversationMember.objects.get(member_user_id=user.id, conversation_id=room_id)
    except ConversationMember.DoesNotExist:
        return request_failed(6, 'User is not in the conversation', 403)

    if message in member.deleted_messages.all():
        return request_failed(7, 'Message already marked as deleted', 409)

    member.deleted_messages.add(message)
    return request_success()