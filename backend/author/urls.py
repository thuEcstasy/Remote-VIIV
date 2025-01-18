from django.urls import path
import author.views as views

urlpatterns = [
    path('login', views.login),
    path('register',views.register),
    path('delete',views.delete),
    path('avatar/update',views.update_avatar),
    path('email/verification/send',views.bind_email),
    path('email/verification/verify',views.verify_email),
    path('number/verification/send',views.bind_phone_number),
    path('number/verification/verify',views.verify_phone_number),
    path('logout',views.logout),
    path('user/info',views.get_user_info),
    path('change/password',views.password_change),
    path('change/name',views.name_change)
]