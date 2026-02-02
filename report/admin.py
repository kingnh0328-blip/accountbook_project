"""
고객센터 관리자 설정
"""

from django.contrib import admin
from .models import Inquiry, FAQ


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """
    문의 관리자
    """
    list_display = ['name', 'email', 'status', 'is_read', 'created_at']
    list_filter = ['status', 'is_read', 'created_at']
    search_fields = ['name', 'email', 'content']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('문의 정보', {
            'fields': ('user', 'name', 'phone', 'email', 'content')
        }),
        ('관리', {
            'fields': ('status', 'is_read', 'admin_response')
        }),
        ('기타', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """관리자가 저장할 때 자동으로 열람 표시"""
        if change:  # 수정할 때만
            obj.is_read = True
        super().save_model(request, obj, form, change)

    actions = ['mark_as_pending', 'mark_as_in_progress', 'mark_as_completed']

    def mark_as_pending(self, request, queryset):
        queryset.update(status='PENDING')
    mark_as_pending.short_description = '선택된 문의를 "승인"으로 변경'

    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='IN_PROGRESS')
    mark_as_in_progress.short_description = '선택된 문의를 "진행중"으로 변경'

    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
    mark_as_completed.short_description = '선택된 문의를 "답변완료"로 변경'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """
    FAQ 관리자
    """
    list_display = ['question', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
