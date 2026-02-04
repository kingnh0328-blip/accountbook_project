"""
고객센터 URL 설정
"""

from django.urls import path
from . import views

app_name = 'report'

urlpatterns = [
    path('', views.CustomerServiceView.as_view(), name='customer_service'),
]
