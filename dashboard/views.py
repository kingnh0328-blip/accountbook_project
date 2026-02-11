# dashboard/views.py
"""
대시보드 뷰
담당: 팀원 C
팀원 B와 소통 완료 - Transaction 연동
transactions.Attachment 사용
"""

from django.views.generic import TemplateView, CreateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from datetime import datetime
import calendar
from collections import defaultdict

from transactions.models import Transaction, Category, Attachment  
from accounts.models import Account  
from .forms import AttachmentForm


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    대시보드 메인 뷰
    - 월별 수입/지출 통계
    - 카테고리별 지출 비율
    """
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        대시보드 페이지에 필요한 데이터를 준비

        처리 순서:
        1. 계좌 존재 여부 확인
        2. 월 파라미터 파싱 (URL에서 month 파라미터 추출)
        3. 거래 필터링 (선택된 월 및 계좌 기준)
        4. 수입/지출 집계
        5. 순합 계산
        6. 카테고리별 통계 생성
        7. 달력 데이터 생성
        8. 최근 거래 내역 조회
        """
        context = super().get_context_data(**kwargs)

        # ===== 1단계: 계좌 존재 여부 확인 =====
        # 사용자가 활성 계좌를 가지고 있는지 확인
        has_account = Account.objects.filter(
            user=self.request.user,
            is_active=True
        ).exists()

        if not has_account:
            # 계좌가 없으면 계좌 생성 안내 페이지로 변경
            self.template_name = 'accounts/make_your_account.html'
            return context

        # ===== 2단계: 월 파라미터 파싱 =====
        # URL에서 month 파라미터를 읽어 연도와 월을 추출
        # 예: ?month=2026-02 → year=2026, month=2
        month_param = self.request.GET.get('month')
        if month_param:
            try:
                year, month = map(int, month_param.split('-'))
            except (ValueError, AttributeError):
                # 잘못된 형식이면 현재 월을 기본값으로 사용
                now = datetime.now()
                year, month = now.year, now.month
        else:
            # 파라미터가 없으면 현재 월을 사용
            now = datetime.now()
            year, month = now.year, now.month

        # ===== 3단계: 거래 필터링 =====
        # URL에서 계좌 ID 파라미터 추출
        account_id = self.request.GET.get('account')

        # 선택된 월의 모든 거래 조회 (활성 계좌만)
        transactions = Transaction.objects.filter(
            user=self.request.user,
            account__is_active=True,
            occurred_at__year=year,
            occurred_at__month=month
        )

        # 특정 계좌가 선택된 경우 해당 계좌 거래만 필터링
        if account_id:
            transactions = transactions.filter(account_id=account_id)

        # 사용자의 활성 계좌 목록 조회 (드롭다운 표시용)
        accounts = Account.objects.filter(user=self.request.user, is_active=True)
        
        # ===== 4단계: 수입/지출 집계 =====
        # 선택된 월의 총 수입 계산 (tx_type='IN')
        income = transactions.filter(tx_type='IN').aggregate(
            total=Sum('amount')
        )['total'] or 0

        # 선택된 월의 총 지출 계산 (tx_type='OUT')
        expense = transactions.filter(tx_type='OUT').aggregate(
            total=Sum('amount')
        )['total'] or 0

        # ===== 5단계: 순합 계산 =====
        # 계좌 잔액 합계 (계좌 필터 적용)
        if account_id:
            # 특정 계좌가 선택된 경우: 해당 계좌의 잔액만
            account_balance = Account.objects.filter(
                user=self.request.user,
                id=account_id
            ).aggregate(
                total=Sum('balance')
            )['total'] or 0
        else:
            # 전체 계좌 선택 시: 모든 계좌의 잔액 합계
            account_balance = Account.objects.filter(
                user=self.request.user
            ).aggregate(
                total=Sum('balance')
            )['total'] or 0

        # 최종 순합 계산 공식:
        # 순합 = 계좌 잔액 
        balance = account_balance
        
        # 카테고리별 통계 (지출만)
        category_summary = transactions.filter(
            tx_type='OUT',
            category__isnull=False
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]  # Top 5 - 지출 높은 순으로 정렬

        # 카테고리별 비율 계산 (차트용)
        if category_summary:
            total_expense_for_ratio = sum(stat['total'] for stat in category_summary)
            for stat in category_summary:
                # expense_ratio: 전체 지출 대비 해당 카테고리 지출 비율
                stat['expense_ratio'] = (stat['total'] / total_expense_for_ratio * 100) if total_expense_for_ratio > 0 else 0
                # percentage: 프로그레스 바 너비용 (동일한 값)
                stat['percentage'] = stat['expense_ratio']

        # ===== 달력 데이터 생성 =====
        # 날짜별 수입/지출 계산
        daily_data = defaultdict(lambda: {'income': 0, 'expense': 0})

        for transaction in transactions:
            day = transaction.occurred_at.day
            if transaction.tx_type == 'IN':
                daily_data[day]['income'] += float(transaction.amount)
            else:
                daily_data[day]['expense'] += float(transaction.amount)

        # 달력 구조 생성 (주 단위로)
        cal = calendar.monthcalendar(year, month)
        calendar_weeks = []

        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append(None)
                else:
                    week_data.append({
                        'day': day,
                        'income': daily_data[day]['income'],
                        'expense': daily_data[day]['expense']
                    })
            calendar_weeks.append(week_data)
        # ===========================

        # 최근 거래 내역 (최대 4개)
        recent_transactions = transactions.order_by('-occurred_at')[:4]

        context.update({
            'year': year,
            'month': month,
            'total_income': income,
            'total_expense': expense,
            'balance': balance,
            'transaction_count': transactions.count(),
            'category_summary': category_summary,
            'calendar_weeks': calendar_weeks,
            'accounts': accounts,
            'selected_account_id': account_id,
            'recent_transactions': recent_transactions,
        })
        return context


