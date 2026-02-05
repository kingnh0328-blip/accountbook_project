"""
transactions/admin.py
관리자 페이지 설정 (하이브리드 버전)
- 준호님 코드 + Document 1 코드의 장점 결합
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """카테고리 Admin"""
    
    list_display = ['id', 'name', 'type_badge']  # 뱃지 추가
    list_filter = ['type']
    search_fields = ['name']
    list_per_page = 30
    
    def type_badge(self, obj):
        """유형 뱃지 (색상 표시)"""
        colors = {
            'IN': '#28a745',    # 초록색
            'OUT': '#dc3545',   # 빨간색
            'BOTH': '#6c757d',  # 회색
        }
        color = colors.get(obj.type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = '유형'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """거래 Admin (하이브리드 버전)"""
    
    # 📋 list_display: 준호님 구조 + 내 메서드
    list_display = [
        'id', 
        'occurred_at_short',    # 내 버전: 간결한 날짜
        'user_name',            # 내 버전: 사용자명만
        'account_name',         # 내 버전: 계좌명만
        'type_badge',           # 내 버전: 컬러 뱃지
        'amount_display',       # 둘 다: 금액 (내 버전이 더 화려)
        'category_name',        # 내 버전: 카테고리명만
        'merchant',             # 준호님: 그대로
    ]
    
    # 📝 필터/검색: 준호님 버전 그대로 (더 상세함)
    list_filter = [
        'tx_type',
        'category',
        'occurred_at',
        'created_at',
    ]
    
    search_fields = [
        'user__username',
        'account__name',
        'merchant',
        'memo',
    ]
    
    # 📅 날짜 계층: 준호님 버전
    date_hierarchy = 'occurred_at'
    
    # 🔒 읽기 전용: 준호님 버전
    readonly_fields = ['created_at', 'updated_at']
    
    # 📄 페이지당 항목: 준호님 버전 (30개)
    list_per_page = 30
    
    # 🚀 자동완성: 내 버전 (선택사항)
    autocomplete_fields = ['category']
    
    # 📑 fieldsets: 준호님 버전 (더 상세함)
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'account', 'category')
        }),
        ('거래 정보', {
            'fields': ('tx_type', 'amount', 'occurred_at', 'merchant', 'memo')
        }),
        ('생성/수정 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # ============================================
    # 커스텀 메서드들
    # ============================================
    
    def occurred_at_short(self, obj):
        """거래일시 짧게 (내 버전)"""
        return obj.occurred_at.strftime('%Y-%m-%d %H:%M')
    occurred_at_short.short_description = '거래일시'
    occurred_at_short.admin_order_field = 'occurred_at'
    
    def user_name(self, obj):
        """사용자명 (내 버전)"""
        return obj.user.username
    user_name.short_description = '사용자'
    user_name.admin_order_field = 'user__username'
    
    def account_name(self, obj):
        """계좌명 (내 버전)"""
        return obj.account.name
    account_name.short_description = '계좌'
    account_name.admin_order_field = 'account__name'
    
    def category_name(self, obj):
        """카테고리명 (내 버전)"""
        return obj.category.name if obj.category else '-'
    category_name.short_description = '카테고리'
    
    def type_badge(self, obj):
        """거래유형 뱃지 (내 버전 - 컬러)"""
        color = '#28a745' if obj.tx_type == 'IN' else '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_tx_type_display()
        )
    type_badge.short_description = '유형'
    
    def amount_display(self, obj):
        """금액 표시 (내 버전 - 컬러 + 굵게)"""
        color = '#28a745' if obj.tx_type == 'IN' else '#dc3545'
        sign = '+' if obj.tx_type == 'IN' else '-'
        formatted_amount = f"{sign}{obj.amount:,.0f}원"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            formatted_amount
        )
    amount_display.short_description = '금액'
    amount_display.admin_order_field = 'amount'
    
    # ============================================
    # 권한 & 자동 설정 (내 버전)
    # ============================================
    
    def get_queryset(self, request):
        """
        쿼리셋 최적화 + 권한 제어
        - 슈퍼유저가 아니면 본인 거래만
        """
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'account', 'category')
        
        # 슈퍼유저가 아니면 본인 거래만
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        
        return queryset
    
    def save_model(self, request, obj, form, change):
        """저장 시 user 자동 설정 (새 거래일 때)"""
        if not change:  # 새로 생성할 때만
            if not obj.user_id:
                obj.user = request.user
        super().save_model(request, obj, form, change)


# ============================================
# 버전별 특징 요약
# ============================================
#
# 준호님 버전 장점:
# ✅ 더 상세한 list_filter
# ✅ 더 체계적인 fieldsets
# ✅ date_hierarchy 네비게이션
# ✅ list_per_page 설정
#
# Document 1 버전 장점:
# ✅ 컬러 뱃지 (시각적)
# ✅ 간결한 날짜 표시
# ✅ 권한 제어 (본인 거래만)
# ✅ 자동 user 설정
# ✅ 쿼리 최적화 (select_related)
#
# 하이브리드 버전:
# ✅ 두 버전의 모든 장점 통합!