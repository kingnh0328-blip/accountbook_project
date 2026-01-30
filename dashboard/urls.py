# dashboard/urls.py
"""
대시보드 URL 설정
담당: 팀원 C
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # 대시보드 메인
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # 영수증 업로드 (transaction_id 필요)
    path('upload/<int:transaction_id>/', views.UploadReceiptView.as_view(), name='upload_receipt'),
    
    # 영수증 삭제
    path('delete/<int:pk>/', views.DeleteReceiptView.as_view(), name='delete_receipt'),
    
    # 영수증 다운로드 (선택 사항)
    path('download/<int:pk>/', views.DownloadReceiptView.as_view(), name='download_receipt'),
]