class UploadReceiptView(LoginRequiredMixin, CreateView):
    """
    영수증 업로드 뷰
    """
    model = Attachment
    form_class = AttachmentForm
    template_name = 'dashboard/upload_receipt.html'
    
    def get_success_url(self):
        # 업로드 후 거래 상세 페이지로 리다이렉트
        transaction_id = self.kwargs.get('transaction_id')
        return reverse_lazy('transactions:transaction_detail', kwargs={'pk': transaction_id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 거래 정보 가져오기
        transaction_id = self.kwargs.get('transaction_id')
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            user=self.request.user  # 본인 거래만
        )
        context['transaction'] = transaction
        
        return context
    
    def form_valid(self, form):
        # 현재 로그인한 사용자로 설정
        form.instance.user = self.request.user
        
        # URL에서 transaction_id 가져오기
        transaction_id = self.kwargs.get('transaction_id')
        
        # Transaction 존재 여부 및 권한 확인
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            user=self.request.user  # 본인 거래만 업로드 가능
        )
        
        form.instance.transaction = transaction
        
        return super().form_valid(form)


class DeleteReceiptView(LoginRequiredMixin, DeleteView):
    """
    영수증 삭제 뷰
    """
    model = Attachment
    template_name = 'dashboard/delete_receipt.html'
    
    def get_success_url(self):
        # 삭제 후 거래 상세 페이지로 리다이렉트
        return reverse_lazy('transactions:transaction_detail', kwargs={'pk': self.object.transaction.id})
    
    def get_queryset(self):
        # 본인이 업로드한 파일만 삭제 가능
        return Attachment.objects.filter(user=self.request.user)


class DownloadReceiptView(LoginRequiredMixin, View):
    """
    영수증 다운로드 뷰
    """
    def get(self, request, *args, **kwargs):
        attachment_id = kwargs.get('pk')
        
        # 본인이 업로드한 파일만 다운로드 가능
        attachment = get_object_or_404(
            Attachment,
            id=attachment_id,
            user=request.user
        )
        
        # 파일이 존재하는지 확인
        if not attachment.file:
            raise Http404("파일을 찾을 수 없습니다.")
        
        # 파일 다운로드
        response = FileResponse(
            attachment.file.open('rb'),
            content_type=attachment.content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{attachment.original_name}"'
        
        return response