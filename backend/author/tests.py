import random
from django.test import TestCase, Client, RequestFactory
from utils.utils_require import require
from author.models import User, EmailVerification,PhoneVerification
import datetime
import hashlib
import hmac
import time
import json
import base64

from utils.utils_jwt import EXPIRE_IN_SECONDS, SALT, b64url_encode
from .views import *

# Create your tests here.
class AuthorTests(TestCase):
    # Initializer
    def setUp(self):
        holder = User.objects.create(name="Ashitemaru", password="123456")
        self.factory = RequestFactory()
        
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
    

    # * author
    def post_login(self, username, password):
        return self.client.post("/author/login", data={"userName": username, "password": password}, content_type="application/json")
    def post_register(self, username, password):
        return self.client.post("/author/register", data={"userName": username, "password": password}, content_type="application/json")
    def delete_delete(self, password, header):
        return self.client.delete("/author/delete", data={"password": password}, content_type="application/json",**header)
    def post_avatar_update(self, path, header):
        with open(path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        return self.client.post("/author/avatar/update", data={"avatar": base64_image}, content_type="application/json",**header)
    def post_bind_email(self, email, header):
        return self.client.post("/author/email/verification/send", data={"email": email}, content_type="application/json",**header)
    def post_verify_email(self, email, code, header):
        return self.client.post("/author/email/verification/verify", data={"email": email, "code": code}, content_type="application/json",**header)
    def post_bind_phone_number(self, phone, header):
        return self.client.post("/author/number/verification/send", data={"number": phone}, content_type="application/json",**header)
    def post_verify_phone_number(self, phone, code, header):
        return self.client.post("/author/number/verification/verify", data={"number": phone, "code": code}, content_type="application/json",**header)
    # ! Test section
    # * Tests for /register
        
    # + normal case [POST]
        
    def test_register_normal(self):

        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        res = self.post_register(username, password)
        self.assertEqual(res.json()['code'], 0)
    
        self.assertEqual(res.status_code, 200)

    # + unsupported method
        
    def test_register_unsupported(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        res = self.client.delete("/author/register", data={"username": username, "password": password}, content_type="application/json")
        self.assertEqual(res.json()['code'], -3)
        self.assertEqual(res.status_code, 405)
    
    # + incorrect username: ' '(space) in username

    def test_register_incorrect_username(self):
        username = 'SpaceIn Username'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        res = self.post_register(username, password)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.status_code, 400)

    # + incorrect password: len < 8 or ' '(space) in password

    def test_register_incorrect_password(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = '7letter'
        res = self.post_register(username, password)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.status_code, 400)

        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = 'SpaceIn Password'
        res = self.post_register(username, password)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.status_code, 400)

    # + username already exist       
         
    def test_register_username_exist(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        res = self.post_register(username, password)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 200)
        password = 'UsernameAlreadyExist'
        res = self.post_register(username, password)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.status_code, 401)

    # * Tests for /login
        
    # + normal case [POST]
        
    def test_login_normal(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        res = self.post_login(username, password)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 200)

    # + unsupported method
        
    def test_login_unsupported(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        res = self.client.delete("/author/login", data={"username": username, "password": password}, content_type="application/json")
        self.assertEqual(res.json()['code'], -3)
        self.assertEqual(res.status_code, 405)

    # + wrong password
        
    def test_login_wrong_password(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        password = 'WrongPassword'
        res = self.post_login(username, password)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.status_code, 401)

    # + username not exist    
    
    def test_login_username_not_exist(self):
        username = 'UsernameNotExist'
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        res = self.post_login(username, password)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.status_code, 401)
    
    # # Tests for /delete
    # + normal case [DELETE]

    def test_delete_normal(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.delete_delete(password, headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['msg'], "User successfully deleted")

    # + unsupported method
    def test_delete_unsupported(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.post("/author/delete", data={"password": password}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Bad request method')

    # + missing token
    def test_delete_missing_token(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = {}
        res = self.delete_delete(password, headers)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Authorization token is missing')
    
    # + invalid token
    def test_delete_invalid_token(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        res = self.delete_delete(password, headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Invalid token')
    
    # + json decode error
    def test_delete_json_decode_error(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.delete("/author/delete", data='Invalid Data', content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Invalid request body')

    # + missing password
    def test_delete_missing_password(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.delete_delete('', headers)
        self.assertEqual(res.json()['code'], 5)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Password is required')

    # + user not exist
    def test_delete_user_not_exist(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header('UserNotExist')
        res = self.delete_delete(password, headers)
        self.assertEqual(res.json()['code'], 6)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['info'],'User not found')

    # + wrong password
    def test_delete_wrong_password(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.delete_delete('WrongPassword', headers)
        self.assertEqual(res.json()['code'], 7)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Password is incorrect')
    
    # # Tests for /avatar/update
    # + normal case [POST]
    def test_update_avatar_normal(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.post_avatar_update('author/avatar.png', headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['msg'],"Your avatar successfully changes")

    # + unsupported method
    def test_update_avatar_unsupported(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        with open('author/avatar.png', 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        res = self.client.delete("/author/avatar/update", data={"avatar": base64_image}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Invalid request')

    # + missing token
    def test_update_avatar_missing_token(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = {}
        res = self.post_avatar_update('author/avatar.png', headers)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Authorization token is missing')

    # + missing username
    def test_update_avatar_missing_username(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        res = self.post_avatar_update('author/avatar.png', headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Invalid token')

    # + missing avatar
    def test_update_avatar_missing_avatar(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.post("/author/avatar/update", data={}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Avatar is missing')

    # + user not exist
    def test_update_avatar_user_not_exist(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header('UserNotExist')
        res = self.post_avatar_update('author/avatar.png', headers)
        self.assertEqual(res.json()['code'], 5)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['info'],'User not found')

    # # Tests for /change/name
    # + normal case [POST]
    def test_change_name_normal(self):
        username = 'testNameChange1'
        password = '123456789'
        self.post_register(username, password)
        user_id = User.objects.filter(name=username).values('id').first().get('id')
        headers = self.generate_header(username)
        new_name = 'newName1'
        res = self.client.post("/author/change/name", data={"new_name": new_name}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['msg'],'Your userName successfully changes')
        self.assertEqual(User.objects.filter(id=user_id).values('name').first().get('name'), new_name)


    # + unsupported method
    def test_change_name_unsupported(self):
        username = 'testNameChange2'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        new_name = 'newName2'
        res = self.client.delete("/author/change/name", data={"new_name": new_name}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.json()['info'], 'Invalid request')
        
    # + missing token
    def test_change_name_missing_token(self):
        username = 'testNameChange3'
        password = '123456789'
        self.post_register(username, password)
        headers = {}
        new_name = 'newName3'
        res = self.client.post("/author/change/name", data={"new_name": new_name}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.json()['info'], 'Authorization token is missing')

    # + missing username
    def test_change_name_missing_username(self):
        username = 'testNameChange4'
        password = '123456789'
        self.post_register(username, password)
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        new_name = 'newName4'
        res = self.client.post("/author/change/name", data={"new_name": new_name}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.json()['info'], 'Invalid token')

    # + user not found
    def test_change_name_user_not_found(self):
        username = 'testNameChange5'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header('UserNotExist')
        new_name = 'newName5'
        res = self.client.post("/author/change/name", data={"new_name": new_name}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.json()['info'], 'User not found')

    # + new name contain spaces
    def test_change_name_new_name_contain_spaces(self):
        username = 'testNameChange6'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        new_name = 'new Name6'
        res = self.client.post("/author/change/name", data={"new_name": new_name}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 5)
        self.assertEqual(res.json()['info'], 'Username should not contain spaces')

    # + new name already exist
    def test_change_name_new_name_already_exist(self):
        username = 'testNameChange7'
        password = '123456789'
        self.post_register(username, password)
        self.post_register('newName7', password)
        headers = self.generate_header(username)
        new_name = 'newName7'
        res = self.client.post("/author/change/name", data={"new_name": new_name}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 6)
        self.assertEqual(res.json()['info'], 'User already exists')

    # # Tests for /change/password
    # + normal case [POST]
    def test_change_password_normal(self):
        username = 'testPasswordChange1'
        password = '123456789'
        self.post_register(username, password)
        user_id = User.objects.filter(name=username).values('id').first().get('id')
        headers = self.generate_header(username)
        newPassword = '987654321'
        res = self.client.post("/author/change/password", data={"old_password": password, "new_password": newPassword}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['msg'],'Your password successfully changes')

    # + unsupported method
    def test_change_password_unsupported(self):
        username = 'testPasswordChange2'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        newPassword = '987654321'
        res = self.client.delete("/author/change/password", data={"old_password": password, "new_password": newPassword}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.json()['info'], 'Invalid request')

    # + missing token
    def test_change_password_missing_token(self):
        username = 'testPasswordChange3'
        password = '123456789'
        self.post_register(username, password)
        headers = {}
        newPassword = '987654321'
        res = self.client.post("/author/change/password", data={"old_password": password, "new_password": newPassword}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.json()['info'], 'Authorization token is missing')

    # + missing username
    def test_change_password_missing_username(self):
        username = 'testPasswordChange4'
        password = '123456789'
        self.post_register(username, password)
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        newPassword = '987654321'
        res = self.client.post("/author/change/password", data={"old_password": password, "new_password": newPassword}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.json()['info'], 'Invalid token')

    # + user not exist
    def test_change_password_user_not_exist(self):
        username = 'testPasswordChange5'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header('UserNotExist')
        newPassword = '987654321'
        res = self.client.post("/author/change/password", data={"old_password": password, "new_password": newPassword}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 5)
        self.assertEqual(res.json()['info'], 'User not found')

    # + Invalid new password
    def test_change_password_invalid_new_password(self):
        username = 'testPasswordChange6'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        newPassword = '123456'
        res = self.client.post("/author/change/password", data={"old_password": password, "new_password": newPassword}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 6)
        self.assertEqual(res.json()['info'], 'Password must be at least 8 characters long and not contain spaces')

    # + wrong old password
    def test_change_password_wrong_old_password(self):
        username = 'testPasswordChange7'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        newPassword = '987654321'
        res = self.client.post("/author/change/password", data={"old_password": '111111111', "new_password": newPassword}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 7)
        self.assertEqual(res.json()['info'], 'Old password is incorrect')
    # # Tests for /email/verification/send
    # + normal case [POST]

    def test_bind_email_normal(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        res = self.post_bind_email(email, headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['msg'],'Verification code sent successfully')

    # + unsupported method
    def test_bind_email_unsupported(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        res = self.client.delete("/author/email/verification/send", data={"email": email}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Invalid request')

    # + missing token
    def test_bind_email_missing_token(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = {}
        email = '2321404500@qq.com'
        res = self.post_bind_email(email, headers)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Authorization token is missing')

    # + missing username
    def test_bind_email_missing_username(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        email = '2321404500@qq.com'
        res = self.post_bind_email(email, headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Invalid token')

    # + missing email
    def test_bind_email_missing_email(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.post("/author/email/verification/send", data={'email': ''}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Email is missing')

    # + email invalid
    def test_bind_email_email_invalid(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500'
        res = self.post_bind_email(email, headers)
        self.assertEqual(res.json()['code'], 8)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Email is invalid')

    # + email is already your's
    def test_bind_email_email_already_yours(self):
        username = 'testBindEmail1'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email, headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()

        # 如果存在验证码字典，则获取其值并转换为字符串形式
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            # 如果验证码字典为空或者不存在验证码字段，则将值设置为 None 或者其他默认值
            verification_code_str = None  # 或者其他默认值
        self.post_verify_email(email, verification_code_str, headers)
        res = self.post_bind_email(email, headers)
        self.assertEqual(res.json()['code'], 6)
        self.assertEqual(res.json()['info'], 'This email is already yours')

    # + email is already binded
    def test_bind_email_email_already_binded(self):
        username = 'testBindEmail2'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email, headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()

        # 如果存在验证码字典，则获取其值并转换为字符串形式
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            # 如果验证码字典为空或者不存在验证码字段，则将值设置为 None 或者其他默认值
            verification_code_str = None  # 或者其他默认值
        self.post_verify_email(email, verification_code_str, headers)
        username = 'testBindEmail3'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.post_bind_email(email, headers)
        self.assertEqual(res.json()['code'], 7)
        self.assertEqual(res.json()['info'], 'This email is already bound')
    # # Tests for /email/verification/verify
    # + normal case [POST]
    def test_verify_email_normal(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email, headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()

        # 如果存在验证码字典，则获取其值并转换为字符串形式
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            # 如果验证码字典为空或者不存在验证码字段，则将值设置为 None 或者其他默认值
            verification_code_str = None  # 或者其他默认值

        res = self.post_verify_email(email, verification_code_str, headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['msg'],'Your email successfully changes')

    # + unsupported method
    def test_verify_email_unsupported(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email, headers)
        res = self.client.delete("/author/email/verification/verify", data={"email": email,"code": '123456'}, content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Invalid request')

    # + missing token
    def test_verify_email_missing_token(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email,headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            verification_code_str = None 
        headers = {}
        res = self.post_verify_email(email, verification_code_str, headers)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Authorization token is missing')

    # + missing username
    def test_verify_email_missing_username(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers =self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email,headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            verification_code_str = None 
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        res = self.post_verify_email(email, verification_code_str, headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['info'],'Invalid token')

    # + missing email or usercode
    def test_verify_email_missing_email_or_usercode(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email,headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            verification_code_str = None
        res1 = self.post_verify_email(email, '', headers)
        self.assertEqual(res1.json()['code'], 4)
        self.assertEqual(res1.status_code, 400)
        self.assertEqual(res1.json()['info'],'Email and verification code are required')
        res2 = self.post_verify_email('', verification_code_str, headers)
        self.assertEqual(res2.json()['code'], 4)
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(res2.json()['info'],'Email and verification code are required')

    # wrong code
    def test_verify_email_wrong_code(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        self.post_register(username, password)
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email, headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()

        # 如果存在验证码字典，则获取其值并转换为字符串形式
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            # 如果验证码字典为空或者不存在验证码字段，则将值设置为 None 或者其他默认值
            verification_code_str = None  # 或者其他默认值

        res = self.post_verify_email(email, '000000', headers) # wrong code
        self.assertEqual(res.json()['code'], 5)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Invalid verification code or expired')

    # + user not exist
    def test_verify_email_user_not_exist(self):
        username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
        headers = self.generate_header(username)
        email = '2321404500@qq.com'
        self.post_bind_email(email, headers)
        verification_dict = EmailVerification.objects.filter(email=email).values('verification_code').first()

        # 如果存在验证码字典，则获取其值并转换为字符串形式
        if verification_dict:
            verification_code_str = str(verification_dict.get('verification_code'))
        else:
            # 如果验证码字典为空或者不存在验证码字段，则将值设置为 None 或者其他默认值
            verification_code_str = None  # 或者其他默认值
        res = self.post_verify_email(email, verification_code_str, headers)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['info'],'Email and verification code are required')

    
    # Tests for /number/verification/send
    # + normal case [POST]
    # def test_bind_phone_number_normal(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     phone = '19974345123'
    #     res = self.post_bind_phone_number(phone, headers)
    #     print(res.json())
    #     self.assertEqual(res.json()['code'], 0)
        
    #     self.assertEqual(res.json()['msg'],'Verification code sent successfully')

    # # + unsupported method
    # def test_bind_phone_number_unsupported(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     phone = '19974345123'
    #     res = self.client.delete("/author/number/verification/send", data={"number": phone}, content_type="application/json",**headers)
    #     self.assertEqual(res.json()['code'], 1)
    #     self.assertEqual(res.status_code, 400)
    #     self.assertEqual(res.json()['info'],'Invalid request')

    # # + missing token
    # def test_bind_phone_number_missing_token(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = {}
    #     phone = '19974345123'
    #     res = self.post_bind_phone_number(phone, headers)
    #     self.assertEqual(res.json()['code'], 2)
    #     self.assertEqual(res.status_code, 401)
    #     self.assertEqual(res.json()['info'],'Authorization token is missing')

    # # + missing username
    # def test_bind_phone_number_missing_username(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
    #     phone = '19974345123'
    #     res = self.post_bind_phone_number(phone, headers)
    #     self.assertEqual(res.json()['code'], 3)
    #     self.assertEqual(res.status_code, 401)
    #     self.assertEqual(res.json()['info'],'Invalid token')

    # # + incorrect phone number length
    # def test_bind_phone_number_incorrect_phone_number_length(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     phone = '123456789'
    #     res = self.post_bind_phone_number(phone, headers)
    #     self.assertEqual(res.json()['code'], 4)
    #     self.assertEqual(res.status_code, 400)
    #     self.assertEqual(res.json()['info'],'Phone number is invalid')

    # # # Tests for /number/verification/verify
    # # + normal case [POST]
    # def test_verify_phone_number_normal(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     number = '19974345123'
    #     self.post_bind_phone_number(number, headers)
    #     verification_dict = PhoneVerification.objects.filter(number=number).values('verification_code').first()
    #     if verification_dict:
    #         verification_code_str = str(verification_dict.get('verification_code'))
    #     else:
    #         verification_code_str = None
    #     res = self.post_verify_phone_number(number, verification_code_str, headers)
    #     self.assertEqual(res.json()['code'], 0)
    #     self.assertEqual(res.json()['msg'],'Your phone number successfully changes')

    # # + unsupported method
    # def test_verify_phone_number_unsupported(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     number = '19974345123'
    #     self.post_bind_phone_number(number, headers)
    #     verification_dict = PhoneVerification.objects.filter(number=number).values('verification_code').first()
    #     if verification_dict:
    #         verification_code_str = str(verification_dict.get('verification_code'))
    #     else:
    #         verification_code_str = None
    #     res = self.client.delete("/author/number/verification/verify", data={"number": number, "verification_code": verification_code_str}, content_type="application/json",**headers)
    #     self.assertEqual(res.json()['code'], 1)
    #     self.assertEqual(res.status_code, 400)
    #     self.assertEqual(res.json()['info'],'Invalid request')

    # # + missing token
    # def test_verify_phone_number_missing_token(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     number = '19974345123'
    #     self.post_bind_phone_number(number, headers)
    #     verification_dict = PhoneVerification.objects.filter(number=number).values('verification_code').first()
    #     if verification_dict:
    #         verification_code_str = str(verification_dict.get('verification_code'))
    #     else:
    #         verification_code_str = None  
    #     headers = {}
    #     res = self.post_verify_phone_number(number, verification_code_str, headers)
    #     self.assertEqual(res.json()['code'], 2)
    #     self.assertEqual(res.status_code, 401)
    #     self.assertEqual(res.json()['info'],'Authorization token is missing')

    # # + missing username
    # def test_verify_phone_number_missing_username(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     number = '19974345123'
    #     self.post_bind_phone_number(number, headers)
    #     verification_dict = PhoneVerification.objects.filter(number=number).values('verification_code').first()
    #     if verification_dict:
    #         verification_code_str = str(verification_dict.get('verification_code'))
    #     else:
    #         verification_code_str = None  
    #     headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
    #     res = self.post_verify_phone_number(number, verification_code_str, headers)
    #     self.assertEqual(res.json()['code'], 3)
    #     self.assertEqual(res.status_code, 401)
    #     self.assertEqual(res.json()['info'],'Invalid token')

    # # + missing number or code
    # def test_verify_phone_number_missing_number_or_code(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     number = '19974345123'
    #     self.post_bind_phone_number(number, headers)
    #     verification_dict = PhoneVerification.objects.filter(number=number).values('verification_code').first()
    #     if verification_dict:
    #         verification_code_str = str(verification_dict.get('verification_code'))
    #     else:
    #         verification_code_str = None  
    #     res1 = self.post_verify_phone_number(number, '', headers)
    #     self.assertEqual(res1.json()['code'], 4)
    #     self.assertEqual(res1.status_code, 400)
    #     self.assertEqual(res1.json()['info'],' and verification code are required')
        
    #     res2 = self.post_verify_phone_number('', verification_code_str, headers)
    #     self.assertEqual(res1.json()['code'], 4)
    #     self.assertEqual(res1.status_code, 400)
    #     self.assertEqual(res1.json()['info'],' and verification code are required')

    # # + wrong code
    # def test_verify_phone_number_wrong_code(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     self.post_register(username, password)
    #     headers = self.generate_header(username)
    #     number = '19974345123'
    #     self.post_bind_phone_number(number, headers)
    #     verification_dict = PhoneVerification.objects.filter(number=number).values('verification_code').first()
    #     if verification_dict:
    #         verification_code_str = str(verification_dict.get('verification_code'))
    #     else:
    #         verification_code_str = None
    #     res = self.post_verify_phone_number(number, 'wrongC', headers) # wrong code
    #     self.assertEqual(res.json()['code'], 5)
    #     self.assertEqual(res.status_code, 400)
    #     self.assertEqual(res.json()['info'],'Invalid verification code or expired')

    # # + user not exist
    # def test_verify_phone_number_user_not_exist(self):
    #     username = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     password = ''.join([random.choice("qwertyuiop12345678") for _ in range(12)])
    #     headers = self.generate_header(username)
    #     number = '19974345123'
    #     self.post_bind_phone_number(number, headers)
    #     verification_dict = PhoneVerification.objects.filter(number=number).values('verification_code').first()
    #     if verification_dict:
    #         verification_code_str = str(verification_dict.get('verification_code'))
    #     else:
    #         verification_code_str = None
    #     res = self.post_verify_phone_number(number, verification_code_str, headers)
    #     self.assertEqual(res.json()['code'], 5)
    #     self.assertEqual(res.status_code, 404)
    #     self.assertEqual(res.json()['info'],'User not found')

    # # Tests for /user/info
    # + normal case [GET]
    def test_get_user_info_normal(self):
        username = 'testGetUserInfo1'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.get("/author/user/info", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['data']['name'], username)

    # + unsupported method
    def test_get_user_info_unsupported(self):
        username = 'testGetUserInfo2'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.post("/author/user/info", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.json()['info'],'Bad request method')

    # + missing token
    def test_get_user_info_missing_token(self):
        username = 'testGetUserInfo3'
        password = '123456789'
        self.post_register(username, password)
        headers = {}
        res = self.client.get("/author/user/info", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.json()['info'],'Authorization token is missing')

    # + missing username
    def test_get_user_info_missing_username(self):
        username = 'testGetUserInfo4'
        password = '123456789'
        self.post_register(username, password)
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        res = self.client.get("/author/user/info", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.json()['info'],'Invalid token')

    # + user not exist
    def test_get_user_info_user_not_exist(self):
        username = 'testGetUserInfo5'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header('UserNotExist')
        res = self.client.get("/author/user/info", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 4)
        self.assertEqual(res.json()['info'],'User not found')

    # + Tests for /logout
    # + normal case [POST]
    def test_logout_normal(self):
        username = 'testLogout1'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.post("/author/logout", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['msg'],'Logout successfully')

    # + unsupported method
    def test_logout_unsupported(self):
        username = 'testLogout2'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header(username)
        res = self.client.get("/author/logout", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 1)
        self.assertEqual(res.json()['info'],'Invalid request')

    # + missing token
    def test_logout_missing_token(self):
        username = 'testLogout3'
        password = '123456789'
        self.post_register(username, password)
        headers = {}
        res = self.client.post("/author/logout", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 2)
        self.assertEqual(res.json()['info'],'Authorization token is missing')

    # + missing username
    def test_logout_missing_username(self):
        username = 'testLogout4'
        password = '123456789'
        self.post_register(username, password)
        headers = {'HTTP_AUTHORIZATION': 'Invalid token'}
        res = self.client.post("/author/logout", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 3)
        self.assertEqual(res.json()['info'],'Invalid token')

    # + user not exist
    def test_logout_user_not_exist(self):
        username = 'testLogout5'
        password = '123456789'
        self.post_register(username, password)
        headers = self.generate_header('UserNotExist')
        res = self.client.post("/author/logout", content_type="application/json",**headers)
        self.assertEqual(res.json()['code'], 5)
        self.assertEqual(res.json()['info'],'User not found')