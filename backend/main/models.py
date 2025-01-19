from django.db import models

# Create your models here.
class User(models.Model):
    seatNumber = models.IntegerField()
    seatName = models.CharField(max_length=100)
