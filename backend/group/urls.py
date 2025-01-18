from django.urls import path
import group.views as views

urlpatterns = [
    path('create',views.create_group),
    path('room/information',views.chatroom_details),
    path('room/setadmins',views.assign_admins),
    path('room/transfer',views.transfer_ownership),
    path('room/remove',views.remove_member),
    path('room/invite',views.invite_friend),
    path('room/handle',views.handle_invitation),
    path('room/get/invitation',views.get_pending_invitations),
    path('room/leave',views.leave_group),
    path('room/dissolve',views.dissolve_chatroom),
    path('room/post/notice',views.post_notice),
    # path('room/get/notices',views.get_notices_with_read_status),
    # path('room/get/unread_notice',views.get_latest_unread_notice),
    # path("room/notice/setread",views.set_notice_read),
    path('room/getall',views.get_my_chatrooms),
    path('get/identity',views.get_identity),
    path('judge/friend',views.judge_friend),
]