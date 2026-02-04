"""
고객센터 모델
- 문의(Inquiry): 사용자 문의 내역
- FAQ: 자주하는 질문
"""

from django.db import models
from django.contrib.auth.models import User


class Inquiry(models.Model):
    """
    문의 모델
    - 사용자가 제출한 문의 내역 관리
    """
    STATUS_CHOICES = [
        ('PENDING', '승인'),
        ('IN_PROGRESS', '진행중'),
        ('COMPLETED', '답변완료'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='inquiries',
        null=True,
        blank=True,
        verbose_name='사용자'
    )

    name = models.CharField(max_length=100, verbose_name='이름')
    phone = models.CharField(max_length=20, verbose_name='번호')
    email = models.EmailField(verbose_name='이메일')
    content = models.TextField(verbose_name='문의 내용')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='상태'
    )

    is_read = models.BooleanField(default=False, verbose_name='열람 여부')
    admin_response = models.TextField(blank=True, verbose_name='관리자 답변')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='문의 일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정 일시')

    class Meta:
        verbose_name = '문의'
        verbose_name_plural = '문의 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class FAQ(models.Model):
    """
    자주하는 질문 모델
    """
    question = models.CharField(max_length=200, verbose_name='질문')
    answer = models.TextField(verbose_name='답변')
    order = models.IntegerField(default=0, verbose_name='정렬 순서')
    is_active = models.BooleanField(default=True, verbose_name='활성화')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ 목록'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.question
