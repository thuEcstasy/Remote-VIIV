import json
from django.http import HttpRequest, HttpResponse
from VIIV.constants import OFFLINE,ONLINE,TWILIO_SID,TWILIO_TOKEN
from author.models import  User,EmailVerification,PhoneVerification
from utils.utils_request import BAD_METHOD,request_failed, request_success
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password,check_password
import random
import string
from django.core.mail import send_mail
from dotenv import load_dotenv
from communication.models import ConversationMember,MessageStatus
from  group.models import ChatRoom
from django.db import transaction 
from friends.models import Group,UserGroup
import os
from twilio.rest import Client
from email_validator import validate_email, EmailNotValidError




@CheckRequire
def login(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
   
    body = json.loads(req.body.decode("utf-8"))
    
    username = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    user_input_password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    if User.objects.filter(name=username).exists():
        user = User.objects.get(name=username)
        
        if user.status == ONLINE:
           return request_failed(2, "Your account is already online", 401)
        if check_password(user_input_password, user.password):
            user.status = ONLINE
            user.save()
            user_info = {
            'id': user.id,
            'name': user.name,
            'avatar': user.avatar,
            'email': user.email,
            'phone_number': user.phone_number
        }
            return request_success({"token": generate_jwt_token(username),'data': user_info})
        else:
            return request_failed(3, "Wrong password or account", 401)
    else:
        return request_failed(4, "Wrong password or account", 401)
        


@CheckRequire
def register(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD  # 确保请求方法为POST
    

    body = json.loads(req.body.decode("utf-8"))
    # 解析用户名和密码
    username = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    plain_password = require(body, "password", "string", err_msg="Missing or error type of [password]")

    # 检查用户名中是否含有空格
    if " " in username:
        return request_failed(1, "Username should not contain spaces", 400)
    # 检查密码长度是否不少于8个字符，并且不包含空格
    if len(plain_password) < 8 or " " in plain_password:
        return request_failed(2, "Password must be at least 8 characters long and not contain spaces", 400)

    # 检查用户是否存在
    if User.objects.filter(name=username).exists():
        return request_failed(3, "User already exists", 401)
    else:
        try:
        # 在事务中创建用户和好友分组
            with transaction.atomic():
                # 创建新用户并保存
                user = User(name=username, registered_time=get_timestamp())
                hashed_password = make_password(plain_password)
                user.password = hashed_password
                user.save()

                # 创建用户的好友分组
                friend_group = Group(name='My friends', owner=user)
                friend_group.save()

                # 将用户添加到好友分组中
                user_group = UserGroup(user=user, group=friend_group)
                user_group.save()
            
        except Exception as e:
            # 捕获所有异常，并设置事务回滚
            transaction.set_rollback(True)
            return request_failed(4, f'Unexpected error: {str(e)}', 500)
       
    return request_success({"message":"user successfully created"})

@CheckRequire
def name_change(req: HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)

    # 从请求头中获取JWT
    data = json.loads(req.body.decode('utf-8'))
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    # 解析JWT以获取用户名
    username = check_jwt_token(token)
   
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    username = username['username']

    try:
        user = User.objects.get(name=username)
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)

    
    new_name = data.get('new_name') 
    if " " in new_name:
        return request_failed(5, "Username should not contain spaces", 400)
    
    if User.objects.filter(name=new_name).exists():
        return request_failed(6, "User already exists", 401)
    
    user.name = new_name
    user.save()
    return request_success({"token": generate_jwt_token(new_name),"msg": "Your userName successfully changes"})

@CheckRequire
def password_change(req: HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)

    # 从请求头中获取JWT
    data = json.loads(req.body.decode('utf-8'))
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(3, 'Authorization token is missing', 401)
    
    # 解析JWT以获取用户名
    username = check_jwt_token(token)
   
    if username is None:
        return request_failed(4, 'Invalid token', 401)
    username = username['username']

    user_input_password = data.get('old_password')
    try:
        user = User.objects.get(name=username)
    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
    
    # 验证密码
    
    new_password = data.get('new_password')

    if len(new_password) < 8 or " " in new_password:
        return request_failed(6, "Password must be at least 8 characters long and not contain spaces", 400)

    if not check_password(user_input_password, user.password):
        return request_failed(7, 'Old password is incorrect', 401)
    
    user.password = make_password(new_password)
    user.save()
    return request_success({"msg": "Your password successfully changes"})
    
    
@CheckRequire
def update_avatar(req: HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)

    # 从请求头中获取JWT
    data = json.loads(req.body.decode('utf-8'))
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    # 解析JWT以获取用户名
    username = check_jwt_token(token)
   
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    username = username['username']

    base64_avatar = data.get('avatar')
    if not base64_avatar:
        return request_failed(4, 'Avatar is missing', 400)

    try:
        user = User.objects.get(name=username)  # 假设用户模型使用的是name字段作为用户名
        user.avatar = base64_avatar
        user.save()
        return request_success({"msg": "Your avatar successfully changes"})
    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
    
@CheckRequire
def bind_phone_number(req:HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)
    body = json.loads(req.body.decode("utf-8"))
    # 从请求头中获取JWT
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)

    # 解析JWT以获取用户名
    username = check_jwt_token(token)

    if username is None:
        return request_failed(3, 'Invalid token', 401)
    phone_number = require(body, "number", "string", err_msg="Missing or error type of [number]")
    if not phone_number or len(phone_number) != 11:
        return request_failed(4, 'Phone number is invalid', 400)
    
    verification_code = ''.join(random.choices(string.ascii_letters, k=6))
    load_dotenv()
    account_sid = TWILIO_SID
    auth_token = TWILIO_TOKEN
    # 初始化Twilio客户端
    client = Client(account_sid, auth_token)

    # 发送短信
    message = client.messages.create(
        body=f'{verification_code}',  # 短信内容
        from_='+19254489327',  # 我的Twilio电话号码
        to=f'+86{phone_number}'  # 接收短信的电话号码
    )
    PhoneVerification.objects.update_or_create(
        number=phone_number,
        defaults={'verification_code': verification_code,'created_at':timezone.now()}
    )
    return request_success({'msg': 'Verification code sent successfully'})

