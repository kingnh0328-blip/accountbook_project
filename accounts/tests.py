"""
accounts/tests.py
계좌 앱 테스트 - 모델, 폼, 뷰
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal

from .models import Account
from .forms import AccountForm


# ============================================
# 1. 모델 테스트
# ============================================

class AccountModelTest(TestCase):
    """Account 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='생활비 통장',
            bank_name='국민은행',
            account_number='110-123-456789',
            balance=Decimal('100000.00')
        )

    def test_account_creation(self):
        """계좌 생성 확인"""
        self.assertEqual(self.account.name, '생활비 통장')
        self.assertEqual(self.account.bank_name, '국민은행')
        self.assertEqual(self.account.balance, Decimal('100000.00'))
        self.assertTrue(self.account.is_active)

    def test_account_str(self):
        """__str__ 반환값 확인"""
        self.assertEqual(str(self.account), '생활비 통장 (국민은행)')

    def test_masked_account_number_with_hyphens(self):
        """하이픈 포함 계좌번호 마스킹"""
        self.assertEqual(self.account.masked_account_number, '110-***-6789')

    def test_masked_account_number_without_hyphens(self):
        """하이픈 없는 계좌번호 마스킹"""
        self.account.account_number = '1101234567890'
        self.assertEqual(self.account.masked_account_number, '110***7890')

    def test_masked_account_number_empty(self):
        """빈 계좌번호 마스킹"""
        self.account.account_number = ''
        self.assertEqual(self.account.masked_account_number, '')

    def test_default_balance(self):
        """잔액 기본값 0"""
        account = Account.objects.create(
            user=self.user,
            name='새 계좌',
            bank_name='신한은행',
            account_number='110-999-888777'
        )
        self.assertEqual(account.balance, Decimal('0'))

    def test_ordering(self):
        """최신 생성 순 정렬"""
        account2 = Account.objects.create(
            user=self.user,
            name='두번째 계좌',
            bank_name='신한은행',
            account_number='222-333-444555'
        )
        accounts = Account.objects.all()
        self.assertEqual(accounts[0], account2)


# ============================================
# 2. 폼 테스트
# ============================================

class AccountFormTest(TestCase):
    """AccountForm 유효성 검사 테스트"""

    def test_valid_form(self):
        """정상 데이터"""
        data = {
            'name': '테스트 계좌',
            'bank_name': '국민은행',
            'account_number': '110-123-456789',
            'balance': '50000',
        }
        form = AccountForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_account_number_special_chars(self):
        """계좌번호에 특수문자 포함 시 실패"""
        data = {
            'name': '테스트 계좌',
            'bank_name': '국민은행',
            'account_number': '110@123#456',
            'balance': '50000',
        }
        form = AccountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('account_number', form.errors)

    def test_invalid_account_number_too_short(self):
        """계좌번호 8자리 미만 시 실패"""
        data = {
            'name': '테스트 계좌',
            'bank_name': '국민은행',
            'account_number': '12-34',
            'balance': '50000',
        }
        form = AccountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('account_number', form.errors)

    def test_negative_balance(self):
        """음수 잔액 시 실패"""
        data = {
            'name': '테스트 계좌',
            'bank_name': '국민은행',
            'account_number': '110-123-456789',
            'balance': '-1000',
        }
        form = AccountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('balance', form.errors)


# ============================================
# 3. 뷰 테스트
# ============================================

class AuthViewTest(TestCase):
    """인증 뷰 테스트"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_home_redirects_to_login(self):
        """비로그인 시 홈에서 로그인 페이지로 리다이렉트"""
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_home_redirects_to_dashboard(self):
        """로그인 시 홈에서 대시보드로 리다이렉트"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/', response.url)

    def test_signup_page(self):
        """회원가입 페이지 접근"""
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')

    def test_signup_post(self):
        """회원가입 POST"""
        data = {
            'username': 'newuser',
            'password1': 'complexPass!123',
            'password2': 'complexPass!123',
        }
        response = self.client.post(reverse('accounts:signup'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_page(self):
        """로그인 페이지 접근"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_post(self):
        """로그인 POST"""
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(reverse('accounts:login'), data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/', response.url)

    def test_logout(self):
        """로그아웃"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)


class AccountViewTest(TestCase):
    """계좌 CRUD 뷰 테스트"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', password='otherpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='내 계좌',
            bank_name='국민은행',
            account_number='110-123-456789',
            balance=Decimal('100000')
        )
        self.other_account = Account.objects.create(
            user=self.other_user,
            name='남의 계좌',
            bank_name='신한은행',
            account_number='222-333-444555',
            balance=Decimal('500000')
        )
        self.client.login(username='testuser', password='testpass123')

    def test_account_list_login_required(self):
        """비로그인 시 계좌 목록 접근 불가"""
        self.client.logout()
        response = self.client.get(reverse('accounts:account_list'))
        self.assertEqual(response.status_code, 302)

    def test_account_list_shows_only_own_accounts(self):
        """계좌 목록에 본인 계좌만 표시"""
        response = self.client.get(reverse('accounts:account_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '내 계좌')
        self.assertNotContains(response, '남의 계좌')

    def test_account_create(self):
        """계좌 생성"""
        data = {
            'name': '새 계좌',
            'bank_name': '우리은행',
            'account_number': '333-444-555666',
            'balance': '0',
        }
        response = self.client.post(reverse('accounts:account_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Account.objects.filter(name='새 계좌', user=self.user).exists()
        )

    def test_account_detail(self):
        """계좌 상세 조회"""
        response = self.client.get(
            reverse('accounts:account_detail', kwargs={'pk': self.account.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_account_detail_other_user_404(self):
        """다른 사용자 계좌 조회 시 404"""
        response = self.client.get(
            reverse('accounts:account_detail', kwargs={'pk': self.other_account.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_account_update(self):
        """계좌 수정"""
        data = {
            'name': '수정된 계좌',
            'bank_name': '국민은행',
            'account_number': '110-123-456789',
            'balance': '200000',
        }
        response = self.client.post(
            reverse('accounts:account_update', kwargs={'pk': self.account.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)
        self.account.refresh_from_db()
        self.assertEqual(self.account.name, '수정된 계좌')

    def test_account_delete_soft_delete(self):
        """계좌 삭제 시 소프트 삭제(비활성화)"""
        response = self.client.post(
            reverse('accounts:account_delete', kwargs={'pk': self.account.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.account.refresh_from_db()
        self.assertFalse(self.account.is_active)

    def test_account_delete_other_user_404(self):
        """다른 사용자 계좌 삭제 시 404"""
        response = self.client.post(
            reverse('accounts:account_delete', kwargs={'pk': self.other_account.pk})
        )
        self.assertEqual(response.status_code, 404)
