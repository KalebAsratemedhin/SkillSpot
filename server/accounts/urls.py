from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    PasswordResetView,
    PasswordResetConfirmView,
    UserDetailView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('reset-password-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='reset_password_confirm'),
    
    path('users/me/', UserDetailView.as_view(), name='user_detail'),
]