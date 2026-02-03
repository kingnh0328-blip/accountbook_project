"""
transactions/tests.py
거래 앱 테스트 - 모델, 폼, 뷰, API
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import json

from .models import Transaction, Category, Attachment
from .forms import TransactionForm, CategoryForm
from accounts.models import Account


# ============================================
# 1. 카테고리 모델 테스트
# ============================================

class CategoryModelTest(TestCase):
    """카테고리 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_category_creation(self):
        """카테고리 생성 테스트"""
        category = Category.objects.create(name='식비', type='OUT')
        self.assertEqual(category.name, '식비')
        self.assertEqual(category.type, 'OUT')

    def test_category_str(self):
        """카테고리 __str__ 테스트"""
        category = Category.objects.create(name='식비', type='OUT')
        self.assertIn('식비', str(category))
        self.assertIn('지출', str(category))

    def test_category_default_type(self):
        """카테고리 기본 타입은 BOTH"""
        category = Category.objects.create(name='기타')
        self.assertEqual(category.type, 'BOTH')

    def test_category_with_user(self):
        """사용자 카테고리 생성"""
        category = Category.objects.create(
            name='취미', type='OUT', user=self.user
        )
        self.assertEqual(category.user, self.user)

    def test_category_without_user(self):
        """공통 카테고리 (user=None)"""
        category = Category.objects.create(name='기타', type='BOTH')
        self.assertIsNone(category.user)


# ============================================
# 2. 거래 모델 테스트
# ============================================

class TransactionModelTest(TestCase):
    """거래 모델 테스트"""

    def setUp(self):
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
        self.category = Category.objects.create(name='식비', type='OUT')

    def test_transaction_creation(self):
        """거래 생성 테스트"""
        tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
            merchant='스타벅스'
        )
        self.assertEqual(tx.user, self.user)
        self.assertEqual(tx.amount, Decimal('5000'))
        self.assertEqual(tx.merchant, '스타벅스')

    def test_transaction_str(self):
        """거래 __str__ 테스트"""
        tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('15000'),
            occurred_at=timezone.now(),
            merchant='스타벅스'
        )
        self.assertIn('스타벅스', str(tx))

    def test_balance_update_on_expense(self):
        """지출 시 계좌 잔액 감소"""
        initial_balance = self.account.balance
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('5000'))

    def test_balance_update_on_income(self):
        """수입 시 계좌 잔액 증가"""
        initial_balance = self.account.balance
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='IN',
            amount=Decimal('50000'),
            occurred_at=timezone.now(),
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('50000'))

    def test_balance_restored_on_delete(self):
        """거래 삭제 시 잔액 복원"""
        tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
        )
        self.account.refresh_from_db()
        balance_after_tx = self.account.balance

        tx.delete()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, balance_after_tx + Decimal('5000'))

    def test_balance_update_on_edit(self):
        """거래 수정 시 잔액 올바르게 업데이트"""
        tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('95000'))

        tx.amount = Decimal('10000')
        tx.save()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('90000'))

    def test_ordering_by_occurred_at(self):
        """최신 거래 순 정렬"""
        tx1 = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('1000'),
            occurred_at=timezone.now() - timezone.timedelta(days=1),
        )
        tx2 = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('2000'),
            occurred_at=timezone.now(),
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0], tx2)


# ============================================
# 3. 폼 테스트
# ============================================

