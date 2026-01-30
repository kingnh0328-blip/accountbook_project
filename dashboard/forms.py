# dashboard/forms.py
"""
대시보드 폼
담당: 팀원 C
transactions.Attachment 사용
"""

from django import forms
from transactions.models import Attachment  # ← 변경!


class AttachmentForm(forms.ModelForm):
    """
    영수증 업로드 폼
    - 파일 필드만 포함
    - 확장자 제한: .jpg, .jpeg, .png, .pdf
    """
    class Meta:
        model = Attachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'accept': '.jpg,.jpeg,.png,.pdf',
                'class': 'form-control'
            })
        }
        labels = {
            'file': '영수증 파일'
        }
        help_texts = {
            'file': '허용 형식: JPG, PNG, PDF (최대 5MB)'
        }