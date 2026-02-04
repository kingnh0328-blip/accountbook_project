"""
고객센터 폼
"""

from django import forms
from .models import Inquiry


class InquiryForm(forms.ModelForm):
    """
    문의 작성 폼
    """
    class Meta:
        model = Inquiry
        fields = ['name', 'phone', 'email', 'content']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '이름을 입력하세요'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '연락처를 입력하세요'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '이메일을 입력하세요'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '문의 내용을 입력하세요',
                'rows': 5
            }),
        }
        labels = {
            'name': '이름',
            'phone': '연락처',
            'email': '이메일',
            'content': '문의 내용'
        }
