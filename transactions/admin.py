"""
transactions/admin.py
관리자 페이지 설정
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Transaction



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """카테고리 Admin"""
    
    list_display = ['id', 'name', 'type_badge']
    search_fields = ['name']
    
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
    """거래 Admin"""
    
    list_display = [
        'id', 'occurred_at_short', 'user_name', 'account_name',
        'merchant', 'type_badge', 'amount_display', 'category_name'
    ]
    list_filter = ['tx_type', 'category', 'occurred_at', 'created_at']
    search_fields = ['merchant', 'memo', 'user__username', 'account__name']
    date_hierarchy = 'occurred_at'
    autocomplete_fields = ['category']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('거래 정보', {
            'fields': ('user', 'account', 'tx_type', 'amount', 'occurred_at')
        }),
        ('상세 정보', {
            'fields': ('category', 'merchant', 'memo')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def occurred_at_short(self, obj):
        """거래일시 짧게"""
        return obj.occurred_at.strftime('%Y-%m-%d %H:%M')
    occurred_at_short.short_description = '거래일시'
    occurred_at_short.admin_order_field = 'occurred_at'
    
    def user_name(self, obj):
        """사용자명"""
        return obj.user.username
    user_name.short_description = '사용자'
    user_name.admin_order_field = 'user__username'
    
    def account_name(self, obj):
        """계좌명"""
        return obj.account.name
    account_name.short_description = '계좌'
    account_name.admin_order_field = 'account__name'
    
    def category_name(self, obj):
        """카테고리명"""
        return obj.category.name if obj.category else '-'
    category_name.short_description = '카테고리'
    
    def type_badge(self, obj):
        """거래유형 뱃지"""
        color = '#28a745' if obj.tx_type == 'IN' else '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_tx_type_display()
        )
    type_badge.short_description = '유형'
    
    def amount_display(self, obj):
        """금액 표시 (색상 포함)"""
        color = '#28a745' if obj.tx_type == 'IN' else '#dc3545'
        sign = '+' if obj.tx_type == 'IN' else '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{:,.0f}원</span>',
            color,
            sign,
            obj.amount
        )
    amount_display.short_description = '금액'
    amount_display.admin_order_field = 'amount'
    
    def get_queryset(self, request):
        """쿼리셋 최적화"""
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
