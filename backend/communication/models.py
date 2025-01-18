from django.db import models
from author.models import User
from group.models import ChatRoomNotice

class MessageStatus(models.Model):
    id = models.BigAutoField(primary_key=True)
    conversation_id = models.IntegerField()  # 全局唯一的会话标志符
    msg_id = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)  # 消息创建时间
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    reply_id = models.IntegerField(null=True, blank=True)
    

    def __str__(self):  
        return f'Message {self.msg_id} in Conversation {self.conversation_id}'

    class Meta:
        unique_together = ('conversation_id', 'msg_id')
class ConversationMember(models.Model):
    conversation_id = models.IntegerField()  # 全局唯一的会话标志符
    member_user_id = models.IntegerField()  # 成员的用户标志符
    join_time = models.DateTimeField(auto_now_add=True)  # 成员的加入时间
    read_front_index = models.IntegerField(default=0)  # 成员当前已读到的消息索引
    deleted_messages = models.ManyToManyField(MessageStatus, related_name='deleted_by') 

    def __str__(self):
        return f'Conversation {self.conversation_id} - Member {self.member_user_id}'
    class Meta:
        unique_together = ('conversation_id', 'member_user_id')






