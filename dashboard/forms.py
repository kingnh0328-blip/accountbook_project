# dashboard/forms.py
"""
대시보드 폼
담당: 팀원 C
"""

from django import forms
from .models import Attachment


class AttachmentForm(forms.ModelForm):
    """
    영수증 업로드 폼
    - 파일 필드만 (user, transaction은 뷰에서 자동 설정)
    """
    class Meta:
        model = Attachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.pdf'  # 허용 확장자 제한
            })
        }
        labels = {
            'file': '영수증 파일'
        }
        help_texts = {
            'file': '지원 형식: JPG, PNG, PDF (최대 5MB)'
        }