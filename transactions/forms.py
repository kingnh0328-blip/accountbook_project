"""
거래 및 첨부파일 폼
- 역할: 거래 생성/수정, 영수증 업로드 폼
- 담당: 팀원 B
"""

from django import forms
from .models import Transaction, Attachment, Category
from accounts.models import Account
from django.core.exceptions import ValidationError
import os


class TransactionForm(forms.ModelForm):
    """
    거래 생성/수정 폼
    """
    
    class Meta:
        model = Transaction
        fields = ['account', 'category', 'tx_type', 'amount', 
                  'occurred_at', 'merchant', 'memo']
        
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tx_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '금액 입력',
                'step': '0.01',
                'min': '0.01'
            }),
            'occurred_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'  # HTML5 날짜/시간 선택기
            }),
            'merchant': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 스타벅스 강남점'
            }),
            'memo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '메모 (선택사항)'
            }),
        }
        
        labels = {
            'account': '계좌',
            'category': '카테고리',
            'tx_type': '거래 타입',
            'amount': '금액',
            'occurred_at': '거래일시',
            'merchant': '가맹점/거래처',
            'memo': '메모',
        }
    
    
    def clean_amount(self):
        """
        금액 유효성 검사
        """
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise ValidationError('금액은 0보다 커야 합니다.')
        
        # 최대 금액 제한 (선택사항)
        if amount > 10000000000:  # 100억
            raise ValidationError('금액이 너무 큽니다. 확인해주세요.')
        
        return amount


class TransactionFilterForm(forms.Form):
    """
    거래 필터링 폼
    - 목록 페이지에서 검색 조건 입력용
    """
    
    account = forms.ModelChoiceField(
        queryset=None,  # 뷰에서 동적으로 설정 (본인 계좌만)
        required=False,
        label='계좌',
        empty_label='전체',  # 선택 안 함 옵션
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='카테고리',
        empty_label='전체',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tx_type = forms.ChoiceField(
        choices=[('', '전체')] + Transaction.TX_TYPE_CHOICES,
        required=False,
        label='거래 타입',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        label='시작일',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        label='종료일',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    q = forms.CharField(
        required=False,
        label='검색',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '메모 또는 가맹점 검색'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        """
        폼 초기화
        - user 파라미터로 본인 계좌만 설정
        """
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(
                user=user,
                is_active=True
            )


class AttachmentForm(forms.ModelForm):
    """
    영수증 파일 업로드 폼
    """
    
    # 허용할 파일 확장자
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']
    
    # 최대 파일 크기 (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 바이트 단위
    
    class Meta:
        model = Attachment
        fields = ['file']
        
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.pdf'  # 브라우저에서 파일 선택 제한
            })
        }
        
        labels = {
            'file': '영수증 파일',
        }
        
        help_texts = {
            'file': 'JPG, PNG, PDF 파일만 업로드 가능 (최대 5MB)',
        }
    
    
    def clean_file(self):
        """
        파일 유효성 검사
        """
        file = self.cleaned_data.get('file')
        
        if not file:
            return file
        
        # 1. 확장자 검사
        ext = os.path.splitext(file.name)[1].lower()
        # os.path.splitext('receipt.jpg') → ('receipt', '.jpg')
        
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f'허용되지 않는 파일 형식입니다. '
                f'({", ".join(self.ALLOWED_EXTENSIONS)} 만 가능)'
            )
        
        # 2. 파일 크기 검사
        if file.size > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(
                f'파일 크기는 {max_size_mb:.0f}MB를 초과할 수 없습니다. '
                f'(현재: {file.size / (1024 * 1024):.1f}MB)'
            )
        
        # 3. 파일 내용 검증 (선택사항)
        # 실제로 이미지 파일인지 확인
        if ext in ['.jpg', '.jpeg', '.png']:
            try:
                from PIL import Image
                Image.open(file).verify()
                file.seek(0)  # 파일 포인터 초기화
            except:
                raise ValidationError('유효하지 않은 이미지 파일입니다.')
        
        return file


# ========================================
# 템플릿 사용 예시
# ========================================
#
# 1. 거래 생성 폼:
# <form method="post">
#     {% csrf_token %}
#     {{ form.as_p }}
#     <button>저장</button>
# </form>
#
# 2. 필터링 폼:
# <form method="get">
#     {{ filter_form.as_p }}
#     <button>검색</button>
# </form>
#
# 3. 파일 업로드 폼:
# <form method="post" enctype="multipart/form-data">
#     {% csrf_token %}
#     {{ form.as_p }}
#     <button>업로드</button>
# </form>
# 
# 주의: 파일 업로드 시 enctype="multipart/form-data" 필수!