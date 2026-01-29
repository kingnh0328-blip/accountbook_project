"""
계좌(Account) 모델 정의
- 역할: 사용자의 계좌 정보(통장, 카드, 현금) 관리
- 담당: 팀원 A
"""

from django.db import models
from django.contrib.auth.models import User  # Django 기본 User 모델 사용


class Account(models.Model):
    """
    계좌 모델
    - 사용자가 보유한 계좌 정보를 저장
    - 거래(Transaction)가 발생하는 기준 단위
    """
    
    # 1. 관계 필드: 누구의 계좌인가?
    user = models.ForeignKey(
        User,                           # Django 기본 User 모델과 연결
        on_delete=models.CASCADE,       # 사용자 삭제 시 계좌도 함께 삭제
        related_name='accounts'         # user.accounts.all()로 사용자의 모든 계좌 조회 가능
    )
    
    # 2. 기본 정보 필드
    name = models.CharField(
        max_length=100,                 # 최대 100자
        verbose_name='계좌명'           # Admin 페이지에 표시될 이름
    )
    # 예: "생활비 통장", "카드 1", "비상금 통장"
    
    bank_name = models.CharField(
        max_length=50,
        verbose_name='은행명'
    )
    # 예: "국민은행", "신한카드", "현금"
    
    account_number = models.CharField(
        max_length=50,
        verbose_name='계좌번호'
    )
    # 예: "110-123-456789"
    # 주의: 화면에 출력할 때는 반드시 마스킹 처리!
    
    # 3. 잔액 정보
    balance = models.DecimalField(
        max_digits=12,                  # 총 자릿수 (예: 1,000,000,000원까지)
        decimal_places=2,               # 소수점 자릿수 (예: 1000.50원)
        default=0,
        verbose_name='잔액'
    )
    
    # 4. 활성화 상태
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 여부'
    )
    # True: 사용 중, False: 비활성 (삭제 대신 숨김 처리)
    
    # 5. 자동 생성 필드
    created_at = models.DateTimeField(auto_now_add=True)  # 계좌 생성 시간 (자동)
    updated_at = models.DateTimeField(auto_now=True)      # 계좌 수정 시간 (자동)
    
    
    class Meta:
        """모델 메타 정보"""
        ordering = ['-created_at']          # 최신 생성 순으로 정렬
        verbose_name = '계좌'               # Admin 단수형 이름
        verbose_name_plural = '계좌 목록'   # Admin 복수형 이름
    
    
    def __str__(self):
        """
        객체를 문자열로 표현 (Admin, Shell에서 보이는 이름)
        예: "생활비 통장 (국민은행)"
        """
        return f"{self.name} ({self.bank_name})"
    
    
    @property
    def masked_account_number(self):
        """
        계좌번호 마스킹 처리
        - 보안을 위해 중간 부분을 ***로 가림
        - 예: 110-123-456789 → 110-***-6789
        """
        if not self.account_number:
            return ""
        
        # 하이픈 기준으로 분리
        parts = self.account_number.split('-')
        
        if len(parts) >= 3:
            # 예: ['110', '123', '456789']
            # 중간 부분을 *** 처리, 마지막 4자리만 표시
            return f"{parts[0]}-***-{parts[-1][-4:]}"
        
        elif len(self.account_number) > 8:
            # 하이픈이 없는 경우: 앞 3자리 + *** + 뒤 4자리
            return f"{self.account_number[:3]}***{self.account_number[-4:]}"
        
        else:
            # 너무 짧은 경우
            return "***" + self.account_number[-4:] if len(self.account_number) > 4 else "***"


# 사용 예시:
# account = Account.objects.get(id=1)
# print(account.account_number)         # 110-123-456789 (실제 번호)
# print(account.masked_account_number)  # 110-***-6789 (마스킹된 번호)