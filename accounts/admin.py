from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """
    계좌 관리자 페이지
    - 목록 표시, 필터, 검색 기능
    - 계좌번호는 마스킹되어 표시
    """
    list_display = [
        'id',
        'user',
        'name',
        'bank_name',
        'masked_account_display',
        'balance',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'bank_name',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'bank_name',
        'user__username',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'masked_account_display',
    ]
    
    list_per_page = 20
    
    def masked_account_display(self, obj):
        """
        계좌번호를 마스킹해서 표시
        """
        return obj.masked_account_number
    masked_account_display.short_description = '계좌번호 (마스킹)'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'name', 'bank_name')
        }),
        ('계좌 정보', {
            'fields': ('account_number', 'masked_account_display', 'balance', 'is_active')
        }),
        ('생성/수정 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # 기본적으로 접혀있음
        }),
    )