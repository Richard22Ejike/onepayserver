from django.urls import path
from . import views

urlpatterns = [
    path('', views.getroutes),
    path('users/', views.getUsers),
    path('users/addUsers', views.addUsers),
    path('users/signup/', views.createUser),
    path('users/signin/', views.SignInUser),
    path('users/forget_password/', views.forget_password),  # Added for forget password
    path('users/reset_password/', views.reset_password),  # Added for reset password
    path('users/send_otp_to_phone/', views.send_otp_to_phone),  # Added for sending OTP to phone
    path('users/send_otp_to_email/', views.send_otp_to_email),  # Added for sending OTP to email
    path('users/otp_verified/', views.otp_verified),
    path('users/set-pin/<str:pk>/', views.SetPin),  # Added for OTP verification
    path('users/password_reset_otp_verified/', views.password_reset_otp_verified),
    path('users/change-pin/<str:pk>/', views.ChangePin),
    path('users/update/<str:pk>/', views.updateUser),
    path('users/<str:pk>/delete/', views.deleteUser),
    path('users/<str:pk>/', views.getUser),
    path('users/updateKYC1/<str:pk>/', views.updateUserToKYC1),  # Added for updating KYC step 1
    path('users/updateKYC2/<str:pk>/', views.updateUserToKYC2),  # Added for updating KYC step 2
    path('users/updateKYC2v2/<str:pk>/', views.updateUserToKYC2v2),
    path('users/updateKYC3/<str:pk>/', views.updateUserToKYC3),  # Added for updating KYC step 3
    path('api/core/guest/webhook/', views.webhook_listener, name='webhook_listener'),
]
