"""
거래 관리 및 필터링 뷰
- 역할: 거래 CRUD, 필터링/검색, 영수증 업로드
- 담당: 팀원 B
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q  # OR 조건 검색용
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from .models import Transaction, Attachment, Category
from accounts.models import Account
from .forms import TransactionForm, AttachmentForm


# ============================================
# 1. 거래 관리 뷰 (CRUD + 필터링)
# ============================================

class TransactionListView(LoginRequiredMixin, ListView):
    """
    거래 내역 목록 뷰 (필터링 포함)
    - 본인 거래만 표시
    - 계좌, 카테고리, 입출금, 기간, 키워드로 필터링 가능
    """
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20  # 페이지당 20개씩 표시
    
    def get_queryset(self):
        """
        거래 조회 + 필터링
        - request.GET으로 전달된 필터 조건 적용
        """
        # 기본: 본인 거래만 + 관련 데이터 미리 로딩 (성능 최적화)
        queryset = Transaction.objects.filter(
            user=self.request.user
        ).select_related('account', 'category')
        
        # 1. 계좌 필터 (?account=1)
        account_id = self.request.GET.get('account')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        
        # 2. 카테고리 필터 (?category=2)
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # 3. 입출금 타입 필터 (?tx_type=OUT)
        tx_type = self.request.GET.get('tx_type')
        if tx_type in ['IN', 'OUT']:
            queryset = queryset.filter(tx_type=tx_type)
        
        # 4. 기간 필터 (?start_date=2026-01-01)
        start_date = self.request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(occurred_at__gte=start_date)
        
        end_date = self.request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(occurred_at__lte=end_date)
        
        # 5. 키워드 검색 (?q=카페)
        # 메모 또는 가맹점에서 검색
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(memo__icontains=q) | Q(merchant__icontains=q)
            )
            # icontains: 대소문자 구분 없이 포함 검색
            # Q(...) | Q(...): OR 조건
        
        return queryset
    
    # 예: GET /transactions/ → 전체 거래 목록
    #     GET /transactions/?account=1 → 1번 계좌 거래만
    #     GET /transactions/?q=카페 → "카페"가 포함된 거래 검색


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """
    거래 생성 뷰
    """
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/transaction_form.html'
    success_url = reverse_lazy('transactions:transaction_list')
    
    def get_form(self, form_class=None):
        """
        폼에서 본인 계좌만 선택 가능하도록 설정
        """
        form = super().get_form(form_class)
        # account 필드의 선택지를 본인 계좌로 제한
        form.fields['account'].queryset = Account.objects.filter(
            user=self.request.user,
            is_active=True
        )
        return form
    
    def form_valid(self, form):
        """자동으로 현재 사용자 설정"""
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    # 예: GET /transactions/create/ → 거래 생성 폼
    #     POST /transactions/create/ → 거래 생성


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """
    거래 상세 뷰
    - 거래 정보 + 영수증 표시
    """
    model = Transaction
    template_name = 'transactions/transaction_detail.html'
    context_object_name = 'transaction'
    
    def get_queryset(self):
        """본인 거래만 접근 가능"""
        return Transaction.objects.filter(user=self.request.user)
    
    # 템플릿에서 영수증 확인:
    # {% if transaction.attachment %}
    #     <img src="{{ transaction.attachment.file.url }}">
    # {% endif %}


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """
    거래 수정 뷰
    """
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/transaction_form.html'
    
    def get_queryset(self):
        """본인 거래만 수정 가능"""
        return Transaction.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        """수정 후 해당 거래 상세 페이지로"""
        return reverse_lazy('transactions:transaction_detail', 
                          kwargs={'pk': self.object.pk})


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """
    거래 삭제 뷰
    """
    model = Transaction
    success_url = reverse_lazy('transactions:transaction_list')
    
    def get_queryset(self):
        """본인 거래만 삭제 가능"""
        return Transaction.objects.filter(user=self.request.user)
    
    # 삭제 시 연결된 영수증도 자동 삭제됨 (CASCADE)


# ============================================
# 2. 영수증 업로드 뷰
# ============================================

class AttachmentUploadView(LoginRequiredMixin, CreateView):
    """
    영수증 업로드 뷰
    - 특정 거래에 영수증 첨부
    """
    model = Attachment
    form_class = AttachmentForm
    template_name = 'transactions/transaction_upload.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        거래가 본인 것인지 확인
        """
        self.transaction = get_object_or_404(
            Transaction,
            pk=kwargs['pk'],
            user=request.user  # 본인 거래만
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.transaction
        return context

    def form_valid(self, form):
        """
        파일 메타데이터 자동 설정
        """
        form.instance.user = self.request.user
        form.instance.transaction = self.transaction
        
        # 파일 정보 추출
        uploaded_file = form.cleaned_data['file']
        form.instance.original_name = uploaded_file.name
        form.instance.size = uploaded_file.size
        form.instance.content_type = uploaded_file.content_type
        
        return super().form_valid(form)
    

    
    def get_success_url(self):
        """업로드 후 해당 거래 상세 페이지로"""
        return reverse_lazy('transactions:transaction_detail',
                          kwargs={'pk': self.transaction.pk})
    
    # 예: GET /transactions/1/upload/ → 1번 거래에 영수증 업로드 폼
    #     POST /transactions/1/upload/ → 영수증 업로드


class AttachmentDeleteView(LoginRequiredMixin, View):
    """
    영수증 삭제 뷰
    """
    def post(self, request, pk):
        """POST 요청으로만 삭제 가능"""
        attachment = get_object_or_404(
            Attachment,
            pk=pk,
            user=request.user  # 본인 영수증만
        )
        
        transaction_pk = attachment.transaction.pk
        attachment.delete()  # 파일도 함께 삭제됨 (모델의 delete 메서드)
        
        return redirect('transactions:transaction_detail', pk=transaction_pk)
    
    # 예: POST /attachment/5/delete/ → 5번 영수증 삭제


# ============================================
# URL 패턴과의 연결 예시
# ============================================
#
# urls.py에서:
# path('', TransactionListView.as_view(), name='transaction_list')
# path('create/', TransactionCreateView.as_view(), name='transaction_create')
# path('<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail')
#
# 필터링 URL 예시:
# /transactions/?account=1&category=2&tx_type=OUT&q=카페
# → 1번 계좌, 2번 카테고리, 출금, "카페" 검색
