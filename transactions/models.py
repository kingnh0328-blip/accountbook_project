"""
거래(Transaction) 및 첨부파일(Attachment) 모델 정의
- 역할: 입출금 거래 내역 및 영수증 관리
- 담당: 팀원 B
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """
    카테고리 모델
    - 거래를 분류하기 위한 기준 (식비, 교통, 월세, 급여 등)
    - 관리자가 미리 만들어두거나 초기 데이터로 제공
    """
    
    TYPE_CHOICES = [
        ('IN', '수입'),      # 입금 전용
        ('OUT', '지출'),     # 출금 전용
        ('BOTH', '공통'),    # 입금/출금 둘 다 사용 가능
    ]
    
    name = models.CharField(
        max_length=50,
        verbose_name='카테고리명'
    )
    # 예: "식비", "교통", "월세", "급여", "용돈"
    
    type = models.CharField(
        max_length=4,
        choices=TYPE_CHOICES,
        default='BOTH',
        verbose_name='타입'
    )
    
    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리 목록'
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    """
    거래 내역 모델
    - 계좌에서 발생한 입금/출금 기록
    - 프로젝트의 핵심 비즈니스 데이터
    """
    
    # 거래 타입 선택지
    TX_TYPE_CHOICES = [
        ('IN', '입금'),
        ('OUT', '출금'),
    ]
    
    # 1. 관계 필드: 누가, 어느 계좌에서, 어떤 카테고리로?
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='사용자'
    )
    # 누구의 거래인지 (권한 체크용)
    
    account = models.ForeignKey(
        'accounts.Account',              # accounts 앱의 Account 모델 참조
        on_delete=models.CASCADE,        # 계좌 삭제 시 거래도 함께 삭제
        related_name='transactions',
        verbose_name='계좌'
    )
    # 어느 계좌에서 발생한 거래인지
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,       # 카테고리 삭제 시 NULL로 설정 (거래는 유지)
        null=True,                       # NULL 허용 (카테고리 없어도 됨)
        blank=True,                      # 폼에서 비워둘 수 있음
        related_name='transactions',
        verbose_name='카테고리'
    )
    
    # 2. 거래 정보
    tx_type = models.CharField(
        max_length=3,
        choices=TX_TYPE_CHOICES,
        verbose_name='거래 타입'
    )
    # 'IN' 또는 'OUT'
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],  # 최소 0.01원 이상
        verbose_name='금액'
    )
    # 거래 금액 (음수 불가)
    
    occurred_at = models.DateTimeField(
        verbose_name='거래일시'
    )
    # 실제 거래가 발생한 날짜와 시간
    
    # 3. 추가 정보 (선택사항)
    merchant = models.CharField(
        max_length=100,
        blank=True,                      # 비워둘 수 있음
        verbose_name='가맹점/거래처'
    )
    # 예: "스타벅스 강남점", "쿠팡", "월급", "용돈"
    
    memo = models.TextField(
        blank=True,
        verbose_name='메모'
    )
    # 거래에 대한 추가 메모
    
    # 4. 자동 생성 필드
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        ordering = ['-occurred_at']      # 최신 거래 순으로 정렬
        verbose_name = '거래 내역'
        verbose_name_plural = '거래 내역 목록'
        
        indexes = [
            models.Index(fields=['-occurred_at']),  # 거래일 기준 조회 최적화
        ]
    
    
    def __str__(self):
        """
        예: "출금 15,000원 - 스타벅스"
        """
        return f"{self.get_tx_type_display()} {self.amount:,.0f}원 - {self.merchant or '메모 없음'}"


class Attachment(models.Model):
    """
    영수증/첨부파일 모델
    - 거래에 첨부되는 영수증 이미지 또는 PDF 파일
    - 파일 자체는 MEDIA 폴더에 저장, DB에는 경로만 저장
    """
    
    # 1. 관계 필드
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='사용자'
    )
    
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,        # 거래 삭제 시 첨부파일도 삭제
        related_name='attachment',       # transaction.attachment로 접근
        verbose_name='거래'
    )
    # OneToOneField: 거래당 1개의 영수증만 첨부 가능
    
    # 2. 파일 정보
    file = models.FileField(
        upload_to='receipts/%Y/%m/%d/',  # 업로드 경로: media/receipts/2026/01/29/
        verbose_name='파일'
    )
    
    original_name = models.CharField(
        max_length=255,
        verbose_name='원본 파일명'
    )
    # 사용자가 업로드한 원래 파일 이름
    
    size = models.IntegerField(
        verbose_name='파일 크기(bytes)'
    )
    # 파일 크기 (바이트 단위)
    
    content_type = models.CharField(
        max_length=100,
        verbose_name='파일 타입'
    )
    # 예: "image/jpeg", "image/png", "application/pdf"
    
    # 3. 자동 생성 필드
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        verbose_name = '첨부파일'
        verbose_name_plural = '첨부파일 목록'
    
    
    def __str__(self):
        return f"{self.transaction} - {self.original_name}"
    
    
    def delete(self, *args, **kwargs):
        """
        모델 삭제 시 실제 파일도 함께 삭제
        - DB 레코드만 삭제되고 파일이 남지 않도록
        """
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)


# 사용 예시:
# 
# # 거래 생성
# transaction = Transaction.objects.create(
#     user=request.user,
#     account=my_account,
#     category=food_category,
#     tx_type='OUT',
#     amount=15000,
#     occurred_at=timezone.now(),
#     merchant='스타벅스',
#     memo='아메리카노 2잔'
# )
#
# # 영수증 첨부
# attachment = Attachment.objects.create(
#     user=request.user,
#     transaction=transaction,
#     file=uploaded_file,
#     original_name=uploaded_file.name,
#     size=uploaded_file.size,
#     content_type=uploaded_file.content_type
# )
#
# # 거래의 영수증 조회
# if hasattr(transaction, 'attachment'):
#     print(transaction.attachment.file.url)