"""
dashboard/tests.py
대시보드 앱 테스트 - 뷰, 통계, 권한
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from accounts.models import Account
from transactions.models import Transaction, Category


class DashboardViewTest(TestCase):
    """대시보드 뷰 테스트"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='테스트계좌',
            bank_name='테스트은행',
            account_number='123-456-789012',
            balance=Decimal('100000')
        )
        self.client.login(username='testuser', password='testpass123')

    def test_dashboard_login_required(self):
        """비로그인 시 대시보드 접근 불가"""
        self.client.logout()
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_with_account(self):
        """계좌가 있을 때 대시보드 정상 표시"""
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')

    def test_dashboard_without_account(self):
        """계좌가 없을 때 계좌 생성 안내 페이지"""
        self.account.is_active = False
        self.account.save()
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/make_your_account.html')

    def test_dashboard_shows_income_expense(self):
        """대시보드에 수입/지출 통계 표시"""
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='IN',
            amount=Decimal('50000'),
            occurred_at=timezone.now(),
        )
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('10000'),
            occurred_at=timezone.now(),
        )
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_income'], Decimal('50000'))
        self.assertEqual(response.context['total_expense'], Decimal('10000'))

    def test_dashboard_month_filter(self):
        """월별 필터링"""
        response = self.client.get(
            reverse('dashboard:dashboard') + '?month=2026-01'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['year'], 2026)
        self.assertEqual(response.context['month'], 1)

    def test_dashboard_invalid_month_param(self):
        """잘못된 월 파라미터 시 현재 월 사용"""
        response = self.client.get(
            reverse('dashboard:dashboard') + '?month=invalid'
        )
        self.assertEqual(response.status_code, 200)
        now = timezone.now()
        self.assertEqual(response.context['year'], now.year)
        self.assertEqual(response.context['month'], now.month)

    def test_dashboard_account_filter(self):
        """계좌 필터링"""
        response = self.client.get(
            reverse('dashboard:dashboard') + f'?account={self.account.pk}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['selected_account_id'],
            str(self.account.pk)
        )

    def test_dashboard_category_summary(self):
        """카테고리별 지출 통계"""
        category = Category.objects.create(name='식비', type='OUT')
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=category,
            tx_type='OUT',
            amount=Decimal('15000'),
            occurred_at=timezone.now(),
        )
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        summary = response.context['category_summary']
        self.assertTrue(len(summary) > 0)

    def test_dashboard_recent_transactions(self):
        """최근 거래 표시"""
        for i in range(5):
            Transaction.objects.create(
                user=self.user,
                account=self.account,
                tx_type='OUT',
                amount=Decimal('1000'),
                occurred_at=timezone.now(),
            )
        response = self.client.get(reverse('dashboard:dashboard'))
        # 최대 4개만 표시
        self.assertTrue(len(response.context['recent_transactions']) <= 4)

    def test_dashboard_other_user_data_hidden(self):
        """다른 사용자 데이터 미포함"""
        other_user = User.objects.create_user(
            username='other', password='otherpass123'
        )
        other_account = Account.objects.create(
            user=other_user,
            name='남의계좌',
            bank_name='은행',
            account_number='999-888-777666',
        )
        Transaction.objects.create(
            user=other_user,
            account=other_account,
            tx_type='IN',
            amount=Decimal('999999'),
            occurred_at=timezone.now(),
        )
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.context['total_income'], 0)
