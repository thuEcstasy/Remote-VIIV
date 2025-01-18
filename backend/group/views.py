import json
from django.http import HttpRequest
from author.models import  User
from utils.utils_request import BAD_METHOD,request_failed, request_success
from utils.utils_require import MAX_CHAR_LENGTH
from utils.utils_jwt import  check_jwt_token
from django.views.decorators.http import require_http_methods
from django.db import transaction
from communication.models import ConversationMember, MessageStatus
from friends.models import Group,UserGroup
from group.models import ChatRoomNotice,Invitation,ChatRoom
from django.db.models import Q
class NotAFriendException(Exception):
    pass

def is_friend(owner_id, member_id):
    return Group.objects.filter(owner_id=owner_id, group_members__user_id=member_id).exists()

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
        data = json.loads(req.body.decode('utf-8'))
    except json.JSONDecodeError:
        return request_failed(4, 'Invalid JSON', 400)

    group_name = data.get('name')
    member_ids = data.get('members', []) 

    if not group_name or not isinstance(member_ids, list):
        return request_failed(5, 'Missing or invalid data', 400)

    try:
        owner = User.objects.get(name=username['username'])
        if owner.id in member_ids:
            return request_failed(11,'member_ids can\'t contain owner id',400)
    except User.DoesNotExist:
        return request_failed(6, 'User not found', 404)

    # 检查是否已经存在同名的群组
    if ChatRoom.objects.filter(owner=owner, name=group_name).exists():
        return request_failed(7, 'Group with this name already exists', 409)
    try:
        with transaction.atomic():
            # 创建群组
            group = ChatRoom.objects.create(name=group_name, owner=owner,type=ChatRoom.GROUP)

            # 为每个成员（包括群主）创建UserGroup记录
            for member_id in [owner.id] + member_ids:  # 包括群主自己
                try:
                    member = User.objects.get(id=member_id)
                    group.members.add(member)
                    # 假设is_friend函数检查成员是否为群主的好友，此逻辑可能需要根据您的应用逻辑调整
                    if not Group.objects.filter(owner_id=owner.id, group_members__user_id=member.id).exists():
                        raise NotAFriendException(f'User {member_id} is not a friend')
                    ConversationMember.objects.create(conversation_id=group.id, member_user_id=member_id)
                


                # 进行其他数据库操作...
            
                except NotAFriendException as e:
                    transaction.set_rollback(True)
                    return request_failed(8, str(e), 403)
                except User.DoesNotExist:
                    transaction.set_rollback(True)
                    return request_failed(9, f'Member {member_id} not found', 404)
    except Exception as e:
        transaction.set_rollback(True)
        return request_failed(10, f'Unexpected error: {str(e)}', 500)
            

    return request_success({'message': 'Group created successfully', 'room_id': group.id})

