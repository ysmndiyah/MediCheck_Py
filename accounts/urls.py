from django.urls import path
from . import views


app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('bmi/', views.bmi_view, name='bmi'),
    path('monitor/', views.monitor_view, name='monitor'),
    path('tips/', views.tips_view, name='tips'),
    path('logout/', views.logout_view, name='logout'),
    path("weekly-meal/", views.weekly_meal_view, name="weekly_meal"),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path("chatbot/api/", views.chatbot_api, name="chatbot_api"),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('new-password/', views.new_password_view, name='new_password'),
]