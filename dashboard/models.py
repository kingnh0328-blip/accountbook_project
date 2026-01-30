# dashboard/models.py
"""
대시보드 모델
담당: 팀원 C

Note: Attachment 모델은 transactions 앱에서 관리합니다.
      dashboard에서는 transactions.models.Attachment를 import하여 사용합니다.
      
협업 완료:
- 팀원 B: transactions.Attachment 모델 제공 및 메서드 추가 확인
"""

from django.db import models

# Create your models here.

# Attachment 모델은 transactions.models.Attachment를 사용합니다.
# dashboard/views.py, dashboard/forms.py, dashboard/admin.py에서
# from transactions.models import Attachment로 import하여 사용