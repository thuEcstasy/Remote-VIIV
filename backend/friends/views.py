import json
from django.http import JsonResponse
from django.http import HttpRequest
from author.models import  User
from friends.models import FriendRequest, Group, UserGroup
from utils.utils_request import BAD_METHOD,request_failed, request_success
from utils.utils_require import MAX_CHAR_LENGTH
from utils.utils_jwt import  check_jwt_token
from django.views.decorators.http import require_http_methods
from django.db import transaction,IntegrityError  #保证函数体中的要么都成功创建，要么在遇到任何错误时都不会创建，这样可以保持数据库的一致性。
from communication.models import ConversationMember,MessageStatus
from group.models import ChatRoom


@require_http_methods(["GET"])
def search_users(req:HttpRequest):
    
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    query = req.GET.get('query', '')
    
    user_groups = Group.objects.filter(owner__name=username['username']).values_list('group_id', flat=True)
    users = User.objects.filter(name__contains=query).values('id', 'name','avatar')
    # 获取已发送但未处理的好友请求
    friend_requests_sent = FriendRequest.objects.filter(from_user__name=username['username'], status='pending').values_list('to_user_id', flat=True)
    
    
    # 检查用户是否在好友分组中或已发送但未处理的好友请求中
    for user in users:
        user['status'] = 0
        if user['id'] in friend_requests_sent:
            user['status'] = 2
        else:
            for group_id in user_groups:
                if UserGroup.objects.filter(group_id=group_id, user_id=user['id']).exists():
                    user['status'] = 1
                    break
    return JsonResponse(list(users), safe=False)


@require_http_methods(["GET"])
def get_all_friends(req):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(4,'Authorization token is missing', 401)
    
    username = check_jwt_token(token)  # 确保这个函数返回用户名或者User实例
    if username is None:
        return request_failed(4,'Invalid token', 401)
    
    
    try:
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4,'User not found', 404)
    
    groups = Group.objects.filter(owner=user)

    # 初始化成员信息列表
    all_members = []

    for group in groups:
        # 对于每个群组，获取组内所有成员的User实例
        user_groups = group.group_members.all()
        
        # 遍历每个UserGroup实例来获取成员信息
        for user_group in user_groups:
            member = {
                'id': user_group.user.id,
                'username': user_group.user.name,
                'avatar': user_group.user.avatar 
            }
            if member not in all_members:  # 防止重复添加相同的成员信息
                all_members.append(member)

    # 返回所有群组成员的信息
    return JsonResponse({'code': 0, 'members': list(all_members)}, safe=False, status=200)


@require_http_methods(["GET"])
def get_all_friends_in_group(req):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(4,'Authorization token is missing', 401)
    
    username = check_jwt_token(token)  # 确保这个函数返回用户名或者User实例
    if username is None:
        return request_failed(4,'Invalid token', 401)
    
    group_name = req.GET.get('group')  # 获取URL参数中的group名字
    if not group_name:
        return request_failed(3,'Group name is required', 400)
    
    try:
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4,'User not found', 404)
    
    try:
        group = Group.objects.get(name=group_name, owner=user)
    except Group.DoesNotExist:
        return request_failed(4,'Group not found or you are not the owner', 404)
    
    # 获取组内所有成员的信息
    user_groups = group.group_members.all()

    # 初始化成员信息列表
    members_info = []

    # 遍历每个UserGroup实例来获取成员信息
    for user_group in user_groups:
        user = user_group.user
        member = {
            'id': user.id,
            'name': user.name,  # 假设User模型有一个username字段作为用户的名字
            'avatar': user.avatar # 确保User模型有一个avatar字段
        }
        members_info.append(member)

    
    return JsonResponse({'code':0,'members': members_info}, safe=False, status=200)

    

@require_http_methods(["POST"])
def send_friend_request(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)
   
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    data = json.loads(req.body.decode('utf-8'))
    to_user_id = data.get('to_user_id') ##注意这里搜索的是id
    
    from_user = User.objects.get(name=username['username'])
    try:
        to_user = User.objects.get(id=to_user_id)
        if from_user == to_user:
            return request_failed(4,'You cannot send a friend request to yourself.', 400)

        friend_request, created = FriendRequest.objects.get_or_create(
            from_user=from_user,
            to_user=to_user,
            defaults={'status': 'pending'}
        )
        if not created and friend_request.status == 'pending':
            return request_failed(4, 'Friend request already sent', 400)
        elif friend_request.status == 'accepted':
            return request_failed(6, 'The user is already your friend', 400)
        elif not created and friend_request.status == 'rejected':
            friend_request.status = 'pending'
            friend_request.save()
        
        return request_success({'msg':'Friend request sent successfully.',
                                })
    except User.DoesNotExist:
        return  request_failed(5, 'User not found', 404)