@CheckRequire
def verify_phone_number(req: HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)

    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    body = json.loads(req.body.decode("utf-8"))
    number = require(body, "number", "string", err_msg="Missing or error type of [email]")
    user_code = require(body, "code", "string", err_msg="Missing or error type of [verification code]")
    
    if not number or not user_code: 
        return request_failed(4, ' and verification code are required', 400)
    
    try:
        # 假设我们设置验证码有效期为10分钟
        verification = PhoneVerification.objects.get(number=number, verification_code=user_code, created_at__gte=timezone.now() - timedelta(minutes=3))
    except PhoneVerification.DoesNotExist:
        return request_failed(5, 'Invalid verification code or expired', 400)
    
    username = username['username']
    try:
        user = User.objects.get(name=username)  # 假设用户模型使用的是name字段作为用户名
        user.phone_number = number
        user.save()
        return request_success({"msg": "Your phone number successfully changes"})
    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
### 发送邮箱验证码的逻辑
@CheckRequire
def bind_email(req: HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)
    
    # 从请求头中获取JWT
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)

    # 解析JWT以获取用户
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    body = json.loads(req.body.decode("utf-8"))
    email = require(body, "email", "string", err_msg="Missing or error type of [email]")
    if not email:
        return request_failed(4, 'Email is missing', 400)
    if not User.objects.filter(name=username['username']).exists():
        return request_failed(5, 'User not found', 404)
    if email == User.objects.get(name=username['username']).email:
        return request_failed(6, 'This email is already yours', 400)
    if User.objects.filter(email=email).exists():
        return request_failed(7, 'This email is already bound', 400)
    
    try:
        v = validate_email(email)
        email = v["email"]
    except EmailNotValidError as e:
        return request_failed(8, 'Email is invalid', 400)
    verification_code = str(random.randint(100000, 999999))
    send_mail(
        'Your Email Verification Code',
        f'Your verification code is: {verification_code}.',
        'infinitqgl@gmail.com',  # 发件人
        [email],  # 收件人列表
        fail_silently=False,
    )
    EmailVerification.objects.update_or_create(
        email=email,
        defaults={'verification_code': verification_code, 'created_at': timezone.now()}
    )
    return request_success({'msg': 'Verification code sent successfully'})
