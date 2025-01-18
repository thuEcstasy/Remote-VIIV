from django.urls import path
import communication.views as views

urlpatterns = [
    path('searchby/member',views.filter_messages_by_sender_in_room),
    path('searchby/date',views.filter_messages_by_date_in_room),
    path('searchby/room',views.filter_messages_by_room),
    path('delete/message',views.delete_message),
]