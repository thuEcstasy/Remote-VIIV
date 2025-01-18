from utils import utils_time
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH

# Create your models here.

class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_LENGTH, unique=True)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    
    class Meta:
        indexes = [models.Index(fields=["name"])]
        
    def serialize(self):
        boards = Board.objects.filter(user=self)
        return {
            "id": self.id, 
            "name": self.name, 
            "createdAt": self.created_time,
            "boards": [ return_field(board.serialize(), ["id", "boardName", "userName", "createdAt"])
                       for board in boards ]
        }
    
    def __str__(self) -> str:
        return self.name


class Board(models.Model):
    # TODO Start: [Student] Finish the model of Board
    
    # id, BigAutoField, primary_key=True
    # user, ForeignKey to User, CASCADE deletion
    # board_state, CharField
    # board_name, CharField
    # created_time, FloatField, default=utils_time.get_timestamp
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board_state = models.CharField(max_length=2500)
    board_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    
    # Meta data
    # Create index on board_name
    # Create unique_together on user and board_name
    class Meta:
        indexes = [models.Index(fields=["board_name"])]
        unique_together = ["user", "board_name"]
    
    # TODO End: [Student] Finish the model of Board


    def serialize(self):
        userName = self.user.name
        return {
            "id": self.id,
            "board": self.board_state, 
            "boardName": self.board_name,
            "userName": userName,
            "createdAt": self.created_time
        }

    def __str__(self) -> str:
        return f"{self.user.name}'s board {self.board_name}"
