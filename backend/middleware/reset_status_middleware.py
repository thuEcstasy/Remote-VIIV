from django.utils.deprecation import MiddlewareMixin
from asgiref.sync import sync_to_async
from VIIV.constants import OFFLINE

class ResetUserStatusMiddleware(MiddlewareMixin):
    _has_reset = False

    

