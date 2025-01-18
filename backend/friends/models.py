from django.db import models
from author.models import User

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)  # 请求发送的时间
    status = models.CharField(default='pending',max_length=10)  # 请求是否被接受

    class Meta:
        unique_together = ('from_user', 'to_user')  # 确保每对用户之间最多只有一个好友请求

    
class Group(models.Model):
    group_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100,default='My friends')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')
    

class UserGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_groups')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_members')

    class Meta:
        unique_together = ('user', 'group')
