from django.urls import path
import friends.views as views

urlpatterns = [
     path('search/user',views.search_users),
     path('friend/list_group',views.get_all_friends_in_group),
     path('friend/list_all',views.get_all_friends),
     path('delete/friend',views.delete_friend),
     path('request/friend',views.send_friend_request),
     path('require/friend',views.get_friend_requests),
     path('request/friend/handle',views.handle_friend_request),
     path('friend/group/create',views.create_group),
     path('friend/group/move',views.add_user_to_group),
     path('friends/groups',views.get_all_groups),
     path('get/position',views.get_user_position),
     path('get/all/ingroup',views.get_all_users_in_group),
     path('rename/group',views.rename_group),
     path('remove/group',views.remove_group),
]