class TransactionFormTest(TestCase):
    """TransactionForm 테스트"""

    def setUp(self):
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
        self.category_in = Category.objects.create(
            name='급여', type='IN', user=self.user
        )
        self.category_out = Category.objects.create(
            name='식비', type='OUT', user=self.user
        )
        self.category_both = Category.objects.create(
            name='이체', type='BOTH', user=self.user
        )

    def test_form_filters_categories_for_income(self):
        """수입 선택 시 IN/BOTH 카테고리만 표시"""
        form = TransactionForm(user=self.user, tx_type='IN')
        category_qs = form.fields['category'].queryset
        self.assertIn(self.category_in, category_qs)
        self.assertIn(self.category_both, category_qs)
        self.assertNotIn(self.category_out, category_qs)

    def test_form_filters_categories_for_expense(self):
        """지출 선택 시 OUT/BOTH 카테고리만 표시"""
        form = TransactionForm(user=self.user, tx_type='OUT')
        category_qs = form.fields['category'].queryset
        self.assertIn(self.category_out, category_qs)
        self.assertIn(self.category_both, category_qs)
        self.assertNotIn(self.category_in, category_qs)

    def test_form_shows_all_categories_without_type(self):
        """타입 미지정 시 전체 카테고리 표시"""
        form = TransactionForm(user=self.user, tx_type=None)
        category_qs = form.fields['category'].queryset
        self.assertIn(self.category_in, category_qs)
        self.assertIn(self.category_out, category_qs)
        self.assertIn(self.category_both, category_qs)

    def test_form_tx_type_choices_restricted_for_income(self):
        """수입 타입 시 tx_type 선택지가 IN만"""
        form = TransactionForm(user=self.user, tx_type='IN')
        choices = form.fields['tx_type'].choices
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0][0], 'IN')

    def test_form_tx_type_choices_restricted_for_expense(self):
        """지출 타입 시 tx_type 선택지가 OUT만"""
        form = TransactionForm(user=self.user, tx_type='OUT')
        choices = form.fields['tx_type'].choices
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0][0], 'OUT')

    def test_form_filters_accounts_to_user(self):
        """본인 계좌만 표시"""
        other_user = User.objects.create_user(
            username='other', password='otherpass123'
        )
        other_account = Account.objects.create(
            user=other_user,
            name='남의 계좌',
            bank_name='신한은행',
            account_number='222-333-444555',
        )
        form = TransactionForm(user=self.user, tx_type=None)
        account_qs = form.fields['account'].queryset
        self.assertIn(self.account, account_qs)
        self.assertNotIn(other_account, account_qs)

    def test_clean_amount_zero(self):
        """금액 0 이하 시 유효성 실패"""
        data = {
            'account': self.account.pk,
            'tx_type': 'OUT',
            'amount': '0',
            'occurred_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        }
        form = TransactionForm(data=data, user=self.user, tx_type='OUT')
        self.assertFalse(form.is_valid())

    def test_clean_amount_too_large(self):
        """금액이 100억 초과 시 유효성 실패"""
        data = {
            'account': self.account.pk,
            'tx_type': 'OUT',
            'amount': '99999999999',
            'occurred_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        }
        form = TransactionForm(data=data, user=self.user, tx_type='OUT')
        self.assertFalse(form.is_valid())


class CategoryFormTest(TestCase):
    """CategoryForm 테스트"""

    def test_valid_category_form(self):
        """정상 카테고리 생성"""
        form = CategoryForm(data={'name': '취미', 'type': 'OUT'})
        self.assertTrue(form.is_valid())

    def test_empty_name(self):
        """카테고리명 비어있으면 실패"""
        form = CategoryForm(data={'name': '', 'type': 'OUT'})
        self.assertFalse(form.is_valid())


# ============================================
# 4. 뷰 테스트
# ============================================

class TransactionViewTest(TestCase):
    """거래 CRUD 뷰 테스트"""

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
            name='테스트계좌',
            bank_name='테스트은행',
            account_number='123-456-789012',
            balance=Decimal('100000')
        )
        self.category = Category.objects.create(name='식비', type='OUT')
        self.client.login(username='testuser', password='testpass123')

    def test_transaction_list_view(self):
        """거래 목록 뷰"""
        response = self.client.get(reverse('transactions:transaction_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaction_list.html')

    def test_transaction_list_login_required(self):
        """비로그인 시 거래 목록 접근 불가"""
        self.client.logout()
        response = self.client.get(reverse('transactions:transaction_list'))
        self.assertEqual(response.status_code, 302)

    def test_transaction_list_shows_only_own(self):
        """본인 거래만 표시"""
        my_tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
            merchant='내거래',
        )
        other_account = Account.objects.create(
            user=self.other_user,
            name='남의계좌',
            bank_name='은행',
            account_number='999-888-777666',
        )
        other_tx = Transaction.objects.create(
            user=self.other_user,
            account=other_account,
            tx_type='OUT',
            amount=Decimal('3000'),
            occurred_at=timezone.now(),
            merchant='남의거래',
        )
        response = self.client.get(reverse('transactions:transaction_list'))
        self.assertContains(response, '내거래')
        self.assertNotContains(response, '남의거래')

    def test_transaction_list_accounts_filter_own_only(self):
        """거래 목록의 계좌 필터에 본인 계좌만 표시"""
        other_account = Account.objects.create(
            user=self.other_user,
            name='남의계좌',
            bank_name='은행',
            account_number='999-888-777666',
        )
        response = self.client.get(reverse('transactions:transaction_list'))
        self.assertContains(response, '테스트계좌')
        self.assertNotContains(response, '남의계좌')

    def test_transaction_create_get(self):
        """거래 생성 폼 페이지"""
        response = self.client.get(reverse('transactions:transaction_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaction_form.html')

    def test_transaction_create_with_type_in(self):
        """수입 타입으로 거래 생성 폼"""
        response = self.client.get(
            reverse('transactions:transaction_create') + '?type=IN'
        )
        self.assertEqual(response.status_code, 200)

    def test_transaction_create_post(self):
        """거래 생성 POST"""
        data = {
            'account': self.account.pk,
            'tx_type': 'OUT',
            'amount': '5000',
            'occurred_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'merchant': '스타벅스',
            'memo': '커피',
        }
        response = self.client.post(
            reverse('transactions:transaction_create'), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 1)
        tx = Transaction.objects.first()
        self.assertEqual(tx.merchant, '스타벅스')
        self.assertEqual(tx.user, self.user)

    def test_transaction_detail(self):
        """거래 상세 조회"""
        tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
        )
        response = self.client.get(
            reverse('transactions:transaction_detail', kwargs={'pk': tx.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_transaction_detail_other_user_404(self):
        """다른 사용자 거래 상세 접근 시 404"""
        other_account = Account.objects.create(
            user=self.other_user,
            name='남의계좌',
            bank_name='은행',
            account_number='999-888-777666',
        )
        other_tx = Transaction.objects.create(
            user=self.other_user,
            account=other_account,
            tx_type='OUT',
            amount=Decimal('3000'),
            occurred_at=timezone.now(),
        )
        response = self.client.get(
            reverse('transactions:transaction_detail', kwargs={'pk': other_tx.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_transaction_update(self):
        """거래 수정"""
        tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
            merchant='원래가게',
        )
        data = {
            'account': self.account.pk,
            'tx_type': 'OUT',
            'amount': '10000',
            'occurred_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'merchant': '수정된가게',
            'memo': '',
        }
        response = self.client.post(
            reverse('transactions:transaction_update', kwargs={'pk': tx.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)
        tx.refresh_from_db()
        self.assertEqual(tx.merchant, '수정된가게')
        self.assertEqual(tx.amount, Decimal('10000'))

    def test_transaction_delete(self):
        """거래 삭제"""
        tx = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
        )
        response = self.client.post(
            reverse('transactions:transaction_delete', kwargs={'pk': tx.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 0)


# ============================================
# 5. 필터링 테스트
# ============================================

class TransactionFilterTest(TestCase):
    """거래 목록 필터링 테스트"""

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

        self.tx_in = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='IN',
            amount=Decimal('50000'),
            occurred_at=timezone.now(),
            merchant='월급',
        )
        self.tx_out = Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=timezone.now(),
            merchant='카페',
            memo='아메리카노',
        )

    def test_filter_by_tx_type_in(self):
        """수입 타입 필터"""
        response = self.client.get(
            reverse('transactions:transaction_list') + '?tx_type=IN'
        )
        self.assertContains(response, '월급')
        self.assertNotContains(response, '카페')

    def test_filter_by_tx_type_out(self):
        """지출 타입 필터"""
        response = self.client.get(
            reverse('transactions:transaction_list') + '?tx_type=OUT'
        )
        self.assertContains(response, '카페')
        self.assertNotContains(response, '월급')

    def test_filter_by_keyword(self):
        """키워드 검색 (메모)"""
        response = self.client.get(
            reverse('transactions:transaction_list') + '?q=아메리카노'
        )
        self.assertContains(response, '카페')
        self.assertNotContains(response, '월급')

    def test_filter_by_keyword_merchant(self):
        """키워드 검색 (가맹점)"""
        response = self.client.get(
            reverse('transactions:transaction_list') + '?q=카페'
        )
        self.assertContains(response, '카페')

    def test_filter_by_date_range_same_day(self):
        """같은 날짜로 기간 필터 (end_date 버그 수정 검증)"""
        today = timezone.localtime().strftime('%Y-%m-%d')
        response = self.client.get(
            reverse('transactions:transaction_list')
            + f'?start_date={today}&end_date={today}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '월급')
        self.assertContains(response, '카페')


# ============================================
# 6. 카테고리 API 테스트
# ============================================

class CategoryByTypeAPITest(TestCase):
    """카테고리 타입별 필터링 API 테스트"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.cat_in = Category.objects.create(
            name='급여', type='IN', user=self.user
        )
        self.cat_out = Category.objects.create(
            name='식비', type='OUT', user=self.user
        )
        self.cat_both = Category.objects.create(
            name='이체', type='BOTH', user=self.user
        )

    def test_api_returns_json(self):
        """API가 JSON 반환"""
        response = self.client.get(
            reverse('transactions:api_categories_by_type') + '?tx_type=IN'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_filter_income(self):
        """수입 타입 필터 시 IN/BOTH만 반환"""
        response = self.client.get(
            reverse('transactions:api_categories_by_type') + '?tx_type=IN'
        )
        data = json.loads(response.content)
        cat_ids = [c['id'] for c in data['categories']]
        self.assertIn(self.cat_in.id, cat_ids)
        self.assertIn(self.cat_both.id, cat_ids)
        self.assertNotIn(self.cat_out.id, cat_ids)

    def test_api_filter_expense(self):
        """지출 타입 필터 시 OUT/BOTH만 반환"""
        response = self.client.get(
            reverse('transactions:api_categories_by_type') + '?tx_type=OUT'
        )
        data = json.loads(response.content)
        cat_ids = [c['id'] for c in data['categories']]
        self.assertIn(self.cat_out.id, cat_ids)
        self.assertIn(self.cat_both.id, cat_ids)
        self.assertNotIn(self.cat_in.id, cat_ids)

    def test_api_no_filter(self):
        """타입 미지정 시 전체 반환"""
        response = self.client.get(
            reverse('transactions:api_categories_by_type')
        )
        data = json.loads(response.content)
        cat_ids = [c['id'] for c in data['categories']]
        self.assertIn(self.cat_in.id, cat_ids)
        self.assertIn(self.cat_out.id, cat_ids)
        self.assertIn(self.cat_both.id, cat_ids)

    def test_api_login_required(self):
        """비로그인 시 API 접근 불가"""
        self.client.logout()
        response = self.client.get(
            reverse('transactions:api_categories_by_type') + '?tx_type=IN'
        )
        self.assertEqual(response.status_code, 302)

    def test_api_excludes_other_users_categories(self):
        """다른 사용자 카테고리 미포함"""
        other_user = User.objects.create_user(
            username='other', password='otherpass123'
        )
        other_cat = Category.objects.create(
            name='남의카테고리', type='IN', user=other_user
        )
        response = self.client.get(
            reverse('transactions:api_categories_by_type') + '?tx_type=IN'
        )
        data = json.loads(response.content)
        cat_ids = [c['id'] for c in data['categories']]
        self.assertNotIn(other_cat.id, cat_ids)


# ============================================
# 7. 카테고리 CRUD 뷰 테스트
# ============================================

class CategoryViewTest(TestCase):
    """카테고리 관리 뷰 테스트"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_category_create(self):
        """카테고리 생성"""
        data = {'name': '취미', 'type': 'OUT'}
        response = self.client.post(
            reverse('transactions:category_create'), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Category.objects.filter(name='취미', user=self.user).exists()
        )

    def test_category_list(self):
        """카테고리 목록 (본인만)"""
        Category.objects.create(name='내카테고리', type='OUT', user=self.user)
        other_user = User.objects.create_user(
            username='other', password='otherpass123'
        )
        Category.objects.create(name='남의카테고리', type='OUT', user=other_user)

        response = self.client.get(reverse('transactions:category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '내카테고리')
        self.assertNotContains(response, '남의카테고리')

    def test_category_delete(self):
        """카테고리 삭제"""
        category = Category.objects.create(
            name='삭제할카테고리', type='OUT', user=self.user
        )
        response = self.client.post(
            reverse('transactions:category_delete', kwargs={'pk': category.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_category_delete_other_user_404(self):
        """다른 사용자 카테고리 삭제 시 404"""
        other_user = User.objects.create_user(
            username='other', password='otherpass123'
        )
        other_cat = Category.objects.create(
            name='남의것', type='OUT', user=other_user
        )
        response = self.client.post(
            reverse('transactions:category_delete', kwargs={'pk': other_cat.pk})
        )
        self.assertEqual(response.status_code, 404)
