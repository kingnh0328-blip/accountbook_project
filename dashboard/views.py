# dashboard/views.py
"""
대시보드 & 파일 업로드 뷰
담당: 팀원 C
"""

from django.views.generic import TemplateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import Http404
from datetime import datetime
import os

# 다른 팀원 모델 import (소통 필요)
# accounts 앱에서
# from accounts.models import Account

# transactions 앱에서
# from transactions.models import Transaction, Category

from .models import Attachment
from .forms import AttachmentForm


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    대시보드 뷰
    - 월별 통계 조회
    - 카테고리별 집계
    """
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. 월 파라미터 파싱
        month_param = self.request.GET.get('month')
        if month_param:
            try:
                # YYYY-MM 형식
                year, month = map(int, month_param.split('-'))
            except (ValueError, AttributeError):
                # 잘못된 형식이면 현재 월 사용
                today = datetime.now()
                year, month = today.year, today.month
        else:
            # 파라미터 없으면 현재 월
            today = datetime.now()
            year, month = today.year, today.month
        
        # 2. 해당 월 거래 필터
        # (소통 필요: Transaction 모델이 transactions 앱에 있음)
        # transactions = Transaction.objects.filter(
        #     user=self.request.user,
        #     occurred_at__year=year,
        #     occurred_at__month=month
        # )
        
        # 임시로 빈 쿼리셋 (팀원 B의 Transaction 모델 확정 후 수정)
        transactions = None  # (소통 필요)
        
        # 3. 집계
        if transactions is not None:
            # 총 수입 (입금)
            total_income = transactions.filter(
                tx_type='IN'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # 총 지출 (출금)
            total_expense = transactions.filter(
                tx_type='OUT'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # 순합 (수입 - 지출)
            balance = total_income - total_expense
            
            # 거래 건수
            transaction_count = transactions.count()
        else:
            # 임시 기본값
            total_income = 0
            total_expense = 0
            balance = 0
            transaction_count = 0
        
        # 4. 카테고리별 통계 (지출만)
        if transactions is not None:
            category_stats = transactions.filter(
                tx_type='OUT',
                category__isnull=False  # 카테고리가 있는 것만
            ).values(
                'category__name'  # Category 모델의 name 필드
            ).annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-total')[:5]  # 상위 5개
            
            # 5. 퍼센트 계산 (막대바용)
            if category_stats:
                max_amount = category_stats[0]['total']
                for stat in category_stats:
                    if max_amount > 0:
                        stat['percentage'] = (stat['total'] / max_amount) * 100
                    else:
                        stat['percentage'] = 0
            else:
                category_stats = []
        else:
            category_stats = []
        
        # Context 전달
        context.update({
            'year': year,
            'month': month,
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'transaction_count': transaction_count,
            'category_stats': category_stats,
        })
        
        return context


class UploadReceiptView(LoginRequiredMixin, CreateView):
    """
    영수증 업로드 뷰
    - 파일 업로드
    - 확장자 검증 (.jpg/.png/.pdf)
    - 용량 검증 (5MB 이하)
    - DB 저장 + 파일 저장
    """
    model = Attachment
    form_class = AttachmentForm
    template_name = 'dashboard/upload_receipt.html'
    
    def get_success_url(self):
        # 업로드 후 해당 거래 상세 페이지로 리다이렉트
        # (소통 필요: transactions 앱의 transaction_detail URL)
        transaction_id = self.kwargs.get('transaction_id')
        # return reverse_lazy('transactions:transaction_detail', kwargs={'pk': transaction_id})
        
        # 임시로 대시보드로 리다이렉트
        return reverse_lazy('dashboard:dashboard')
    
    def form_valid(self, form):
        # 현재 로그인한 사용자로 설정
        form.instance.user = self.request.user
        
        # URL에서 transaction_id 가져오기
        transaction_id = self.kwargs.get('transaction_id')
        
        # (소통 필요: Transaction 모델 확인)
        # transaction = get_object_or_404(
        #     Transaction,
        #     id=transaction_id,
        #     user=self.request.user  # 본인 거래만
        # )
        # form.instance.transaction = transaction
        
        # 임시 처리 (팀원 B 코드 확정 후 수정)
        form.instance.transaction_id = transaction_id  # (소통 필요)
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_id = self.kwargs.get('transaction_id')
        
        # (소통 필요: Transaction 정보 표시)
        # transaction = get_object_or_404(
        #     Transaction,
        #     id=transaction_id,
        #     user=self.request.user
        # )
        # context['transaction'] = transaction
        
        context['transaction_id'] = transaction_id
        return context


class DeleteReceiptView(LoginRequiredMixin, DeleteView):
    """
    영수증 삭제 뷰
    - DB에서 삭제
    - 실제 파일도 삭제
    """
    model = Attachment
    success_url = reverse_lazy('dashboard:dashboard')
    template_name = 'dashboard/delete_receipt_confirm.html'
    
    def get_queryset(self):
        # 본인이 업로드한 파일만 삭제 가능
        return Attachment.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        # 삭제 후 해당 거래 상세 페이지로
        # (소통 필요: transactions 앱 URL)
        transaction_id = self.object.transaction_id
        # return reverse_lazy('transactions:transaction_detail', kwargs={'pk': transaction_id})
        
        # 임시로 대시보드로
        return reverse_lazy('dashboard:dashboard')


# 추가 기능: 영수증 다운로드 (선택 사항)
from django.http import FileResponse

class DownloadReceiptView(LoginRequiredMixin, View):
    """
    영수증 다운로드 뷰
    """
    def get(self, request, pk):
        # 본인 파일만 다운로드 가능
        attachment = get_object_or_404(
            Attachment,
            pk=pk,
            user=request.user
        )
        
        # 파일 존재 여부 확인
        if not os.path.exists(attachment.file.path):
            raise Http404("파일을 찾을 수 없습니다.")
        
        # 파일 응답
        response = FileResponse(
            open(attachment.file.path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(attachment.file.name)
        )
        return response