### 验证验证码
@CheckRequire
def verify_email(req: HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)

    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    

    body = json.loads(req.body.decode("utf-8"))
    email = body.get('email')
    user_code = body.get('code')

    if not email or not user_code: 
        return request_failed(4, 'Email and verification code are required', 400)
    
    try:
        verification = EmailVerification.objects.get(email=email, verification_code=user_code, created_at__gte=timezone.now() - timedelta(minutes=3))
    except EmailVerification.DoesNotExist:
        return request_failed(5, 'Invalid verification code or expired', 400)
    
    username = username['username']
    try:
        user = User.objects.get(name=username)  # 假设用户模型使用的是name字段作为用户名
        user.email = email
        user.save()
        return request_success({"msg": "Your email successfully changes"})
    except User.DoesNotExist:
        return request_failed(7, 'User not found', 404)



    
@CheckRequire  
def delete(req: HttpRequest):
    if req.method != "DELETE":
        return request_failed(1, 'Bad request method', 400)
    
    # Extract the JWT from the request headers
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    # Decode the JWT to get the username
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    # Parse the password from the request body
    try:
        body = json.loads(req.body.decode("utf-8"))
        user_input_password = body.get('password')
    except json.JSONDecodeError:
        return request_failed(4, 'Invalid request body', 400)

    if not user_input_password:
        return request_failed(5, 'Password is required', 400)
    
    # Retrieve the user from the database
    try:
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(6, 'User not found', 404)
    
    # Check if the provided password matches the one stored in the database
    if not check_password(user_input_password, user.password):
        return request_failed(7, 'Password is incorrect', 401)
    
    try:
        with transaction.atomic():
            # Before deleting the user, delete all associated ConversationMember entries
            ConversationMember.objects.filter(member_user_id=user.id).delete()
            chatrooms_as_member = ChatRoom.objects.filter(members__id=user.id)
            chatrooms_as_admin = ChatRoom.objects.filter(admins__id=user.id)
            chatrooms_as_owner = ChatRoom.objects.filter(owner=user)

            for chatroom in chatrooms_as_member:
                if chatroom.type == ChatRoom.PRIVATE:
                    ConversationMember.objects.filter(conversation_id=chatroom.id).delete()
                    MessageStatus.objects.filter(conversation_id=chatroom.id).delete()
                    chatroom.delete()
                else:  
                    chatroom.members.remove(user)
            for chatroom in chatrooms_as_admin:
                chatroom.admins.remove(user)
            for chatroom in chatrooms_as_owner:
                ConversationMember.objects.filter(conversation_id=chatroom.id).delete()
                MessageStatus.objects.filter(conversation_id=chatroom.id).delete()
                chatroom.delete() 

            # If password verification passes, delete the user
            user.delete()
    except Exception as e:
        transaction.set_rollback(True)
        return request_failed(8, f'Unexpected error: {str(e)}', 500)

    return request_success({"msg": "User successfully deleted"})


@CheckRequire
def get_user_info(req:HttpRequest):
    if req.method != "GET":
        return request_failed(1, 'Bad request method', 400)
    
    # 从请求头中获取JWT
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    # 解析JWT以获取用户名
    username = check_jwt_token(token) 
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    # 查找数据库中的用户
    try:
        user = User.objects.get(name=username['username'])
        user_info = {
            'id': user.id,
            'name': user.name,
            'avatar': user.avatar,
            'email': user.email,
            'phone_number': user.phone_number
        }
        return request_success({'data': user_info})
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    
@CheckRequire
def logout(req:HttpRequest):
    if req.method != 'POST':
        return request_failed(1, 'Invalid request', 400)

    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    username = username['username']
    try:
        user = User.objects.get(name=username)  # 假设用户模型使用的是name字段作为用户名
        user.status = OFFLINE
        user.save()
        return request_success({"msg": "Logout successfully"})
    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
