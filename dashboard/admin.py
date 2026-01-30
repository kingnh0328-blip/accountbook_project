# dashboard/admin.py
"""
대시보드 관리자 페이지
팀원 A 제공
transactions.Attachment 사용
"""

from django.contrib import admin
from django.utils.html import format_html
from transactions.models import Attachment  # ← 변경!


@admin.register(Attachment)
class DashboardAttachmentAdmin(admin.ModelAdmin):  # ← 클래스명 변경 (충돌 방지)
    """
    영수증 첨부파일 관리자 페이지
    - 업로드된 영수증 파일 관리
    """
    list_display = [
        'id',
        'user',
        'transaction',
        'original_name',
        'file_type_display',
        'size_display',
        'file_preview',
        'uploaded_at',
    ]

    list_filter = [
        'uploaded_at',
        'content_type',
    ]

    search_fields = [
        'user__username',
        'transaction__merchant',
        'original_name',
    ]

    readonly_fields = [
        'uploaded_at',
        'size',
        'content_type',
        'file_preview',
    ]

    list_per_page = 20

    def file_type_display(self, obj):
        """
        파일 타입 표시 (이미지/PDF)
        """
        if obj.is_image():
            return '🖼️ 이미지'
        elif obj.is_pdf():
            return '📄 PDF'
        return '📎 파일'
    file_type_display.short_description = '파일 타입'

    def size_display(self, obj):
        """
        파일 크기를 읽기 쉽게 표시
        """
        size_bytes = obj.size
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
    size_display.short_description = '파일 크기'

    def file_preview(self, obj):
        """
        파일 미리보기 (이미지인 경우)
        """
        if obj.is_image():
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />'
                '</a>',
                obj.file.url,
                obj.file.url
            )
        elif obj.is_pdf():
            return format_html(
                '<a href="{}" target="_blank">PDF 보기</a>',
                obj.file.url
            )
        return '-'
    file_preview.short_description = '미리보기'

    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'transaction')
        }),
        ('파일 정보', {
            'fields': ('file', 'original_name', 'size', 'content_type', 'file_preview')
        }),
        ('업로드 정보', {
            'fields': ('uploaded_at',),
        }),
    )