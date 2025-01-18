from utils import utils_time
from django.db import models
from utils.utils_request import return_field
from VIIV.constants import OFFLINE
from utils.utils_require import MAX_CHAR_LENGTH
from VIIV.constants import DEFAULT_AVATAR_BASE64
import os

# Create your models here.

class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_LENGTH, unique=True,db_collation='utf8_bin')
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    registered_time = models.FloatField(default=utils_time.get_timestamp)
    login_time = models.FloatField(default=None, null=True)
    status = models.IntegerField(default=OFFLINE)
    avatar = models.TextField(default=DEFAULT_AVATAR_BASE64)  # 添加头像字段，假设有default_avatar.jpg作为默认图片
    email = models.EmailField(unique=False, null=True, blank=True)
    phone_number = models.CharField(max_length=11, null=True, blank=True)
    
    class Meta:
        indexes = [models.Index(fields=["name"])]
        
    def serialize(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "createdAt": self.created_time,
        }
    
    def __str__(self) -> str:
        return self.name

class PhoneVerification(models.Model):
    number = models.CharField(max_length=11, null=True, blank=True)
    verification_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


class EmailVerification(models.Model):
    email = models.EmailField(unique=True)
    verification_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

