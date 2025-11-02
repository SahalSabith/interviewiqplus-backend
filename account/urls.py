from django.urls import path
from .views import RegisterUserAPIView, LoginAPIView, RegisterFaceView, VerifyFaceView

urlpatterns = [
    path('register/', RegisterUserAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('register-face/', RegisterFaceView.as_view(), name='register-face'),
    path('verify-face/', VerifyFaceView.as_view(), name='verify-face'),
]