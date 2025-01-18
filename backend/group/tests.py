from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
import random
from author.models import User
import hashlib
import hmac
import time
import json
from utils.utils_jwt import EXPIRE_IN_SECONDS, SALT, b64url_encode
from .views import *
# Create your tests here.
class groupTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(
            name='groupTest', email='test@example.com', password='123456'
        )
    # # ! Utility functions
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
    def create_user(self, username):
        self.client.post("/author/register", data={"userName": username, "password": '123456789'}, content_type="application/json")
    def add_friends(self, username_from, username_to):
        id = User.objects.get(name=username_to).id
        id_from = User.objects.get(name=username_from).id
        headers = self.generate_header(username_from)
        response1 = self.client.post("/friends/request/friend",{'to_user_id': id}, content_type="application/json", **headers)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['msg'], 'Friend request sent successfully.')
        self.assertEqual(response1.json()['code'], 0)
        headers = self.generate_header(username_to)
        response2 = self.client.get("/friends/require/friend", content_type="application/json", **headers)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(id_from, response2.json()['requests'][0]['from_user_id'])
        request_id = response2.json()['requests'][0]['id']
        headers = self.generate_header(username_to)
        response3 = self.client.post("/friends/request/friend/handle",{'request_id': request_id, 'action': 'accept'}, content_type="application/json", **headers)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()['message'], 'Friend request accepted.')
        self.assertEqual(response3.json()['code'], 0)
    # ! Test section
    # * Tests for /create
    # + normal case [POST]
    def test_create_group_normal(self):
        username1 = 'test_group'
        password1 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username1, "password": password1}, content_type="application/json")

        username2 = 'member2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        id2 = User.objects.get(name=username2).id
        username3 = 'member3'
        password3 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username3, "password": password3}, content_type="application/json")
        id3 = User.objects.get(name=username3).id
        header = self.generate_header(username1)
        self.add_friends(username1, username2)
        self.add_friends(username1, username3)
        response = self.client.post('/group/create', {'name': 'test_group', 'members':[id2, id3]}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Group created successfully')
        self.assertEqual(response.json()['room_id'], ChatRoom.objects.get(name='test_group').id)
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 3)

    # + no token
    def test_create_group_no_token(self):
        response = self.client.post('/group/create', {'name': 'test_group'}, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')

    # + no username
    def test_create_group_no_username(self):
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.post('/group/create', {'name': 'test_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')

    # + no group name or 'members' is not a list
    def test_create_group_invalid_data(self):
        header = self.generate_header('groupTest')
        response = self.client.post('/group/create', {'members': [1, 2]}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Missing or invalid data')
        response = self.client.post('/group/create', {'name': 'test_group', 'members': 1}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Missing or invalid data')

    # + Owner not exist in db
    def test_create_group_owner_not_exist(self):
        header = self.generate_header('not_exist')
        response = self.client.post('/group/create', {'name': 'test_group', 'members':[]}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'User not found')

    # + Group name already exists
    def test_create_group_group_exists(self):
        username1 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password1 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username1, "password": password1}, content_type="application/json")
        username2 = 'member2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        id2 = User.objects.get(name=username2).id
        username3 = 'member3'
        password3 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username3, "password": password3}, content_type="application/json")
        id3 = User.objects.get(name=username3).id
        header = self.generate_header(username1)
        self.add_friends(username1, username2)
        self.add_friends(username1, username3)
        response = self.client.post('/group/create', {'name': 'test_group', 'members':[id2, id3]}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Group created successfully')
        self.assertEqual(response.json()['room_id'], ChatRoom.objects.get(name='test_group').id)
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 3)
        response = self.client.post('/group/create', {'name': 'test_group', 'members':[]}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['info'], 'Group with this name already exists')

    # + members are not friend
    def test_create_group_not_friend(self):
        username1 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password1 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username1, "password": password1}, content_type="application/json")
        username2 = 'member2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        id2 = User.objects.get(name=username2).id
        header = self.generate_header(username1)
        response = self.client.post('/group/create', {'name': 'test_group', 'members':[id2]}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['info'], f'User {id2} is not a friend')

    # + members not exist
    def test_create_group_member_not_exist(self):
        username1 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password1 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username1, "password": password1}, content_type="application/json")
        username2 = 'member2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        id2 = User.objects.get(name=username2).id
        header = self.generate_header(username1)
        response = self.client.post('/group/create', {'name': 'test_group', 'members':[-1]}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'Member -1 not found')

    # * Tests for /room/information
    # + normal case [POST]
    def test_chatroom_details_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/information', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['info'], 'Succeed')
        self.assertEqual(len(response.json()['members']),3)

    # + no token
    def test_chatroom_details_no_token(self):
        response = self.client.post('/group/room/information', {'chatroom_id': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')

    # + no username
    def test_chatroom_details_no_username(self):
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.post('/group/room/information', {'chatroom_id': 1}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')

    # + no chatroom_id
    def test_chatroom_details_no_chatroom_id(self):
        header = self.generate_header('groupTest')
        response = self.client.post('/group/room/information', content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Missing chatroom_id')

    # + chatroom_id not exist
    def test_chatroom_details_chatroom_not_exist(self):
        header = self.generate_header('groupTest')
        response = self.client.post('/group/room/information', {'chatroom_id': -1}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'ChatRoom not found')

    # * Tests for /room/setadmins
    # + normal case [POST]
    def test_assign_admin_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        response = self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['info'], 'Succeed')
        self.assertEqual(ChatRoom.objects.get(name='test_group').admins.count(), 1)

    # + no token
    def test_assign_admin_no_token(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/setadmins', {'chatroom_id': 1, 'admin_ids':[1]}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(ChatRoom.objects.get(name='test_group').admins.count(), 0)
    # + no username
    def test_assign_admin_no_username(self):
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.post('/group/room/setadmins', {'chatroom_id': 1, 'admin_ids':[1]}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'], 'Invalid or expired token')
    
    # + chatroom not exist
    def test_assign_admin_chatroom_not_exist(self):
        header = self.generate_header('groupTest')
        response = self.client.post('/group/room/setadmins', {'chatroom_id': -1, 'admin_ids':[1]}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'], 'ChatRoom not found or you are not the owner')

    # + admin_id not in chatroom
    def test_assign_admin_admin_not_in_chatroom(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':[-1]}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 5)
        self.assertEqual(response.json()['info'], 'User -1 is not a member of the chatroom')
    
    # # Tests for /room/transfer
    # + normal case [POST]
    def test_transfer_owenership_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        response = self.client.post('/group/room/transfer', {'chatroom_id': chatroom_id, 'new_owner_id': User.objects.get(name='member2').id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'Ownership transferred successfully')
        self.assertEqual(ChatRoom.objects.get(name='test_group').admins.count(), 0)

    # + no token
    def test_transfer_owenership_no_token(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        response = self.client.post('/group/room/transfer', {'chatroom_id': chatroom_id, 'new_owner_id': User.objects.get(name='member2').id}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')
        self.assertEqual(ChatRoom.objects.get(name='test_group').admins.count(), 1)
    
    # + no username
    def test_transfer_owenership_no_username(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.post('/group/room/transfer', {'chatroom_id': chatroom_id, 'new_owner_id': User.objects.get(name='member2').id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')
        self.assertEqual(ChatRoom.objects.get(name='test_group').admins.count(), 1)

    # + chatroom not exist or member not exist
    def test_transfer_ownership_chatroom_not_exist(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        self.client.post('/group/room/setadmins', {'admin_ids':admin_ids}, content_type='application/json', **header)
        response = self.client.post('/group/room/transfer', {'new_owner_id': User.objects.get(name='member2').id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'],'Missing chatroom_id or new_owner_id')

    # + chatroom is not owned by user
    def test_transfer_ownership_not_owned(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        header = self.generate_header('member2')
        response = self.client.post('/group/room/transfer', {'chatroom_id': chatroom_id, 'new_owner_id': User.objects.get(name='member2').id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 4)
        self.assertEqual(response.json()['info'],'You are not the owner of this chatroom')

    # + chatroom type is private, not group
    def test_transfer_ownership_not_group(self):
        self.create_user('user1')
        self.create_user('user2')
        self.add_friends('user1','user2')
        header = self.generate_header('user1')
        chatroom_name = str(User.objects.get(name='user1').id)+"-"+str(User.objects.get(name='user2').id)
        chatroom_id = ChatRoom.objects.get(name=chatroom_name).id
        response = self.client.post('/group/room/transfer', {'chatroom_id': chatroom_id, 'new_owner_id':User.objects.get(name='user2').id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 8)
        self.assertEqual(response.json()['info'],'Only group chatrooms can invite others')

    # + new owner not in chatroom
    def test_transfer_ownership_new_owner_not_in_chatroom(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        self.create_user('user1')
        new_owner_id = User.objects.get(name='user1').id
        response = self.client.post('/group/room/transfer', {'chatroom_id': chatroom_id, 'new_owner_id': new_owner_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 5)
        self.assertEqual(response.json()['info'],'The new owner must be a member of the chatroom')

    # # Tests for /room/remove
    # + normal case [POST]
    def test_remove_member_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        member_id = User.objects.get(name='member2').id
        response = self.client.post('/group/room/remove', {'chatroom_id': chatroom_id, 'member_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'Member removed successfully')
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 2)

    # + no token
    def test_remove_member_no_token(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        member_id = User.objects.get(name='member2').id
        response = self.client.post('/group/room/remove', {'chatroom_id': chatroom_id, 'member_id': member_id}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')
    

    # + no username
    def test_remove_member_no_username(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header ={
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        member_id = User.objects.get(name='member2').id
        response = self.client.post('/group/room/remove', {'chatroom_id': chatroom_id, 'member_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')
    
    # + chatroom not exist or member not exist
    def test_remove_member_chatroom_not_exist(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        member_id = User.objects.get(name='member2').id
        response = self.client.post('/group/room/remove', {'member_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'],'Missing chatroom_id or member_id')

    # + no permission to remove
    def test_remove_member_no_permission(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('member2')
        member_id = User.objects.get(name='member2').id
        response = self.client.post('/group/room/remove', {'chatroom_id': chatroom_id, 'member_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 4)
        self.assertEqual(response.json()['info'],'You do not have permission to remove members')

    # + cannot remove owner
    def test_remove_member_cannot_remove_owner(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        member_id = User.objects.get(name='test_group').id
        response = self.client.post('/group/room/remove', {'chatroom_id': chatroom_id, 'member_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 5)
        self.assertEqual(response.json()['info'],'Cannot remove the chatroom owner')

    # + only owner can remove admins
    def test_remove_member_only_owner_can_remove_admins(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        header = self.generate_header('member2')
        member_id = User.objects.get(name='member2').id
        response = self.client.post('/group/room/remove', {'chatroom_id': chatroom_id, 'member_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 6)
        self.assertEqual(response.json()['info'],'Only the chatroom owner can remove admins')

    # # Tests for /room/invite
    # + normal case [POST], user is owner or admin
    def test_invite_friend_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        self.create_user('member4')
        self.add_friends('test_group', 'member4')
        member_id = User.objects.get(name='member4').id
        response = self.client.post('/group/room/invite', {'chatroom_id': chatroom_id, 'friend_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'Friend added to chatroom')
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 4)
    
    # + normal case [POST], user is member
    def test_invite_friend_normal2(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        self.create_user('member4')
        self.add_friends('member3', 'member4')
        member_id = User.objects.get(name='member4').id
        header = self.generate_header('member3')
        response = self.client.post('/group/room/invite', {'chatroom_id': chatroom_id, 'friend_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 3)
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        self.assertEqual(response.json()['message'], 'Invitation sent, waiting for approval')
        self.assertEqual(response.json()['invitation_id'], invitation_id)

    # + no token
    def test_invite_friend_no_token(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        self.create_user('member4')
        self.add_friends('test_group', 'member4')
        member_id = User.objects.get(name='member4').id
        response = self.client.post('/group/room/invite', {'chatroom_id': chatroom_id, 'friend_id': member_id}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 3)

    # + no username
    def test_invite_friend_no_username(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        self.create_user('member4')
        self.add_friends('test_group', 'member4')
        member_id = User.objects.get(name='member4').id
        response = self.client.post('/group/room/invite', {'chatroom_id': chatroom_id, 'friend_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 3)

    # + chatroom type is private, not group
    def test_invite_friend_not_group(self):
        self.create_user('user1')
        self.create_user('user2')
        self.add_friends('user1','user2')
        header = self.generate_header('user1')
        chatroom_name = str(User.objects.get(name='user1').id)+"-"+str(User.objects.get(name='user2').id)
        chatroom_id = ChatRoom.objects.get(name=chatroom_name).id
        response = self.client.post('/group/room/invite', {'chatroom_id': chatroom_id, 'friend_id': User.objects.get(name='user2').id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 8)
        self.assertEqual(response.json()['info'],'Only group chatrooms can invite others')

    # + user already in group
    def test_invite_friend_already_in_group(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        member_id = User.objects.get(name='member2').id
        response = self.client.post('/group/room/invite', {'chatroom_id': chatroom_id, 'friend_id': member_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'],'The user is already a member of the chatroom')

    # # Tests for /room/handle
    # + normal case [POST]
    def test_handle_invitation_normal(self):
        self.test_invite_friend_normal2()
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        response = self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        header = self.generate_header('member2')
        response = self.client.post('/group/room/handle', {'invitation_id': invitation_id, 'action': 'accept'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'Invitation approved')
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 4)
    def test_handle_invitation_normal2(self):
        self.test_invite_friend_normal2()
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        response = self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        header = self.generate_header('member2')
        response = self.client.post('/group/room/handle', {'invitation_id': invitation_id, 'action': 'reject'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'Invitation rejected')
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 3)

    # + no token
    def test_handle_invitation_no_token(self):
        self.test_invite_friend_normal2()
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/handle', {'invitation_id': invitation_id, 'action': 'accept'}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')

    # + no username
    def test_handle_invitation_no_username(self):
        self.test_invite_friend_normal2()
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.post('/group/room/handle', {'invitation_id': invitation_id, 'action': 'accept'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')

    # + invitation not exist
    def test_handle_invitation_not_exist(self):
        self.test_invite_friend_normal2()
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/handle', {'invitation_id': -1, 'action': 'accept'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 4)
        self.assertEqual(response.json()['info'],'Invitation not found')

    # + user is not owner or admin
    def test_handle_invitation_no_permission(self):
        self.test_invite_friend_normal2()
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        header = self.generate_header('member3')
        response = self.client.post('/group/room/handle', {'invitation_id': invitation_id, 'action': 'accept'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'],'Only the chatroom owner or admins can approve invitations')

    # + invitation already handled
    def test_handle_invitation_already_handled(self):
        self.test_invite_friend_normal2()
        invitation_id = Invitation.objects.get(inviter=User.objects.get(name='member3')).id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/handle', {'invitation_id': invitation_id, 'action': 'accept'}, content_type='application/json', **header)
        response = self.client.post('/group/room/handle', {'invitation_id': invitation_id, 'action': 'accept'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 4)
        self.assertEqual(response.json()['info'],'This invitation is already been handled')

    # # Tests for /room/get/invitation
    def test_get_pending_invitations_normal(self):
        self.test_invite_friend_normal2()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        response = self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        header = self.generate_header('member2')
        response = self.client.get('/group/room/get/invitation', content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(len(response.json()['pending_invitations']), 1)

    def test_get_pending_invitations_normal2(self):
        self.test_invite_friend_normal2()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        admin_ids = [User.objects.get(name='member2').id]
        response = self.client.post('/group/room/setadmins', {'chatroom_id': chatroom_id, 'admin_ids':admin_ids}, content_type='application/json', **header)
        header = self.generate_header('member3')
        response = self.client.get('/group/room/get/invitation', content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(len(response.json()['pending_invitations']), 0)

    # + no token
    def test_get_pending_invitations_no_token(self):
        self.test_invite_friend_normal2()
        response = self.client.get('/group/room/get/invitation', content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')

    # + no username
    def test_get_pending_invitations_no_username(self):
        self.test_invite_friend_normal2()
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.get('/group/room/get/invitation', content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')

    # # Tests for /room/leave
    # + normal case [POST]
    def test_leave_chatroom_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('member2')
        response = self.client.post('/group/room/leave', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'User left the chatroom')
        self.assertEqual(ChatRoom.objects.get(name='test_group').members.count(), 2)

    # + no token
    def test_leave_chatroom_no_token(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('member2')
        response = self.client.post('/group/room/leave', {'chatroom_id': chatroom_id}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')

    # + no username
    def test_leave_chatroom_no_username(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.post('/group/room/leave', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')

    # # Tests for /room/dissolve
    # + normal case [POST]
    def test_dissolve_chatroom_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.delete('/group/room/dissolve', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'Chatroom dissolved successfully')
        self.assertEqual(ChatRoom.objects.filter(name='test_group').count(), 0)

    # + no token
    def test_dissolve_chatroom_no_token(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.delete('/group/room/dissolve', {'chatroom_id': chatroom_id}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')

    # + no username
    def test_dissolve_chatroom_no_username(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.delete('/group/room/dissolve', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')

    #+ user not exist
    def test_dissolve_chatroom_user_not_exist(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('userNotExist')
        response = self.client.delete('/group/room/dissolve', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 4)
        self.assertEqual(response.json()['info'],'User not found')

    # + chatroom not exist
    def test_dissolve_chatroom_chatroom_not_exist(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.delete('/group/room/dissolve', {'chatroom_id': -1}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 5)
        self.assertEqual(response.json()['info'],'ChatRoom not found')

    # + user is not owner
    def test_dissolve_chatroom_not_owner(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('member2')
        response = self.client.delete('/group/room/dissolve', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'],'Only the chatroom owner can dissolve the chatroom')

    # + chatroom type is private, not group
    def test_dissolve_chatroom_not_group(self):
        self.create_user('user1')
        self.create_user('user2')
        self.add_friends('user1','user2')
        header = self.generate_header('user1')
        chatroom_name = str(User.objects.get(name='user1').id)+"-"+str(User.objects.get(name='user2').id)
        chatroom_id = ChatRoom.objects.get(name=chatroom_name).id
        response = self.client.delete('/group/room/dissolve', {'chatroom_id': chatroom_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 8)
        self.assertEqual(response.json()['info'],'Only group chatrooms can be dissolved')

    # # Tests for /room/post/notice
    # + normal case [POST]
    def test_post_notice_normal(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/post/notice', {'chatroom_id': chatroom_id, 'title': 'test_title', 'text':'test_text'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['message'],'Notice posted successfully')
        self.assertEqual(len(ChatRoomNotice.objects.filter(title='test_title')), 1)

    # + no token
    def test_post_notice_no_token(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/post/notice', {'chatroom_id': chatroom_id, 'title': 'test_title', 'text':'test_text'}, content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')

    # + no username
    def test_post_notice_no_username(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
        }
        response = self.client.post('/group/room/post/notice', {'chatroom_id': chatroom_id, 'title': 'test_title', 'text':'test_text'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid or expired token')

    # + no chatroom_id
    def test_post_notice_no_chatroom_id(self):
        self.test_create_group_normal()
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/post/notice', {'title': 'test_title', 'text':'test_text'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'],'Missing required fields')

    # + chatroom not exist
    def test_post_notice_chatroom_not_exist(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('test_group')
        response = self.client.post('/group/room/post/notice', {'chatroom_id': -1, 'title': 'test_title', 'text':'test_text'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 6)
        self.assertEqual(response.json()['info'],'ChatRoom not found')

    # + user not found
    def test_post_notice_user_not_found(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('userNotExist')
        response = self.client.post('/group/room/post/notice', {'chatroom_id': chatroom_id, 'title': 'test_title', 'text':'test_text'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 5)
        self.assertEqual(response.json()['info'],'User not found')

    # + user is not owner or admin
    def test_post_notice_no_permission(self):
        self.test_create_group_normal()
        chatroom_id = ChatRoom.objects.get(name='test_group').id
        header = self.generate_header('member2')
        response = self.client.post('/group/room/post/notice', {'chatroom_id': chatroom_id, 'title': 'test_title', 'text':'test_text'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 4)
        self.assertEqual(response.json()['info'],'Not authorized to post notices')

    # chatroom is private, not group
    def test_post_notice_not_group(self):
        self.create_user('user1')
        self.create_user('user2')
        self.add_friends('user1','user2')
        header = self.generate_header('user1')
        chatroom_name = str(User.objects.get(name='user1').id)+"-"+str(User.objects.get(name='user2').id)
        chatroom_id = ChatRoom.objects.get(name=chatroom_name).id
        response = self.client.post('/group/room/post/notice', {'chatroom_id': chatroom_id, 'title': 'test_title', 'text':'test_text'}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 8)
        self.assertEqual(response.json()['info'],'Only group chatrooms can post notices')

    # # Tests for /room/getall
    # + normal case [GET]
    def test_get_all_chatrooms_normal(self):
        self.test_create_group_normal()
        header = self.generate_header('test_group')
        response = self.client.get('/group/room/getall', content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(len(response.json()['chatrooms']), 1)
    
    # + no token
    def test_get_all_chatrooms_no_token(self):
        self.test_create_group_normal()
        header = self.generate_header('test_group')
        response = self.client.get('/group/room/getall', content_type='application/json')
        self.assertEqual(response.json()['code'], 1)
        self.assertEqual(response.json()['info'],'Authorization token is missing')

    # + no username
    def test_get_all_chatrooms_no_username(self):
        self.test_create_group_normal()
        header = {
            'HTTP_AUTHORIZATION': 'invalid_token'
            }
        response = self.client.get('/group/room/getall', content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 2)
        self.assertEqual(response.json()['info'],'Invalid token')

    # + user not exist
    def test_get_all_chatrooms_user_not_exist(self):
        self.test_create_group_normal()
        header = self.generate_header('userNotExist')
        response = self.client.get('/group/room/getall', content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 3)
        self.assertEqual(response.json()['info'],'User not found')
