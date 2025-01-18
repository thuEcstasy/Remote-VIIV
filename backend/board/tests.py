import random
from django.test import TestCase, Client
from board.models import User, Board
import datetime
import hashlib
import hmac
import time
import json
import base64

from utils.utils_jwt import EXPIRE_IN_SECONDS, SALT, b64url_encode

# Create your tests here.
class BoardTests(TestCase):
    # Initializer
    def setUp(self):
        holder = User.objects.create(name="Ashitemaru", password="123456")
        Board.objects.create(user=holder, board_state="1"*2500, board_name="Ashitemaru's board")
        
    # ! Utility functions
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

    def post_board(self, board_state, board_name, user_name, headers):
        payload = {
            "board": board_state,
            "boardName": board_name,
            "userName": user_name
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/boards", data=payload, content_type="application/json", **headers)

    def get_board_index(self, index):
        return self.client.get(f"/boards/{index}")
    
    def delete_board_index(self, index, headers):
        return self.client.delete(f"/boards/{index}", **headers)


    # ! Test section
    # * Tests for login view
    def test_login_existing_user_correct_password(self):
        data = {"userName": "Ashitemaru", "password": "123456"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertTrue(res.json()['token'].count('.') == 2)

    def test_login_existing_user_wrong_password(self):
        data = {"userName": "Ashitemaru", "password": "wrongpassword"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)

    def test_login_new_user(self):
        data = {"userName": "NewUser", "password": "123456"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertTrue(res.json()['token'].count('.') == 2)
        self.assertTrue(User.objects.filter(name="NewUser").exists())
    
    
    # * Tests for board
    # normal case [GET]
    def test_boards_get(self):
        random.seed(9)
        res = self.client.get("/boards")
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 200)
    
    def test_boards_post_new(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header(user_name)
        res = self.post_board(board_state, board_name, user_name, headers)

        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {"code": 0, "info": "Succeed", "isCreate": True})
        self.assertTrue(User.objects.filter(name=user_name).exists())
        self.assertTrue(Board.objects.filter(board_name=board_name, board_state=board_state).exists())
        
    def test_boards_post_new_twice_samename(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_state2 = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header("Ashitemaru")
        res = self.post_board(board_state, board_name, user_name, headers)
        res = self.post_board(board_state2, board_name, user_name, headers)
        
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {"code": 0, "info": "Succeed", "isCreate": False})
        self.assertTrue(User.objects.filter(name=user_name).exists())
        self.assertFalse(Board.objects.filter(board_name=board_name, board_state=board_state).exists())
        self.assertTrue(Board.objects.filter(board_name=board_name, board_state=board_state2).exists())

    def test_boards_post_invalid_jwt(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = {"Authorization": "Invalid JWT"}
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)
    
    def test_boards_post_missing_jwt(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = {}
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)

    def test_boards_post_expired_jwt(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        payload = {
            "iat": int(time.time()) - EXPIRE_IN_SECONDS * 2,
            "exp": int(time.time()) - EXPIRE_IN_SECONDS,
            "data": {
                "username": user_name
            }
        }
        
        headers = self.generate_header(user_name, payload)
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)
    
    def test_boards_post_invalid_salt(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header(user_name, {}, "AnotherSalt".encode('utf-8'))
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)

    def test_boards_post_not_same_user(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "c7w"
        
        headers = self.generate_header("Ashitemaru")
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()['code'], 3)
    
    # `board` key missing
    def test_add_board_without_board(self):
        random.seed(2)
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header("Ashitemaru")
        res = self.post_board(None, board_name, user_name, headers)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(Board.objects.filter(board_name=board_name).exists())
    
    
    # + board key length incorrect
    def test_add_board_state_length_incorrect(self):
        length = random.randint(0, 2499)
        
        board_state = ''.join([random.choice("01") for _ in range(length)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header("Ashitemaru")
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(Board.objects.filter(board_name=board_name).exists())
    
    
    # + board with invalid char
    def test_add_board_state_invalid_char(self):
        board_state = ''.join([random.choice("0123") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header("Ashitemaru")
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(Board.objects.filter(board_name=board_name).exists())
        
        board_state = ''.join(random.choice("01中文测试") for _ in range(2500))
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        res = self.post_board(board_state, board_name, user_name, headers)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(Board.objects.filter(board_name=board_name).exists())
        
        
    # + boardName key missing
    def test_add_board_without_board_name(self):
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header("Ashitemaru")
        res = self.post_board(board_state, None, user_name, headers)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(Board.objects.filter(board_state=board_state).exists())


    # + boardName key length incorrect
    def test_add_board_boardname_length(self):
        random.seed(6)
        for length in [0, 51, 255]:
            board_state = ''.join([random.choice("01") for _ in range(2500)])
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(length)])
            user_name = "Ashitemaru"
            
            headers = self.generate_header("Ashitemaru")
            res = self.post_board(board_state, board_name, user_name, headers)
            
            self.assertNotEqual(res.json()['code'], 0)
            self.assertNotEqual(res.status_code, 200)
            self.assertFalse(Board.objects.filter(board_state=board_state).exists())


    # + userName key missing
    def test_add_board_username_missing(self):
        random.seed(7)
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = "Ashitemaru"
        
        headers = self.generate_header("Ashitemaru")
        res = self.post_board(board_state, board_name, None, headers)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(Board.objects.filter(board_state=board_state).exists())
        
    # + unsupported method
    def test_delete_boards(self):
        res = self.client.delete("/boards")
        self.assertEqual(res.json()['code'], -3)
        self.assertEqual(res.status_code, 405)
    
    
    # * Tests for /boards/<index>
    # GET
    # + normal case
    def test_boards_index_get(self):
        index = 1
        res = self.get_board_index(index)
        self.assertEqual(res.json()['code'] , 0)
        self.assertJSONEqual(res.content, {'code': 0, 'info': 'Succeed', 'board': '1'*2500, 'boardName': "Ashitemaru's board", 'userName': 'Ashitemaru'})
        self.assertEqual(res.status_code, 200)
    
    # + index not int
    def test_boards_index_get_idx(self):
        index = "aaa"
        res = self.get_board_index(index)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)

    # + do not exist
    def test_boards_index_get_do_not_exist(self):
        index = 2
        res = self.get_board_index(index)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 404)

    # DELETE
    # + normal case
    def test_boards_index_delete_do_not_exist(self):
        index = 1
        headers = self.generate_header("Ashitemaru")
        res = self.delete_board_index(index, headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(Board.objects.all()), 0)
        
    # + index not int
    def test_boards_index_delete_do_not_exist2(self):
        index = "aaa"
        headers = self.generate_header("Ashitemaru")
        res = self.delete_board_index(index, headers)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        
    # + do not exist
    def test_boards_index_delete_do_not_exist3(self):
        index = 2
        headers = self.generate_header("Ashitemaru")
        res = self.delete_board_index(index, headers)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 404)
    
    # + not authorized
    def test_boards_index_delete_not_owner(self):
        new_user = User.objects.create(name="aaaa", password="aaaa")
        board = Board.objects.create(board_state="1"*2500, board_name="aaaa's board", user=new_user)
        
        headers = self.generate_header("Ashitemaru")
        res = self.delete_board_index(board.id, headers)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 403)


    # + unsupported method
    def test_boards_index_unsupported(self):
        index = 1
        
        res = self.client.post(f"/boards/{index}")
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        
        res = self.client.put(f"/boards/{index}")
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)


    ### Testcases for user_board
    def test_user_board(self):
        res = self.client.get(f"/user/Ashitemaru")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.json()['boards']), 0)
        self.assertFalse("board" in res.json()['boards'][0])

    def test_user_board_not_exist(self):
        res = self.client.get(f"/user/aaaa")
        self.assertEqual(res.status_code, 404)
    
    def test_user_board_method_not_allowed(self):
        res = self.client.post(f"/user/Ashitemaru")
        self.assertNotEqual(res.status_code, 200)
        res = self.client.put(f"/user/Ashitemaru")
        self.assertNotEqual(res.status_code, 200)
        res = self.client.delete(f"/user/Ashitemaru")
        self.assertNotEqual(res.status_code, 200)
