from django.db import models
from author.models import User
from VIIV.constants import DEFAULT_AVATAR_BASE64

class ChatRoom(models.Model):
    GROUP = 'group'
    PRIVATE = 'private'
    TYPE_CHOICES = [
        (GROUP, '群聊'),
        (PRIVATE, '私聊'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey(User, related_name='owned_chatrooms', on_delete=models.CASCADE,null=True, blank=True)
    members = models.ManyToManyField(User, related_name='member_chatrooms')
    admins = models.ManyToManyField(User, related_name='administered_chatrooms', blank=True)
    name = models.CharField(max_length=255)
    create_time = models.DateTimeField(auto_now_add=True)  # 创建时间
    update_time = models.DateTimeField(auto_now=True)  # 更新时间
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, null=True, blank=True,default=GROUP)
    avatar = models.TextField(default=DEFAULT_AVATAR_BASE64)
    def __str__(self):
        return f'ChatRoom {self.name}'
    
class ChatRoomNotice(models.Model):
    id = models.BigAutoField(primary_key=True)
    promulgator = models.ForeignKey(User, related_name='promulgator_notices', on_delete=models.CASCADE,null =True, blank=True)
    chatroom = models.ForeignKey(ChatRoom, related_name='notices', on_delete=models.CASCADE)
    title = models.TextField() ##公告标题
    text = models.TextField()  # 公告内容
    create_time = models.DateTimeField(auto_now_add=True)  # 发布时间

    class Meta:
        ordering = ['-create_time']  # 默认按发布时间降序排列


class Invitation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    id = models.BigAutoField(primary_key=True)
    chatroom = models.ForeignKey(ChatRoom, related_name='invitations', on_delete=models.CASCADE)
    invited = models.ForeignKey(User, related_name='received_invitations', on_delete=models.CASCADE)
    inviter = models.ForeignKey(User, related_name='sent_invitations', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation to {self.chatroom.name} for {self.invited.username} by {self.inviter.username}"
