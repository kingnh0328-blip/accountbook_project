"""
인증 및 계좌 관련 URL
- 담당: 팀원 A
"""

from django.urls import path
from . import views

app_name = 'accounts'  # URL 네임스페이스 ({% url 'accounts:login' %})

urlpatterns = [
    # ========================================
    # 루트 URL - 로그인 상태에 따라 분기
    # ========================================
    path('', views.HomeView.as_view(), name='home'),
    # GET / → 로그인O: 대시보드, 로그인X: 로그인 페이지

    # ========================================
    # 인증 관련 URL
    # ========================================
    path('signup/', views.SignupView.as_view(), name='signup'),
    # GET  /signup/ → 회원가입 폼
    # POST /signup/ → 회원 생성
    
    path('login/', views.LoginView.as_view(), name='login'),
    # GET  /login/ → 로그인 폼
    # POST /login/ → 로그인 처리
    
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # POST /logout/ → 로그아웃
    
    # ========================================
    # 계좌 관련 URL
    # ========================================
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    # GET /accounts/ → 계좌 목록
    
    path('accounts/create/', views.AccountCreateView.as_view(), name='account_create'),
    # GET  /accounts/create/ → 계좌 생성 폼
    # POST /accounts/create/ → 계좌 생성
    
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    # GET /accounts/1/ → 1번 계좌 상세
    # <int:pk>: URL에서 숫자를 받아서 pk(Primary Key) 변수로 전달
    
    path('accounts/<int:pk>/update/', views.AccountUpdateView.as_view(), name='account_update'),
    # GET  /accounts/1/update/ → 1번 계좌 수정 폼
    # POST /accounts/1/update/ → 계좌 수정
    
    path('accounts/<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),
    # POST /accounts/1/delete/ → 1번 계좌 삭제
]