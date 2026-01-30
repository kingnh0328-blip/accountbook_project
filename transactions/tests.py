"""
transactions/tests.py
거래 관련 테스트
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import datetime
from .models import Transaction, Category
from accounts.models import Account


class CategoryModelTest(TestCase):
    """카테고리 모델 테스트"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='식비',
            type='OUT'
        )
    
    def test_category_creation(self):
        """카테고리 생성 테스트"""
        self.assertEqual(self.category.name, '식비')
        self.assertEqual(self.category.type, 'OUT')
    
    def test_category_str(self):
        """카테고리 __str__ 테스트"""
        self.assertIn('식비', str(self.category))


class TransactionModelTest(TestCase):
    """거래 모델 테스트"""
    
    def setUp(self):
        # 테스트 유저
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # 테스트 계좌
        self.account = Account.objects.create(
            user=self.user,
            name='테스트계좌',
            bank_name='테스트은행',
            account_number='123-456-789',
            balance=Decimal('100000')
        )
        
        # 테스트 카테고리
        self.category = Category.objects.create(
            name='식비',
            type='OUT'
        )
        
        # 테스트 거래
        self.transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            tx_type='OUT',
            amount=Decimal('5000'),
            occurred_at=datetime.now(),
            merchant='스타벅스'
        )
    
    def test_transaction_creation(self):
        """거래 생성 테스트"""
        self.assertEqual(self.transaction.user, self.user)
        self.assertEqual(self.transaction.account, self.account)
        self.assertEqual(self.transaction.amount, Decimal('5000'))
        self.assertEqual(self.transaction.merchant, '스타벅스')
    
def test_signed_amount(self):
    """부호 포함 금액 테스트"""
    # 지출
    self.assertEqual(self.transaction.signed_amount, Decimal('-5000'))
    
    # 수입
    income = Transaction.objects.create(
        user=self.user,
        account=self.account,
        tx_type='IN',
        amount=Decimal('10000'),
        occurred_at=datetime.now(),
        merchant='월급'
    )
    self.assertEqual(income.signed_amount, Decimal('10000'))
    
    def test_transaction_manager_income(self):
        """수입 필터 테스트"""
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            tx_type='IN',
            amount=Decimal('10000'),
            occurred_at=datetime.now(),
            merchant='월급'
        )
        
        income_count = Transaction.objects.income().count()
        self.assertEqual(income_count, 1)
    
    def test_transaction_manager_expense(self):
        """지출 필터 테스트"""
        expense_count = Transaction.objects.expense().count()
        self.assertEqual(expense_count, 1)


class TransactionViewTest(TestCase):
    """거래 뷰 테스트"""
    
    def setUp(self):
        self.client = Client()
        
        # 테스트 유저
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # 테스트 계좌
        self.account = Account.objects.create(
            user=self.user,
            name='테스트계좌',
            bank_name='테스트은행',
            account_number='123-456-789',
            balance=Decimal('100000')
        )
        
        # 로그인
        self.client.login(username='testuser', password='testpass123')
    
    def test_transaction_list_view(self):
        """거래 목록 뷰 테스트"""
        response = self.client.get(reverse('transactions:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaction_list.html')
    
    def test_transaction_create_view_get(self):
        """거래 생성 폼 테스트"""
        response = self.client.get(reverse('transactions:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaction_form.html')
    
    def test_transaction_create_view_post(self):
        """거래 생성 제출 테스트"""
        data = {
            'account': self.account.id,
            'tx_type': 'OUT',
            'amount': '5000',
            'occurred_at': datetime.now().strftime('%Y-%m-%dT%H:%M'),
            'merchant': '스타벅스',
            'memo': '커피'
        }
        response = self.client.post(reverse('transactions:create'), data)
        
        # 리다이렉트 확인
        self.assertEqual(response.status_code, 302)
        
        # 거래 생성 확인
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.merchant, '스타벅스')
        self.assertEqual(transaction.user, self.user)
    
    def test_login_required(self):
        """로그인 필수 테스트"""
        self.client.logout()
        response = self.client.get(reverse('transactions:list'))
        
        # 로그인 페이지로 리다이렉트
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
