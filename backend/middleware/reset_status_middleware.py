from django.utils.deprecation import MiddlewareMixin
from author.models import User
from asgiref.sync import sync_to_async
from VIIV.constants import OFFLINE

class ResetUserStatusMiddleware(MiddlewareMixin):
    _has_reset = False
 
    def process_request(self, request):
        if not self.__class__._has_reset:
            User.objects.update(status=OFFLINE)
            self.__class__._has_reset = True
       
    

