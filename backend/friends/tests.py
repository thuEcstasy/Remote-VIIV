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

class FriendTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(
            name='friendsTest', email='test@example.com', password='123456'
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
        self.assertEqual(response3.json()['message'], 'Friend request accepted.')
        self.assertEqual(response3.json()['code'], 0)
        self.assertEqual(response3.status_code, 200)
    # ! Test section
    # * Tests for /search/user
    # + normal case [GET]
    def test_search_users_normal(self):
        username = 'test_search_user'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response1 = self.client.get("/friends/search/user",{'query': 'test_search_user'}, content_type="application/json", **headers)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(response1.json()), 1)
        self.assertEqual(response1.json()[0].get('name'), 'test_search_user')
        response2= self.client.get("/friends/search/user",{'query': 'test_search_user2'}, content_type="application/json", **headers)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.json()), 0)
    # + no token
    def test_search_users_no_token(self):
        response = self.client.get("/friends/search/user",{'query': 'test_search_user'}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_search_users_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.get("/friends/search/user", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)

    # * Tests for /request/friend
    # + normal case [POST]
    def test_send_friend_request_normal(self):
        username0 = 'test_send_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username0, "password": password}, content_type="application/json")
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        id = User.objects.get(name=username0).id
        headers = self.generate_header(username)
        response1 = self.client.post("/friends/request/friend",{'to_user_id': id}, content_type="application/json", **headers)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['msg'], 'Friend request sent successfully.')
        self.assertEqual(response1.json()['code'], 0)

    # + no token
    def test_send_friend_request_no_token(self):
        response = self.client.post("/friends/request/friend",{'to_user_id': 7}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_send_friend_request_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.post("/friends/request/friend",{'to_user_id': 7}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)
    
    # + send request to self
    def test_send_friend_request_to_self(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        id = User.objects.get(name=username).id
        response = self.client.post("/friends/request/friend",{'to_user_id': id}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'You cannot send a friend request to yourself.')
        self.assertEqual(response.json()['code'], 4)

    # not created and friend_request is pending
    def test_send_friend_request_not_created_and_pending(self):
        username0 = 'test_send_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username0, "password": password}, content_type="application/json")
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        id = User.objects.get(name=username0).id
        headers = self.generate_header(username)
        response1 = self.client.post("/friends/request/friend",{'to_user_id': id}, content_type="application/json", **headers)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['msg'], 'Friend request sent successfully.')
        self.assertEqual(response1.json()['code'], 0)
        response2 = self.client.post("/friends/request/friend",{'to_user_id': id}, content_type="application/json", **headers)
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.json()['info'], 'Friend request already sent')
        self.assertEqual(response2.json()['code'], 4)

    # already friends
    def test_send_friend_request_already_friends(self):
        username_to = 'test_handle_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_to, "password": password}, content_type="application/json")
        username_from = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_from, "password": password}, content_type="application/json")
        id = User.objects.get(name=username_to).id
        id_from = User.objects.get(name=username_from).id
        headers_from = self.generate_header(username_from)
        response1 = self.client.post("/friends/request/friend",{'to_user_id': id}, content_type="application/json", **headers_from)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['msg'], 'Friend request sent successfully.')
        self.assertEqual(response1.json()['code'], 0)
        headers_to = self.generate_header(username_to)
        response2 = self.client.get("/friends/require/friend", content_type="application/json", **headers_to)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(id_from, response2.json()['requests'][0]['from_user_id'])
        request_id = response2.json()['requests'][0]['id']
        response3 = self.client.post("/friends/request/friend/handle",{'request_id': request_id, 'action': 'accept'}, content_type="application/json", **headers_to)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()['message'], 'Friend request accepted.')
        self.assertEqual(response3.json()['code'], 0)
        response4 = self.client.post("/friends/request/friend",{'to_user_id': id}, content_type="application/json", **headers_from)
        self.assertEqual(response4.status_code, 400)
        self.assertEqual(response4.json()['info'], 'The user is already your friend')
        self.assertEqual(response4.json()['code'], 6)
    # * Tests for /require/friend
    # + normal case [GET]
    def test_get_friend_requests_normal(self):
        username_to = 'test_get_friend_requests'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_to, "password": password}, content_type="application/json")
        username_from = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_from, "password": password}, content_type="application/json")
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

    # + no token
    def test_get_friend_requests_no_token(self):
        response = self.client.get("/friends/require/friend", content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)
    
    # + no username
    def test_get_friend_requests_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.get("/friends/require/friend", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)

    # * Tests for /request/friend/handle
    # + normal case [POST]
    def test_handle_friend_request_normal_accepted(self):
        username_to = 'test_handle_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_to, "password": password}, content_type="application/json")
        username_from = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_from, "password": password}, content_type="application/json")
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

    def test_handle_friend_request_normal_rejected(self):
        username_to = 'test_handle_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_to, "password": password}, content_type="application/json")
        username_from = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_from, "password": password}, content_type="application/json")
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
        response3 = self.client.post("/friends/request/friend/handle",{'request_id': request_id, 'action': 'reject'}, content_type="application/json", **headers)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()['message'], 'Friend request rejected.')
        self.assertEqual(response3.json()['code'], 0)
    
    # + no token
    def test_handle_friend_request_no_token(self):
        response = self.client.post("/friends/request/friend/handle",{'request_id': 7, 'action': 'accept'}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_handle_friend_request_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.post("/friends/request/friend/handle",{'request_id': 7, 'action': 'accept'}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)

    # + invalid action
    def test_handle_friend_request_invalid_action(self):
        username_to = 'test_handle_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_to, "password": password}, content_type="application/json")
        username_from = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_from, "password": password}, content_type="application/json")
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
        response3 = self.client.post("/friends/request/friend/handle",{'request_id': request_id, 'action': 'invalid'}, content_type="application/json", **headers)
        self.assertEqual(response3.status_code, 400)
        self.assertEqual(response3.json()['info'], 'Invalid action.')
        self.assertEqual(response3.json()['code'], 4)


    # * Tests for /delete/friend
    # + normal case [POST]
    def test_delete_friend_normal(self):
        username_to = 'test_handle_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_to, "password": password}, content_type="application/json")
        username_from = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_from, "password": password}, content_type="application/json")
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
        headers = self.generate_header(username_from)
        response4 = self.client.delete("/friends/delete/friend",{'to_user': username_to}, content_type="application/json", **headers)
        self.assertEqual(response4.status_code, 200)
        self.assertEqual(response4.json()['message'], 'Friendship updated successfully')
        self.assertEqual(response3.json()['code'], 0)

    # + no token
    def test_delete_friend_no_token(self):
        response = self.client.delete("/friends/delete/friend",{'to_user': 'test'}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_delete_friend_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.delete("/friends/delete/friend",{'to_user': 'test'}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)
    
    # * Tests for /friend/list_all
    # + normal case [GET]
    def test_get_all_friends_normal(self):
        username_to = 'test_handle_friend_request'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_to, "password": password}, content_type="application/json")
        username_from = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username_from, "password": password}, content_type="application/json")
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
        headers = self.generate_header(username_to)
        response4 = self.client.get("/friends/friend/list_all", content_type="application/json", **headers)
        self.assertEqual(response4.status_code, 200)
        self.assertEqual(len(response4.json()['members']), 2)
    
    # + no token
    def test_get_all_friends_no_token(self):
        response = self.client.get("/friends/friend/list_all", content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 4)

    # + no username
    def test_get_all_friends_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.get("/friends/friend/list_all", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 4)

    # * Tests for /friend/group/create
    # + normal case [POST]
    def test_create_group_normal(self):
        username = 'test_create_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Group created successfully')
        self.assertEqual(response.json()['code'], 0)
    
    # + no token
    def test_create_group_no_token(self):
        response = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_create_group_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)

    # + no group name
    def test_create_group_no_group_name(self):
        username = 'test_create_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response = self.client.post("/friends/friend/group/create", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Group name is required')
        self.assertEqual(response.json()['code'], 4)

    # + group name already exists
    def test_create_group_group_name_exists(self):
        username = 'test_create_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['message'], 'Group created successfully')
        self.assertEqual(response1.json()['code'], 0)
        response2 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.json()['info'], 'A group with the same name already exists')
        self.assertEqual(response2.json()['code'], 6)

    # * Tests for /friend/group/move
    # + normal case [POST]
    def test_add_user_to_group_normal(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        username2 = 'test_add_user_to_group2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        headers = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response1.json()['code'], 0)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['message'], 'Group created successfully')
        
        # 添加好友
        self.add_friends(username, username2)
        group_name = Group.objects.get(name='test_group').name
        user_id = User.objects.get(name=username2).id
        response2 = self.client.post("/friends/friend/group/move",{'group_name': group_name, 'user_id': user_id }, content_type="application/json", **headers)
        self.assertEqual(response2.json()['code'], 0)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()['message'], 'User successfully moved to the new group')
        

    # + no token
    def test_add_user_to_group_no_token(self):
        response = self.client.post("/friends/friend/group/move",{'group_id': 1, 'user_id': 1}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_add_user_to_group_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.post("/friends/friend/group/move",{'group_id': 1, 'user_id': 1}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)

    # + no group id
    def test_add_user_to_group_no_group_id(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response = self.client.post("/friends/friend/group/move",{'user_id': 1}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'group id is required')
        self.assertEqual(response.json()['code'], 4)

    # + no user id
    def test_add_user_to_group_no_user_id(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response = self.client.post("/friends/friend/group/move",{'group_id': 1}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'user id is required')
        self.assertEqual(response.json()['code'], 4)

    # * Tests for /friends/groups
    # + normal case [GET]
    def test_get_all_groups_normal(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response = self.client.get("/friends/friends/groups", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['groups']), 1)
        username2 = 'test_add_user_to_group2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        headers = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['message'], 'Group created successfully')
        self.assertEqual(response1.json()['code'], 0)
        self.add_friends(username, username2)
        group_name = Group.objects.get(name='test_group').name
        user_id = User.objects.get(name=username2).id
        response2 = self.client.post("/friends/friend/group/move",{'group_name': group_name, 'user_id': user_id }, content_type="application/json", **headers)
        self.assertEqual(response2.json()['code'], 0)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()['message'], 'User successfully moved to the new group')
        
        response3 = self.client.get("/friends/friends/groups", content_type="application/json", **headers)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(len(response3.json()['groups']), 2)

    # + no token
    def test_get_all_groups_no_token(self):
        response = self.client.get("/friends/friends/groups", content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_get_all_groups_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.get("/friends/friends/groups", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 2)

    # * Tests for /friend/list_group
    # + normal case [GET]
    def test_get_all_friends_in_group_normal(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        username2 = 'test_add_user_to_group2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        self.add_friends(username, username2)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['message'], 'Group created successfully')
        self.assertEqual(response1.json()['code'], 0)
        group_name = Group.objects.get(name='test_group').name
        user_id = User.objects.get(name=username2).id
        response2 = self.client.get("/friends/friend/list_group",{'group': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(len(response2.json()['members']), 0)
        self.assertEqual(response2.status_code, 200)
        response3 = self.client.post("/friends/friend/group/move",{'group_name': group_name, 'user_id': user_id }, content_type="application/json", **headers)
        self.assertEqual(response3.json()['code'], 0)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()['message'], 'User successfully moved to the new group')
        response4 = self.client.get("/friends/friend/list_group",{'group': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response4.status_code, 200)
        self.assertEqual(len(response4.json()['members']), 1)

    # + no token
    def test_get_all_friends_in_group_no_token(self):
        response = self.client.get("/friends/friend/list_group",{'group': 'test_group'}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 4)

    # + no username
    def test_get_all_friends_in_group_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.get("/friends/friend/list_group",{'group': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 4)

    # + no group name
    def test_get_all_friends_in_group_no_group_name(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response = self.client.get("/friends/friend/list_group", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Group name is required')
        self.assertEqual(response.json()['code'], 3)

    # + user not exist
    def test_get_all_friends_in_group_user_not_exist(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header('UserNotExist')
        response = self.client.get("/friends/friend/list_group",{'group': 'test_group'}, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'User not found')

    # # Tests for /get/all/ingroup
    # + normal case [GET]
    def test_get_all_users_in_group_normal(self):
        username = 'test_add_user_to_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        headers = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **headers)
        username2 = 'test_add_user_to_group2'
        password2 = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username2, "password": password2}, content_type="application/json")
        self.add_friends(username, username2)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['message'], 'Group created successfully')
        self.assertEqual(response1.json()['code'], 0)
        group_name = Group.objects.get(name='test_group').name
        user_id = User.objects.get(name=username2).id
        response3 = self.client.post("/friends/friend/group/move",{'group_name': group_name, 'user_id': user_id }, content_type="application/json", **headers)
        self.assertEqual(response3.json()['code'], 0)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()['message'], 'User successfully moved to the new group')
        response2 = self.client.get('/friends/get/all/ingroup', data={'group_name': 'test_group'}, content_type='application/json', **headers)
        self.assertEqual(response2.json()['code'], 0)
        self.assertEqual(len(response2.json()['members']), 1)

    # + no token
    def test_get_all_users_in_group_no_token(self):
        response = self.client.get('/friends/get/all/ingroup', data={'group_name': 'test_group'}, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 1)

    # + no username
    def test_get_all_users_in_group_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.get('/friends/get/all/ingroup', data={'group_name': 'test_group'}, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 2)

    # + no group name
    def test_get_all_users_in_group_no_group_name(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.get('/friends/get/all/ingroup', content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Group name is required')
        self.assertEqual(response.json()['code'], 3)

    # + group not exist
    def test_get_all_users_in_group_group_not_exist(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.get('/friends/get/all/ingroup', data={'group_name': 'test_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'Group not found')
        self.assertEqual(response.json()['code'], 4)

    # # Tests for /rename/group
    def test_rename_group_normal(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **header)
        response2 = self.client.put('/friends/rename/group', data={'old_name': 'test_group','new_name': 'new_group'}, content_type='application/json', **header)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()['message'], 'Group renamed successfully')
        self.assertEqual(response2.json()['code'], 0)

    # + no token
    def test_rename_group_no_token(self):
        response = self.client.put('/friends/rename/group', data={'old_name': 'test_group', 'new_name': 'new_group'}, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 1)

    # + no username
    def test_rename_group_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.put('/friends/rename/group', data={'old_name': 'test_group', 'new_name': 'new_group'}, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 2)

    # + user not found
    def test_rename_group_user_not_found(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header('UserNotExist')
        response = self.client.put('/friends/rename/group', data={'old_name': 'test_group', 'new_name': 'new_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'User not found')
        self.assertEqual(response.json()['code'], 4)

    # + missing old name
    def test_rename_group_missing_old_name(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.put('/friends/rename/group', data={'new_name': 'new_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Missing old_name')
        self.assertEqual(response.json()['code'], 6)

    # + missing new name
    def test_rename_group_missing_new_name(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.put('/friends/rename/group', data={'old_name': 'test_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Missing new_name')
        self.assertEqual(response.json()['code'], 7)

    # + old name is 'My friends'
    def test_rename_group_old_name_my_friends(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.put('/friends/rename/group', data={'group_name': 'My friends', 'old_name': 'My friends', 'new_name': 'new_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Cannot rename "My friends" group')
        self.assertEqual(response.json()['code'], 8)

    # + new name and old name are the same
    def test_rename_group_same_name(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.put('/friends/rename/group', data={'old_name': 'test_group', 'new_name': 'test_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'New name must be different from old name')
        self.assertEqual(response.json()['code'], 9)

    # + new name already exists
    def test_rename_group_new_name_exists(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'new_group'}, content_type="application/json", **header)
        response2 = self.client.put('/friends/rename/group', data={'old_name': 'test_group', 'new_name': 'new_group'}, content_type='application/json', **header)
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.json()['info'], 'Group with new_name already exists')
        self.assertEqual(response2.json()['code'], 10)

    # group in old name not found
    def test_rename_group_group_not_found(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.put('/friends/rename/group', data={'old_name': 'test_group', 'new_name': 'new_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'Group with old_name not found')
        self.assertEqual(response.json()['code'], 11)

    # # Tests for /remove/group
    # + normal case [DELETE]
    def test_remove_group_normal(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response1 = self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **header)
        response2 = self.client.delete('/friends/remove/group', data={'group_name': 'test_group'}, content_type='application/json', **header)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()['message'], 'Group deleted successfully')
        self.assertEqual(response2.json()['code'], 0)
        num = Group.objects.filter(name='test_group').count()
        self.assertEqual(num, 0)

    # + no token
    def test_remove_group_no_token(self):
        response = self.client.delete('/friends/remove/group', data={'group_name': 'test_group'}, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)

    # + no username
    def test_remove_group_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.delete('/friends/remove/group', data={'group_name': 'test_group'}, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)

    # + user not found
    def test_remove_group_user_not_found(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header('UserNotExist')
        response = self.client.delete('/friends/remove/group', data={'group_name': 'test_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'User not found')
        self.assertEqual(response.json()['code'], 4)

    # + missing group name
    def test_remove_group_missing_group_name(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.delete('/friends/remove/group', data={}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Group name is required')
        self.assertEqual(response.json()['code'], 6)

    # + group name is "My friends"
    def test_remove_group_my_friends(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.delete('/friends/remove/group', data={'group_name': 'My friends'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['info'], 'Cannot delete "My friends" group')
        self.assertEqual(response.json()['code'], 7)

    # + group not found
    def test_remove_group_group_not_found(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.delete('/friends/remove/group', data={'group_name': 'test_group'}, content_type='application/json', **header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['info'], 'Group not found')
        self.assertEqual(response.json()['code'], 8)

    # # Tests for /get/position
    # + normal case [GET]
    def test_get_position_normal(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        username = 'test_group2'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        self.add_friends('test_group', 'test_group2')
        self.client.post("/friends/friend/group/create",{'group_name': 'test_group'}, content_type="application/json", **header)
        user2_id = User.objects.get(name='test_group2').id
        self.client.post("/friends/friend/group/move",{'group_name': 'test_group', 'user_id':user2_id}, content_type="application/json", **header)
        response = self.client.get('/friends/get/position', data={"member_user_id": user2_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['group'], 'test_group')

    # + no token
    def test_get_position_no_token(self):
        response = self.client.get('/friends/get/position', data={"member_user_id": 1}, content_type='application/json')
        self.assertEqual(response.json()['info'], 'Authorization token is missing')
        self.assertEqual(response.json()['code'], 2)
    
    # + no username
    def test_get_position_no_username(self):
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        response = self.client.get('/friends/get/position', data={"member_user_id": 1}, content_type='application/json', **headers)
        self.assertEqual(response.json()['info'], 'Invalid token')
        self.assertEqual(response.json()['code'], 3)

    # + user not found
    def test_get_position_user_not_found(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header('UserNotExist')
        response = self.client.get('/friends/get/position', data={"member_user_id": 1}, content_type='application/json', **header)
        self.assertEqual(response.json()['info'], 'User not found')
        self.assertEqual(response.json()['code'], 4)

    # + no member user id
    def test_get_position_no_member_user_id(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        response = self.client.get('/friends/get/position', data={}, content_type='application/json', **header)
        self.assertEqual(response.json()['info'], 'User ID is required')
        self.assertEqual(response.json()['code'], 5)

    # + no group matching the member
    def test_get_position_no_group_matching_member(self):
        username = 'test_group'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        header = self.generate_header(username)
        username = 'test_group2'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
        user2_id = User.objects.get(name='test_group2').id
        response = self.client.get('/friends/get/position', data={"member_user_id": user2_id}, content_type='application/json', **header)
        self.assertEqual(response.json()['info'], 'No groups found for the specified user under this owner')
        self.assertEqual(response.json()['code'], 7)
