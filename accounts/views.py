"""
인증 및 계좌 관리 뷰
- 역할: 회원가입, 로그인, 로그아웃, 계좌 CRUD
- 담당: 팀원 A
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin  # 로그인 필수 처리
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.db.models import Sum

from .models import Account
from .forms import AccountForm
from transactions.models import Transaction


# ============================================
# 1. 인증 관련 뷰 (회원가입, 로그인, 로그아웃)
# ============================================

class HomeView(View):
    """
    홈 뷰 (루트 URL)
    - 로그인된 사용자: 대시보드로 리다이렉트
    - 비로그인 사용자: 로그인 페이지 표시
    """
    def get(self, request):
        if request.user.is_authenticated:
            # 로그인되어 있으면 대시보드로
            return redirect('dashboard:dashboard')
        else:
            # 로그인되어 있지 않으면 로그인 페이지로
            return redirect('accounts:login')


class SignupView(CreateView):
    """
    회원가입 뷰
    - GET: 회원가입 폼 보여주기
    - POST: 새 사용자 생성
    """
    form_class = UserCreationForm           # Django 기본 회원가입 폼
    template_name = 'accounts/signup.html'  # 사용할 템플릿
    success_url = reverse_lazy('accounts:login')  # 성공 시 로그인 페이지로 이동
    
    # 예: GET /signup/ → 회원가입 폼
    #     POST /signup/ → 회원 생성 후 로그인 페이지로


class LoginView(FormView):
    """
    로그인 뷰
    - GET: 로그인 폼 보여주기
    - POST: 로그인 처리
    """
    form_class = AuthenticationForm         # Django 기본 로그인 폼
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('dashboard:dashboard')  # 성공 시 대시보드로
    
    def form_valid(self, form):
        """폼이 유효할 때 (로그인 성공)"""
        login(self.request, form.get_user())  # 세션에 사용자 정보 저장
        return super().form_valid(form)


class LogoutView(View):
    """
    로그아웃 뷰
    - POST 요청만 허용 (보안)
    """
    def post(self, request):
        logout(request)  # 세션에서 사용자 정보 제거
        return redirect('accounts:login')
    
    # 템플릿에서 사용:
    # <form method="post" action="{% url 'accounts:logout' %}">
    #     {% csrf_token %}
    #     <button>로그아웃</button>
    # </form>


# ============================================
# 2. 계좌 관리 뷰 (CRUD)
# ============================================

class AccountListView(LoginRequiredMixin, ListView):
    """
    계좌 목록 뷰
    - 로그인한 사용자의 활성 계좌 목록 표시
    """
    model = Account
    template_name = 'accounts/account_list.html'
    context_object_name = 'accounts'  # 템플릿에서 {{ accounts }}로 사용

    def get_queryset(self):
        """
        중요: 본인 계좌만 조회!
        - 다른 사람의 계좌는 절대 보이면 안 됨
        """
        return Account.objects.filter(
            user=self.request.user,  # 현재 로그인한 사용자
            is_active=True           # 활성 계좌만
        )

    def get_context_data(self, **kwargs):
        """총 수입, 총 지출, 순자산 계산"""
        context = super().get_context_data(**kwargs)

        # 사용자의 모든 거래 조회
        transactions = Transaction.objects.filter(user=self.request.user)

        # 총 수입
        total_income = transactions.filter(tx_type='IN').aggregate(
            total=Sum('amount')
        )['total'] or 0

        # 총 지출
        total_expense = transactions.filter(tx_type='OUT').aggregate(
            total=Sum('amount')
        )['total'] or 0


        # 총 순자산 = 모든 계좌의 balance 합계
        # (각 계좌의 balance는 거래 발생 시 자동 업데이트됨)
        net_assets = Account.objects.filter(
            user=self.request.user,
            is_active=True
        ).aggregate(
            total=Sum('balance')
        )['total'] or 0

        context.update({
            'total_income': total_income,
            'total_expense': total_expense,
            'net_assets': net_assets,
        })

        return context



class AccountCreateView(LoginRequiredMixin, CreateView):
    """
    계좌 생성 뷰
    - GET: 계좌 생성 폼 보여주기
    - POST: 새 계좌 생성
    """
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:account_list')
    
    def form_valid(self, form):
        """
        폼이 유효할 때 실행
        - 자동으로 현재 사용자를 계좌의 소유자로 설정
        """
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    # 예: GET /accounts/create/ → 계좌 생성 폼
    #     POST /accounts/create/ → 계좌 생성 후 목록으로


class AccountDetailView(LoginRequiredMixin, DetailView):
    """
    계좌 상세 뷰
    - 특정 계좌의 상세 정보 표시
    """
    model = Account
    template_name = 'accounts/account_detail.html'
    context_object_name = 'account'
    
    def get_queryset(self):
        """본인 계좌만 접근 가능"""
        return Account.objects.filter(user=self.request.user)
    
    # 예: GET /accounts/1/ → 1번 계좌 상세
    # 다른 사람의 계좌 번호로 접근하면 404 에러


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """
    계좌 수정 뷰
    - GET: 계좌 수정 폼 (기존 데이터 포함)
    - POST: 계좌 정보 수정
    """
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:account_list')
    
    def get_queryset(self):
        """본인 계좌만 수정 가능"""
        return Account.objects.filter(user=self.request.user)
    
    # 예: GET /accounts/1/update/ → 1번 계좌 수정 폼
    #     POST /accounts/1/update/ → 계좌 수정 후 목록으로


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    """
    계좌 삭제 뷰
    - POST: 계좌 실제 삭제 (연결된 거래내역도 CASCADE로 함께 삭제)
    """
    model = Account
    success_url = reverse_lazy('accounts:account_list')

    def get_queryset(self):
        """본인 계좌만 삭제 가능"""
        return Account.objects.filter(user=self.request.user)


# ============================================
# 뷰의 흐름 요약
# ============================================
#
# 1. 사용자가 URL 접속 (예: /accounts/create/)
# 2. urls.py에서 해당 뷰 호출 (AccountCreateView)
# 3. 뷰에서 처리:
#    - GET: 템플릿 렌더링 (폼 보여주기)
#    - POST: 데이터 저장 후 리다이렉트
# 4. 템플릿에서 HTML 생성하여 사용자에게 표시
#
# LoginRequiredMixin: 로그인하지 않은 사용자는 자동으로 로그인 페이지로 이동