@require_http_methods(["GET"])
def get_friend_requests(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    try:
        to_user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    
    # 获取所有状态为'pending'的好友请求
    friend_requests = FriendRequest.objects.filter(to_user=to_user, status='pending').order_by('-timestamp')

    # 准备响应数据
    requests_data = [{
        'id': fr.id,
        'timestamp': fr.timestamp,
        'from_user_id': fr.from_user.id,
        'from_user_name': fr.from_user.name,
        #'from_user_avatar': fr.from_user.avatar
    } for fr in friend_requests]

    return request_success({'requests': requests_data})


@require_http_methods(["DELETE"])
def delete_friend(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    try:
        from_user = User.objects.get(name=username["username"])
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    data = json.loads(req.body.decode('utf-8'))
    to_user_username = data.get('to_user')
    if not to_user_username:
        return request_failed(5, 'to_user parameter is missing', 400)
    if to_user_username == from_user.name:
        return request_failed(6, 'You cannot delete yourself', 400)
    try:
        to_user = User.objects.get(name=to_user_username)
    except User.DoesNotExist:
        return request_failed(6, 'to_user not found', 404)

    UserGroup.objects.filter(user=to_user, group__owner=from_user).delete()
    UserGroup.objects.filter(user=from_user, group__owner=to_user).delete()
    FriendRequest.objects.filter(from_user=from_user, to_user=to_user).delete()
    FriendRequest.objects.filter(from_user=to_user, to_user=from_user).delete()
    chatrooms = ChatRoom.objects.filter(members__in=[from_user, to_user]).distinct()
    for chatroom in chatrooms:
        if chatroom.type == ChatRoom.PRIVATE:  # 确保只有这两个成员
            # 删除关联的 ConversationMember 实例
            ConversationMember.objects.filter(conversation_id=chatroom.id).delete()
            
            # 查找关联的 MessageStatus 实例
            message_statuses = MessageStatus.objects.filter(conversation_id=chatroom.id)
                
            # 删除 MessageStatus 实例
            message_statuses.delete()
            
            # 最后删除 ChatRoom 实例
            chatroom.delete()

    return request_success({'message': 'Friendship updated successfully'})

@require_http_methods(["POST"])
def handle_friend_request(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)
   
    if username is None:
        return request_failed(3, 'Invalid token', 401)  
    
    data = json.loads(req.body.decode('utf-8'))
    request_id = data.get('request_id')
    action = data.get('action')  # 'accept' or 'reject'
    to_user = User.objects.get(name=username['username'])
    
    try:
        friend_request = FriendRequest.objects.get(id=request_id, to_user=to_user)
        if action == 'accept':
            friend_request.status = 'accepted'
            friend_request.save()
            from_user = friend_request.from_user
            sorted_ids = sorted([from_user.id, to_user.id])
            room_name = "-".join([str(id) for id in sorted_ids])
            if ChatRoom.objects.filter(name=room_name).exists():
                return request_failed(6, 'You are already friends', 400)
            try:
                with transaction.atomic():
                
                    from_user_group, _ = Group.objects.get_or_create(
                        name='My friends',
                        owner=from_user  # 假设owner字段存储的是用户名
                    )

                
                    to_user_group, _ = Group.objects.get_or_create(
                        name='My friends',
                        owner=to_user
                    )

                    # 为from_user的'My friends'群组中添加to_user为成员
                    UserGroup.objects.get_or_create(
                        user=to_user,
                        group=from_user_group,
                    )

                    # 为to_user的'My friends'群组中添加from_user为成员
                    UserGroup.objects.get_or_create(
                        user=from_user,
                        group=to_user_group,
                    )

                    chat_room = ChatRoom.objects.create(name=room_name,type = ChatRoom.PRIVATE)
                    chat_room.members.set([from_user, to_user])

                    ConversationMember.objects.create(
                            conversation_id=chat_room.id,
                            member_user_id=to_user.id,
                    )

                    ConversationMember.objects.create(
                        conversation_id=chat_room.id,
                        member_user_id=from_user.id,
                    )
            except IntegrityError as e:
                # 处理可能的数据库完整性问题
                transaction.set_rollback(True)
                return request_failed(3, f'Database error: {e}', 500)
            except Exception as e:
                # 捕获其他所有未预料到的异常
                transaction.set_rollback(True)
                return request_failed(4, f'Unexpected error: {str(e)}', 500)
                
            return request_success({'message': 'Friend request accepted.'})
        elif action == 'reject':
            friend_request.status = 'rejected'
            friend_request.save()
            return request_success({'message': 'Friend request rejected.'})
        else:
            return request_failed(4,'Invalid action.', 400)
            
    except FriendRequest.DoesNotExist:
        return request_failed(5, 'Friend request not found.', 404)
    

#创建分组
@require_http_methods(["POST"])
def create_group(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)
    if username is None:
        return request_failed(3, 'Invalid token', 401)  
    try:
        data = json.loads(req.body.decode('utf-8'))  # 解析请求体中的JSON数据
        group_name = data.get('group_name')  # 尝试获取"group_name"字段
        
        if not group_name:  # 如果"group_name"字段为空或不存在
            return request_failed(4, 'Group name is required', 400)
    except json.JSONDecodeError:
        return request_failed(5, 'Invalid JSON data', 400)

    owner = username['username']  # 假设owner字段保存用户名

    if Group.objects.filter(owner__name=owner, name=group_name).exists():
        return request_failed(6, 'A group with the same name already exists', 400)
    # 创建群组
    owner = User.objects.get(name=owner)
    group = Group.objects.create(name=group_name, owner=owner)
    return request_success({"message": "Group created successfully", "group_id": group.group_id})

#添加用户
@require_http_methods(["POST"])
def add_user_to_group(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)
   
    if username is None:
        return request_failed(3, 'Invalid token', 401)  
    data = json.loads(req.body.decode('utf-8'))  # 解析请求体中的JSON数据
    member_user_id= data.get('user_id','') 
    group_name = data.get('group_name','')
    if not member_user_id:  # 如果"group_name"字段为空或不存在
        return request_failed(4, 'user id is required', 400)
    if not group_name:  # 如果"group_name"字段为空或不存在
        return request_failed(4, 'group id is required', 400)
    user = User.objects.get(name = username['username'])
    try:
        member_user = User.objects.get(id=member_user_id)
        target_group = Group.objects.get(name=group_name, owner=user)  # 确保只有组所有者可以操作

        # 检查用户是否已在某个分组中

        existing_memberships = UserGroup.objects.filter(user=member_user, group__owner__name=username['username'])
        if not existing_memberships.exists():
            # 如果用户不在任何分组中，则请求失败
            return request_failed(4,"User must be in a group before being moved", 400)

        # 从先前的分组中移除用户
        existing_memberships.delete()

        # 将用户添加到新的分组
        UserGroup.objects.create(group=target_group, user=member_user)
        return request_success({"message": "User successfully moved to the new group"})

    except User.DoesNotExist:
        return request_failed(4,"User not found",404)
    except Group.DoesNotExist:
        return request_failed(5, "Group not found or you are not the owner",404)
    
@require_http_methods(['GET'])
def get_all_groups(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    try:
        username = check_jwt_token(token)
        if username is None:
            return request_failed(2, 'Invalid token', 401)
    except Exception as e:
        # 处理可能的异常，例如令牌格式错误
        return request_failed(3, str(e), 401)
    user = User.objects.get(name=username['username'])
    # 查询所有owner为username的group
    groups = Group.objects.filter(owner=user).values('group_id', 'name')

    # 将查询结果转换为列表格式，以便可以序列化为JSON
    groups_list = list(groups)

    # 检查是否存在名为"My friends"的组，并将其移动到列表的第一个位置
    my_friends_group = next((group for group in groups_list if group['name'] == "My friends"), None)
    if my_friends_group:
        groups_list.remove(my_friends_group)
        groups_list.insert(0, my_friends_group)
    else:
        return request_failed(4,'something abnormal happened', 404)

    # 返回查询结果
    return request_success({'groups': groups_list})
@require_http_methods(['GET'])
def get_all_users_in_group(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    print(1)
    try:
        username = check_jwt_token(token)
        if username is None:
            return request_failed(2, 'Invalid token', 401)
    except Exception as e:
        # 处理可能的异常，例如令牌格式错误
        return request_failed(2, str(e), 401)
    group_name = req.GET.get('group_name', '')
    user = User.objects.get(name=username['username'])
    # 查询所有owner为username的group
    if not group_name:
        return request_failed(3,'Group name is required', 400)
    
    try:
        group = Group.objects.get(owner=user, name=group_name)
        # 获取群组中所有成员的信息
        members = group.group_members.all().select_related('user')
        # 将查询结果转换为列表格式，以便可以序列化为JSON
        members_list = [{'id': member.user.id, 'name': member.user.name, 'avatar': member.user.avatar} for member in members]
    except Group.DoesNotExist:
        return request_failed(4,'Group not found', 404)
    except Exception as e:
        return request_failed(5,{e}, 500)
    
    # 返回查询结果
    return request_success({'members': members_list})

@require_http_methods(['GET'])
def get_user_position(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)

    if username is None:
        return request_failed(3, 'Invalid token', 401)  
    
    try:
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    
    member_user_id = req.GET.get('member_user_id', None)
    if not member_user_id:
            return request_failed(5,'User ID is required',400)
    
    try:
        # 获取该用户作为所有者的群组中包含指定用户的群组
        group_name = Group.objects.filter(owner=user, group_members__user__id=member_user_id).values_list('name', flat=True).first()
    except Exception as e:
        return request_failed(6,{e}, 500)
    
    if not group_name:
        return request_failed(7,'No groups found for the specified user under this owner', 404)
    
    return request_success({'group': group_name})

@require_http_methods(['PUT'])
def rename_group(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    # 检查JWT令牌是否有效
    try:
        username = check_jwt_token(token)
        if username is None:
            return request_failed(2, 'Invalid token', 401)
    except Exception as e:
        # 处理可能的异常，例如令牌格式错误
        return request_failed(3, str(e), 401)
    
    try:
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    
    try:
        data = json.loads(req.body.decode('utf-8'))
    except json.JSONDecodeError:
        return request_failed(5, 'Invalid JSON data', 400)
    
    old_name = data.get('old_name', '')
    new_name = data.get('new_name', '')

    # 检查old_name和new_name是否缺失
    if not old_name:
        return request_failed(6, 'Missing old_name', 400)
    if not new_name:
        return request_failed(7, 'Missing new_name', 400)
    
    # old_name不能为"My friends"
    if old_name == "My friends":
        return request_failed(8, 'Cannot rename "My friends" group', 400)
    if old_name == new_name:
        return request_failed(9, 'New name must be different from old name', 400)
    # new_name不能为owner已有的分组的name
    if Group.objects.filter(owner=user, name=new_name).exists():
        return request_failed(10, 'Group with new_name already exists', 400)
    
    # 更新组的名称
    try:
        group = Group.objects.get(owner=user, name=old_name)
        group.name = new_name
        group.save()
    except Group.DoesNotExist:
        return request_failed(11, 'Group with old_name not found', 404)
    
    # 返回成功响应
    return request_success({'message': 'Group renamed successfully'})

@require_http_methods(['DELETE'])
def remove_group(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    
    # 检查JWT令牌是否有效
    try:
        username = check_jwt_token(token)
        if username is None:
            return request_failed(3, 'Invalid token', 401)
    except Exception as e:
        # 处理可能的异常，例如令牌格式错误
        return request_failed(3, str(e), 401)
    
    try:
        user = User.objects.get(name=username['username'])
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    
    try:
        data = json.loads(req.body.decode('utf-8'))
    except json.JSONDecodeError:
        return request_failed(5, 'Invalid JSON data', 400)
    
    group_name = data.get('group_name', '')
    
    if not group_name:
        return request_failed(6, 'Group name is required', 400)
    
    # "My friends"组不能被删除
    if group_name == "My friends":
        return request_failed(7, 'Cannot delete "My friends" group', 400)
    
    # 删除组
    try:
        group = Group.objects.get(owner=user, name=group_name)
        
        # 获取"My friends"组
        my_friends_group = Group.objects.get(owner=user, name='My friends')
        
        # 将所有与该组相关的UserGroup对象的group字段设置为"My friends"组
        user_groups = UserGroup.objects.filter(group=group)
        for user_group in user_groups:
            user_group.group = my_friends_group
            user_group.save()
        
        # 删除组
        group.delete()
    except Group.DoesNotExist:
        return request_failed(8, 'Group not found', 404)
    
    # 返回成功响应
    return request_success({'message': 'Group deleted successfully'})





    



