"""
URL configuration for vaqueroconnect project.
"""
from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('sports/', views.sports, name='sports'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('account/', views.account, name='account'),
    path('signup/', views.signup, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