@require_http_methods(["POST"])  
def chatroom_details(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(2, 'Authorization token is missing', 401)
    # 检查JWT令牌是否有效
    username = check_jwt_token(token)
   
    if username is None:
        return request_failed(3, 'Invalid token', 401)
    
    try:
        # 从请求体中解析JSON数据
        data = json.loads(req.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')  # 获取chatroom_id
        
        if not chatroom_id:
            return request_failed(1,'Missing chatroom_id', 400)

        # 获取群聊实例
        chatroom = ChatRoom.objects.get(id=chatroom_id)

        if chatroom.type != ChatRoom.GROUP:
            return request_failed(8, 'Only group chatrooms can take information', 400)
        # 获取群成员信息
        members_info = []
        for member in chatroom.members.all():
            role = "member"
            if member == chatroom.owner:
                role = "owner"
            elif member in chatroom.admins.all():
                role = "admin"
            members_info.append({
                'id': member.id,
                'name': member.name,  # Assuming the User model has 'name'
                'role': role
            })

        
        # 获取群公告信息
        notices = chatroom.notices.all().values('title', 'text', 'create_time').order_by('-create_time')

    except ChatRoom.DoesNotExist:
        return request_failed(2,'ChatRoom not found', 404)
    except json.JSONDecodeError:
        return request_failed(3,'Invalid JSON', 400)

    # 构建响应数据
    chatroom_data = {
        'name': chatroom.name,
        'members': members_info,
        'notices': list(notices)
    }

    return request_success(chatroom_data)


@require_http_methods(["POST"])
def assign_admins(request):
    # 获取和验证token
    token = request.headers.get('Authorization', None)
    if not token:
        return request_failed(1,'Authorization token is missing', 401)
    
    user = check_jwt_token(token)
    if not user:
        return request_failed(2,'Invalid or expired token', 401)

   
    try:
        data = json.loads(request.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')
        admin_ids = data.get('admin_ids', [])
    except json.JSONDecodeError:
        return request_failed(4,'Invalid JSON', 400)
    try:
        # 确保请求者是群主
        chatroom = ChatRoom.objects.get(id=chatroom_id, owner__name=user['username'])
    except ChatRoom.DoesNotExist:
        return request_failed(3,'ChatRoom not found or you are not the owner', 404)
    
    if chatroom.type != ChatRoom.GROUP:
            return request_failed(8, 'Only group chatrooms can invite others', 400)
    # 验证所有指定的管理员是否为群成员
    for admin_id in admin_ids:
        if not chatroom.members.filter(id=admin_id).exists():
            return request_failed(5,f'User {admin_id} is not a member of the chatroom', 400)
    
    # 更新管理员列表
    with transaction.atomic():
        # 添加新的管理员
        chatroom.admins.add(*admin_ids)


    return request_success({'message': 'Admins assigned successfully'})

@require_http_methods(["POST"])
def transfer_ownership(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    if not username:
        return request_failed(2, 'Invalid or expired token', 401)
    
    try:
        data = json.loads(req.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')
        new_owner_id = data.get('new_owner_id')

        if not chatroom_id or not new_owner_id:
            return request_failed(3, 'Missing chatroom_id or new_owner_id', 400)

        chatroom = ChatRoom.objects.get(id=chatroom_id)
        user = User.objects.get(name=username['username'])
        if chatroom.type != ChatRoom.GROUP:
            return request_failed(8, 'Only group chatrooms can invite others', 400)
        # 确保请求者是当前的群主
        if chatroom.owner != user:
            return request_failed(4, 'You are not the owner of this chatroom', 403)
        
        # 确保新群主是群聊的成员
        new_owner = User.objects.get(id=new_owner_id)
        if not chatroom.members.filter(id=new_owner_id).exists():
            return request_failed(5, 'The new owner must be a member of the chatroom', 400)
        
        # 如果新群主是管理员，则先从管理员列表中移除
        if chatroom.admins.filter(id=new_owner_id).exists():
            chatroom.admins.remove(new_owner)
        
        # 转让群主身份
        chatroom.owner = new_owner
        chatroom.save()
        
    except ChatRoom.DoesNotExist:
        return request_failed(6, 'ChatRoom not found', 404)
    except User.DoesNotExist:
        return request_failed(7, 'New owner not found', 404)
    except json.JSONDecodeError:
        return request_failed(8, 'Invalid JSON', 400)
    except Exception as e:
        return request_failed(9, f'Unexpected error: {str(e)}', 500)

    # 成功响应
    return request_success({'message': 'Ownership transferred successfully'})

@require_http_methods(["POST"])
def remove_member(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    if not username:
        return request_failed(2, 'Invalid or expired token', 401)
    
    try:
        data = json.loads(req.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')
        member_id = data.get('member_id')

        if not chatroom_id or not member_id:
            return request_failed(3, 'Missing chatroom_id or member_id', 400)

        chatroom = ChatRoom.objects.get(id=chatroom_id)
        user = User.objects.get(name=username['username'])
        # 确认用户是否有权限移除成员
        if chatroom.owner != user and user not in chatroom.admins.all():
            return request_failed(4, 'You do not have permission to remove members', 403)
        
        member = User.objects.get(id=member_id)

        # 额外的权限检查
        if chatroom.owner == member:
            return request_failed(5, 'Cannot remove the chatroom owner', 403)
        
        if user != chatroom.owner and member in chatroom.admins.all():
            return request_failed(6, 'Only the chatroom owner can remove admins', 403)
        
        # 执行移除操作
        chatroom.members.remove(member)
        ConversationMember.objects.filter(conversation_id=chatroom_id, member_user_id=member_id).delete()
        
    except ChatRoom.DoesNotExist:
        return request_failed(7, 'ChatRoom not found', 404)
    except User.DoesNotExist:
        return request_failed(8, 'Member not found', 404)
    except json.JSONDecodeError:
        return request_failed(9, 'Invalid JSON', 400)
    except Exception as e:
        return request_failed(10, f'Unexpected error: {str(e)}', 500)

    return request_success({'message': 'Member removed successfully'})


@require_http_methods(["POST"])
def invite_friend(request):
    token = request.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    user = check_jwt_token(token)
    if not user:
        return request_failed(2, 'Invalid or expired token', 401)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')
        friend_id = data.get('friend_id')
        
        chatroom = ChatRoom.objects.get(id=chatroom_id)
        friend = User.objects.get(id=friend_id)
        user = User.objects.get(name=user['username'])
        # 检查是否已是群成员

        if chatroom.type != ChatRoom.GROUP:
            return request_failed(8, 'Only group chatrooms can invite others', 400)
        
        if chatroom.members.filter(id=friend_id).exists():
            return request_failed(3, 'The user is already a member of the chatroom', 400)
        
        if Invitation.objects.filter(chatroom=chatroom, invited=friend, status='pending').exists():
            return request_failed(9, 'Invitation already sent to the user', 400)
        
        # 如果邀请者是群主或管理员，直接添加好友到群聊
        if user == chatroom.owner or user in chatroom.admins.all():
            chatroom.members.add(friend)
            ConversationMember.objects.create(conversation_id=chatroom.id, member_user_id=friend.id)
            return request_success({'message': 'Friend added to chatroom'})
        
        # 否则，创建一个待审核的邀请
        invitaion = Invitation.objects.create(
            chatroom=chatroom,
            invited=friend,
            inviter=user,
            status='pending'
        )
        
        return request_success({'message': 'Invitation sent, waiting for approval',"invitation_id":invitaion.id})
    
    except ChatRoom.DoesNotExist:
        return request_failed(4, 'ChatRoom not found', 404)
    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
    except json.JSONDecodeError:
        return request_failed(6, 'Invalid JSON', 400)
    except Exception as e:
        return request_failed(7, f'Unexpected error: {str(e)}', 500)
    
@require_http_methods(["POST"])
def handle_invitation(request):
    token = request.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    user = check_jwt_token(token)
    if not user:
        return request_failed(2, 'Invalid or expired token', 401)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        invitation_id = data.get('invitation_id')
        action = data.get('action')
        if not invitation_id or not action:
            return request_failed(3, 'invitation_id and action are required', 400)
        user = User.objects.get(name=user['username'])
        invitation = Invitation.objects.get(id=invitation_id)
        
        # 只有群主或管理员可以审核邀请
        if user != invitation.chatroom.owner and user not in invitation.chatroom.admins.all():
            return request_failed(3, 'Only the chatroom owner or admins can approve invitations', 403)
        
        # 审核邀请
        if invitation.status != 'pending':
            return request_failed(4, 'This invitation is already been handled', 403)
        elif action == 'accept':
            invitation.status = 'approved'
            invitation.save()
            invitation.chatroom.members.add(invitation.invited)
            ConversationMember.objects.create(conversation_id=invitation.chatroom.id, member_user_id=invitation.invited.id)
            
            return request_success({'message': 'Invitation approved'})
        else :
            invitation.status = 'rejected'
            invitation.save()
            return request_success({'message': 'Invitation rejected'})
    
    except Invitation.DoesNotExist:
        return request_failed(4, 'Invitation not found', 404)
    except Exception as e:
        return request_failed(5, f'Unexpected error: {str(e)}', 500)
    
@require_http_methods(["GET"])
def get_pending_invitations(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1,'Authorization token is missing',401)

    username = check_jwt_token(token)
    if not username:
        return request_failed(2,'Invalid or expired token', 401)

    user = User.objects.get(name=username['username'])
    # 获取当前用户管理的群聊中的所有未处理邀请
    pending_invitations = Invitation.objects.filter(Q(chatroom__owner=user) | Q(chatroom__admins=user), status='pending')

    # 构建每个邀请的详细信息列表
    invitations_data = []
    for invitation in pending_invitations:
        invitation_info = {
            'invitation_id': invitation.id,
            'chatroom_id': invitation.chatroom.id,
            'chatroom_name': invitation.chatroom.name,
            'invited_user_id': invitation.invited.id,
            'invited_username': invitation.invited.name,
            'inviter_user_id': invitation.inviter.id,
            'inviter_username': invitation.inviter.name,
            'create_time': invitation.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        invitations_data.append(invitation_info)

    return request_success({'pending_invitations': invitations_data})

@require_http_methods(["POST"])
def leave_group(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    if not username:
        return request_failed(2, 'Invalid or expired token', 401)
    
    try:
        user = User.objects.get(name=username['username'])
        data = json.loads(req.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')

        chatroom = ChatRoom.objects.get(id=chatroom_id)

        # 检查用户是否是群主
        if chatroom.owner == user:
            return request_failed(8, 'Owner cannot leave the chatroom. Transfer ownership or delete the chatroom first.', 403)
        
        # 检查用户是否是群成员
        if user not in chatroom.members.all():
            return request_failed(3, 'User is   not a member of the chatroom', 400)
        
        
        # 退出群聊
        # 删除用户在该群聊的 ConversationMember 记录
        try:
            with transaction.atomic():
                ConversationMember.objects.filter(conversation_id=chatroom_id, member_user_id=user.id).delete()
                if user in chatroom.admins.all():
                    chatroom.admins.remove(user)
                chatroom.members.remove(user)
        except Exception as e:
            transaction.set_rollback(True)
            return request_failed(9, f'Unexpected error: {str(e)}', 500)

        
        return request_success({'message': 'User left the chatroom'})
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    except ChatRoom.DoesNotExist:
        return request_failed(5, 'ChatRoom not found', 404)
    except json.JSONDecodeError:
        return request_failed(6, 'Invalid JSON', 400)
    except Exception as e:
        return request_failed(7, f'Unexpected error: {str(e)}', 500)
    
@require_http_methods(["DELETE"])
def dissolve_chatroom(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    username = check_jwt_token(token)
    if not username:
        return request_failed(2, 'Invalid or expired token', 401)
    
    
    
    try:
        user = User.objects.get(name=username['username'])  # 确保这里按照实际情况获取用户名
        data = json.loads(req.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')
        chatroom = ChatRoom.objects.get(id=chatroom_id)
        
        # 确认用户是否是群主
        if chatroom.type != ChatRoom.GROUP:
            return request_failed(8, 'Only group chatrooms can be dissolved', 400)
        
        if chatroom.owner != user:
            return request_failed(3, 'Only the chatroom owner can dissolve the chatroom', 403)
        
        # 删除群聊相关的ConversationMember和MessageStatus实例
        ConversationMember.objects.filter(conversation_id=chatroom_id).delete()
        MessageStatus.objects.filter(conversation_id=chatroom_id).delete()
        
        # 解散群聊（删除ChatRoom实例）
        chatroom.delete()
        
        return request_success({'message': 'Chatroom dissolved successfully'})
    except User.DoesNotExist:
        return request_failed(4, 'User not found', 404)
    except ChatRoom.DoesNotExist:
        return request_failed(5, 'ChatRoom not found', 404)
    except json.JSONDecodeError:
        return request_failed(6, 'Invalid JSON', 400)
    except Exception as e:
        return request_failed(7, f'Unexpected error: {str(e)}', 500)
    
@require_http_methods(["POST"])
def post_notice(req):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)

    username = check_jwt_token(token)
    if not username:
        return request_failed(2, 'Invalid or expired token', 401)

    try:
        user = User.objects.get(name=username['username'])
        data = json.loads(req.body.decode('utf-8'))
        chatroom_id = data.get('chatroom_id')
        title = data.get('title')
        text = data.get('text')

        if not chatroom_id or not title or not text:
            return request_failed(3, 'Missing required fields', 400)

        chatroom = ChatRoom.objects.get(id=chatroom_id)

        if chatroom.type != ChatRoom.GROUP:
            return request_failed(8, 'Only group chatrooms can post notices', 400)
        # 检查是否是群主或管理员
        if chatroom.owner != user and user not in chatroom.admins.all():
            return request_failed(4, 'Not authorized to post notices', 403)
                
        conversation_member = ConversationMember.objects.get(
            conversation_id=chatroom_id, 
            member_user_id=user.id,
        )

         # 创建公告
        notice = ChatRoomNotice.objects.create(
            promulgator=user,
            chatroom=chatroom,
            title=title,
            text=text
        )
        return request_success({'message': 'Notice posted successfully',"notice_id":notice.id})
    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
    except ChatRoom.DoesNotExist:
        return request_failed(6, 'ChatRoom not found', 404)
    except Exception as e:
        return request_failed(7, f'Unexpected error: {str(e)}', 500)

# @require_http_methods(["GET"])
# def get_notices_with_read_status(req:HttpRequest):
#     token = req.headers.get('Authorization', None)
#     if not token:
#         return request_failed(1, 'Authorization token is missing', 401)

#     username = check_jwt_token(token)
#     if not username:
#         return request_failed(2, 'Invalid or expired token', 401)
#     try:
#         data = json.loads(req.body.decode('utf-8'))
#         print(data)
#         chatroom_id = data.get('chatroom_id')
#         print(chatroom_id)
#         if not chatroom_id:
#             return request_failed(3, 'Missing chatroom_id', 400)
        
#         user = User.objects.get(name=username['username'])
#         chatroom = ChatRoom.objects.get(id=chatroom_id)

#         if chatroom.type != ChatRoom.GROUP:
#             return request_failed(8, 'Only group chatrooms can post notices', 400)
#         conversation_member = ConversationMember.objects.filter(conversation_id=chatroom_id, member_user_id=user.id).first()
#         if not conversation_member:
#             return request_failed(4, 'User is not a member of the chatroom', 403)
        
#         notices = ChatRoomNotice.objects.filter(chatroom=chatroom).order_by('-create_time')
#         notices_with_read_status = [{
#             'title': notice.title,
#             'text': notice.text,
#             'create_time': notice.create_time.strftime('%Y-%m-%d %H:%M:%S'),
#             'is_read': conversation_member.read_announcements.filter(id=notice.id).exists(),
#             'notice_id': notice.id
#         } for notice in notices]

#         return request_success({'notices': notices_with_read_status})
#     except User.DoesNotExist:
#         return request_failed(5, 'User not found', 404)
#     except ChatRoom.DoesNotExist:
#         return request_failed(6, 'ChatRoom not found', 404)
#     except Exception as e:
#         return request_failed(7, f'Unexpected error: {str(e)}', 500)
    
# @require_http_methods(["GET"])
# def get_latest_unread_notice(req:HttpRequest):
#     token = req.headers.get('Authorization', None)
#     if not token:
#         return request_failed(1, 'Authorization token is missing', 401)

#     username = check_jwt_token(token)
#     if not username:
#         return request_failed(2, 'Invalid or expired token', 401)

#     try:
#         data = json.loads(req.body.decode('utf-8'))
#         chatroom_id = data.get('chatroom_id')
#         if not chatroom_id:
#             return request_failed(3, 'Missing chatroom_id', 400)

#         user = User.objects.get(name=username['username'])
#         chatroom = ChatRoom.objects.get(id=chatroom_id)

#         if chatroom.type != ChatRoom.GROUP:
#             return request_failed(8, 'Only group chatrooms can invite others', 400)
#         conversation_member = ConversationMember.objects.filter(conversation_id=chatroom_id, member_user_id=user.id).first()
#         if not conversation_member:
#             return request_failed(4, 'User is not a member of the chatroom', 403)

#         # 获取最新的未读公告
#         latest_unread_notice = ChatRoomNotice.objects.filter(chatroom=chatroom).exclude(read_by=conversation_member).order_by('-create_time').first()
#         if latest_unread_notice:
#             response_data = {
#                 'title': latest_unread_notice.title,
#                 'text': latest_unread_notice.text,
#                 'notice_id': latest_unread_notice.id,
#                 'promulgator':latest_unread_notice.promulgator.name
#             }
#             return request_success({'latest_unread_notice': response_data})
#         else:
#             return request_success({'message': 'No unread notices found'})
#     except User.DoesNotExist:
#         return request_failed(5, 'User not found', 404)
#     except ChatRoom.DoesNotExist:
#         return request_failed(6, 'ChatRoom not found', 404)
#     except Exception as e:
#         return request_failed(7, f'Unexpected error: {str(e)}', 500)


# @require_http_methods(["PUT"])
# def set_notice_read(req):
    
#     token = req.headers.get('Authorization', None)
#     if not token:
#         return request_failed(1, 'Authorization token is missing', 401)

#     username = check_jwt_token(token)
#     if not username:
#         return request_failed(2, 'Invalid or expired token', 401)

#     try:
#         data = json.loads(req.body.decode('utf-8'))
#         notice_id = data.get('notice_id')
#         if not notice_id:
#             return request_failed(3, 'Missing notice_id', 400)

#         user = User.objects.get(name=username['username'])
#         notice = ChatRoomNotice.objects.get(id=notice_id)
        
#         # 假设用户只属于一个聊天室，或者公告ID全局唯一。如果有多个聊天室，你可能需要提供更多信息来精确获取ConversationMember
#         conversation_member = ConversationMember.objects.filter(member_user_id=user.id, conversation_id=notice.chatroom.id).first()
#         if not conversation_member:
#             return request_failed(4, 'Conversation member not found', 404)

#         # 将公告添加到已读
#         conversation_member.read_announcements.add(notice)

#         return request_success({'message': 'Notice marked as read successfully'})
#     except User.DoesNotExist:
#         return request_failed(5, 'User not found', 404)
#     except ChatRoomNotice.DoesNotExist:
#         return request_failed(6, 'Notice not found', 404)
#     except Exception as e:
#         return request_failed(7, f'Unexpected error: {str(e)}', 500)
    
@require_http_methods(["GET"])
def get_my_chatrooms(request):
    token = request.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    user_info = check_jwt_token(token)  # This function should return a username or User instance
    if not user_info:
        return request_failed(2, 'Invalid token', 401)
    
    try:
        user = User.objects.get(name=user_info['username'])  # Assuming the token returns a dictionary with username
    except User.DoesNotExist:
        return request_failed(3, 'User not found', 404)
    
    chatrooms = ChatRoom.objects.filter(members=user,type = ChatRoom.GROUP).values('id', 'name', 'avatar')
    
    return request_success({
        'chatrooms': list(chatrooms)
    })

@require_http_methods(["GET"])
def get_identity(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    user_name = check_jwt_token(token)
    if not user_name:
        return request_failed(2, 'Invalid or expired token', 401)
    user_name = user_name['username']

    room_id = req.GET.get('room_id')
    if not room_id:
        return request_failed(3, 'Room ID is missing', 400)

    try:
        user = User.objects.get(name=user_name)
        chatroom = ChatRoom.objects.filter(id=room_id, type=ChatRoom.GROUP).first()
        if not chatroom:
            return request_failed(4, 'Chat room not found or not a group chat', 404)

        is_owner = chatroom.owner == user

        is_admin = user in chatroom.admins.all()

        return request_success({
            'is_owner': is_owner,
            'is_admin': is_admin
            })
        
    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
    except Exception as e:
        return request_failed(6, 'Server error', 500, extra_info=str(e))

@require_http_methods(["GET"])
def judge_friend(req:HttpRequest):
    token = req.headers.get('Authorization', None)
    if not token:
        return request_failed(1, 'Authorization token is missing', 401)
    
    user_name = check_jwt_token(token)
    if not user_name:
        return request_failed(2, 'Invalid or expired token', 401)
    user_name = user_name['username']

    member_id = req.GET.get('member_id')
    room_id = req.GET.get('room_id')
    if not member_id or not room_id:
        return request_failed(3, 'Friend ID or Room ID is missing', 400)

    try:
        user = User.objects.get(name=user_name)
        member = User.objects.get(id=member_id)
        room = ChatRoom.objects.get(id=room_id)

        # 检查两个用户是否都是聊天室的成员
        if user in room.members.all() and member in room.members.all():
            is_friend = Group.objects.filter(owner__id=user.id, group_members__user_id=member.id).exists()
            return request_success({'is_friend': is_friend})
        else:
            return request_failed(4, 'One or both users are not members of the specified room', 403)

    except User.DoesNotExist:
        return request_failed(5, 'User not found', 404)
    except ChatRoom.DoesNotExist:
        return request_failed(6, 'ChatRoom not found', 404)
    except Exception as e:
        return request_failed(7, 'Server error', 500)
        
        