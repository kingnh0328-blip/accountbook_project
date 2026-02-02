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

from transactions.models import Transaction, Category, Attachment  # ← 변경!
from .forms import AttachmentForm


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    대시보드 메인 뷰
    - 월별 수입/지출 통계
    - 카테고리별 지출 비율
    """
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 월 파라미터 파싱 (YYYY-MM 형식, 기본값: 현재 월)
        month_param = self.request.GET.get('month')
        if month_param:
            try:
                year, month = map(int, month_param.split('-'))
            except (ValueError, AttributeError):
                # 잘못된 형식이면 현재 월 사용
                now = datetime.now()
                year, month = now.year, now.month
        else:
            now = datetime.now()
            year, month = now.year, now.month
        
        # 해당 월의 거래 필터링
        transactions = Transaction.objects.filter(
            user=self.request.user,
            occurred_at__year=year,
            occurred_at__month=month
        )
        
        # 수입/지출 집계
        income = transactions.filter(tx_type='IN').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        expense = transactions.filter(tx_type='OUT').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        balance = income - expense
        
        # 카테고리별 통계 (지출만)
        category_stats = transactions.filter(
            tx_type='OUT',
            category__isnull=False
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]  # Top 5
        
        # 카테고리별 비율 계산 (차트용)
        total_expense = sum(stat['total'] for stat in category_stats)
        for stat in category_stats:
            stat['percentage'] = (stat['total'] / total_expense * 100) if total_expense > 0 else 0
        
        context.update({
            'year': year,
            'month': month,
            'total_income': income,
            'total_expense': expense,
            'balance': balance,
            'transaction_count': transactions.count(),
            'category_stats': category_stats,
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