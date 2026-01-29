"""
대시보드 뷰
- 역할: 월별/카테고리별 통계 집계 및 표시
- 담당: 팀원 C
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.utils.timezone import now
from datetime import datetime

from transactions.models import Transaction


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    대시보드 뷰
    - 월별 수입/지출 요약
    - 카테고리별 지출 통계
    - CSS 막대 그래프로 시각화
    """
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        템플릿에 전달할 데이터 준비
        - context: 딕셔너리 형태로 템플릿에 전달됨
        """
        context = super().get_context_data(**kwargs)
        
        # ========================================
        # 1. 월 파라미터 처리
        # ========================================
        # URL: /dashboard/?month=2026-01
        month_param = self.request.GET.get('month')
        
        if month_param:
            try:
                # '2026-01' 형식을 파싱
                year, month = map(int, month_param.split('-'))
            except:
                # 잘못된 형식이면 현재 월 사용
                today = now().date()
                year, month = today.year, today.month
        else:
            # 파라미터가 없으면 현재 월 사용
            today = now().date()
            year, month = today.year, today.month
        
        # 템플릿에서 사용할 년/월 정보
        context['year'] = year
        context['month'] = month
        
        # ========================================
        # 2. 해당 월의 거래 데이터 가져오기
        # ========================================
        transactions = Transaction.objects.filter(
            user=self.request.user,      # 본인 거래만
            occurred_at__year=year,      # 해당 연도
            occurred_at__month=month     # 해당 월
        )
        
        # ========================================
        # 3. 총 수입 계산
        # ========================================
        total_income = transactions.filter(
            tx_type='IN'  # 입금만
        ).aggregate(
            total=Sum('amount')  # 금액 합계
        )['total'] or 0
        # aggregate: 집계 함수 (SUM, COUNT, AVG 등)
        # ['total']: 결과에서 'total' 키의 값 가져오기
        # or 0: None이면 0으로 처리
        
        # ========================================
        # 4. 총 지출 계산
        # ========================================
        total_expense = transactions.filter(
            tx_type='OUT'  # 출금만
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # ========================================
        # 5. 순합 계산 (수입 - 지출)
        # ========================================
        net_amount = total_income - total_expense
        # 양수: 흑자, 음수: 적자
        
        # ========================================
        # 6. 카테고리별 지출 통계 (Top 5)
        # ========================================
        category_summary = transactions.filter(
            tx_type='OUT'  # 지출만
        ).values(
            'category__name'  # 카테고리 이름
        ).annotate(
            total=Sum('amount'),   # 카테고리별 합계
            count=Count('id')      # 거래 건수
        ).order_by('-total')[:5]   # 금액 많은 순으로 상위 5개
        
        # 결과 예시:
        # [
        #     {'category__name': '식비', 'total': 300000, 'count': 15},
        #     {'category__name': '교통', 'total': 150000, 'count': 8},
        #     ...
        # ]
        
        # ========================================
        # 7. CSS 그래프를 위한 퍼센트 계산
        # ========================================
        # 가장 큰 금액을 100%로 설정
        if category_summary and total_expense > 0:
            max_amount = category_summary[0]['total']
            
            # 각 카테고리의 비율 계산
            for item in category_summary:
                # 막대 그래프 너비 (0-100%)
                item['percentage'] = (item['total'] / max_amount * 100) if max_amount > 0 else 0
                # 전체 지출 대비 비율
                item['expense_ratio'] = (item['total'] / total_expense * 100) if total_expense > 0 else 0
        
        # ========================================
        # 8. 모든 데이터를 context에 담아서 템플릿으로 전달
        # ========================================
        context.update({
            'total_income': total_income,
            'total_expense': total_expense,
            'net_amount': net_amount,
            'category_summary': category_summary,
        })
        
        return context


# ========================================
# 템플릿에서 사용 예시
# ========================================
#
# dashboard.html:
#
# <h2>{{ year }}년 {{ month }}월 요약</h2>
#
# <div>
#     총 수입: {{ total_income|floatformat:0|intcomma }}원
#     총 지출: {{ total_expense|floatformat:0|intcomma }}원
#     순합: {{ net_amount|floatformat:0|intcomma }}원
# </div>
#
# <h3>카테고리별 지출</h3>
# {% for item in category_summary %}
#     <div>
#         {{ item.category__name }}: {{ item.total|floatformat:0 }}원
#         <!-- CSS 막대 그래프 -->
#         <div style="width: {{ item.percentage }}%; background: blue; height: 20px;"></div>
#     </div>
# {% endfor %}
#
# <!-- 월 변경 폼 -->
# <form method="get">
#     <input type="month" name="month" value="{{ year }}-{{ month|stringformat:'02d' }}">
#     <button>조회</button>
# </form>


# ========================================
# 추가 기능 아이디어
# ========================================
#
# 1. 월별 비교
# - 이번 달 vs 지난 달 지출 비교
#
# 2. 계좌별 통계
# - 계좌별 잔액 변화 추이
#
# 3. 일별 통계
# - 날짜별 지출 그래프 (달력 형태)
#
# 4. 예산 관리
# - 카테고리별 예산 설정 및 초과 여부 표시
