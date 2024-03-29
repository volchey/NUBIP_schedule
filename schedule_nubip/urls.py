"""schedule_nubip URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView, LoginView

from main.views import FillCalendarView, BatchMeetUrlSetView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('batch_meet_url_set/', BatchMeetUrlSetView.as_view(), name='batch_meet_url_set'),
    path('accounts/login/', LoginView.as_view(template_name='admin/login.html')),
    path('login/', LoginView.as_view(template_name='admin/login.html')),
    path('accounts/', include('allauth.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('logout', LogoutView.as_view(), name='logout'),
    path('', FillCalendarView.as_view(template_name="index.html")),
]
