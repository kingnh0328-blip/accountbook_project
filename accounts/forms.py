"""
계좌 관련 폼
- 역할: 계좌 생성/수정 시 사용하는 입력 폼
- 담당: 팀원 A
"""

from django import forms
from .models import Account
from django.core.exceptions import ValidationError


class AccountForm(forms.ModelForm):
    """
    계좌 생성/수정 폼
    - Django ModelForm: 모델과 자동으로 연결되는 폼
    """
    
    class Meta:
        model = Account  # 연결할 모델
        
        # 폼에 표시할 필드들 (user는 자동으로 설정되므로 제외)
        fields = ['name', 'bank_name', 'account_number', 'balance']
        
        # 각 필드의 HTML input 설정
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',           # Bootstrap CSS 클래스
                'placeholder': '예: 생활비 통장',
                'maxlength': '100'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 국민은행',
                'maxlength': '50'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 110-123-456789',
                'maxlength': '50'
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '0.01',                    # 소수점 입력 가능
                'min': '0'
            }),
        }
        
        # 폼 레이블 (한글로 표시)
        labels = {
            'name': '계좌명',
            'bank_name': '은행명',
            'account_number': '계좌번호',
            'balance': '초기 잔액',
        }
        
        # 도움말 텍스트
        help_texts = {
            'account_number': '하이픈(-)을 포함하여 입력하세요. 예: 110-123-456789',
            'balance': '계좌의 현재 잔액을 입력하세요.',
        }
    
    
    def clean_account_number(self):
        """
        계좌번호 유효성 검사
        - 폼 제출 시 자동으로 실행됨
        """
        account_number = self.cleaned_data.get('account_number')
        
        # 숫자와 하이픈만 허용
        if not all(c.isdigit() or c == '-' for c in account_number):
            raise ValidationError('계좌번호는 숫자와 하이픈(-)만 입력 가능합니다.')
        
        # 최소 길이 확인
        if len(account_number.replace('-', '')) < 8:
            raise ValidationError('계좌번호는 최소 8자리 이상이어야 합니다.')
        
        return account_number
    
    
    def clean_balance(self):
        """
        잔액 유효성 검사
        """
        balance = self.cleaned_data.get('balance')
        
        # 음수 불가
        if balance < 0:
            raise ValidationError('잔액은 0 이상이어야 합니다.')
        
        return balance


# ========================================
# 폼 사용 예시 (뷰에서)
# ========================================
#
# views.py:
# class AccountCreateView(CreateView):
#     form_class = AccountForm
#     ...
#
# 템플릿에서:
# <form method="post">
#     {% csrf_token %}
#     {{ form.as_p }}
#     <button>저장</button>
# </form>
#
# 또는 개별 필드:
# <form method="post">
#     {% csrf_token %}
#     
#     <label>{{ form.name.label }}</label>
#     {{ form.name }}
#     {% if form.name.errors %}
#         <span>{{ form.name.errors }}</span>
#     {% endif %}
#     
#     <button>저장</button>
# </form>


# ========================================
# widgets 속성 설명
# ========================================
#
# widgets: HTML input 태그를 어떻게 렌더링할지 설정
#
# TextInput: <input type="text">
# NumberInput: <input type="number">
# EmailInput: <input type="email">
# PasswordInput: <input type="password">
# Textarea: <textarea>
# Select: <select><option></select>
# CheckboxInput: <input type="checkbox">
# DateInput: <input type="date">
#
# attrs: HTML 속성 (class, placeholder, maxlength 등)