"""
report/tests.py
고객센터 앱 테스트 - 모델, 폼, 뷰
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Inquiry, FAQ
from .forms import InquiryForm


# ============================================
# 1. 모델 테스트
# ============================================

class InquiryModelTest(TestCase):
    """Inquiry 모델 테스트"""

    def test_inquiry_creation(self):
        """문의 생성"""
        inquiry = Inquiry.objects.create(
            name='홍길동',
            phone='010-1234-5678',
            email='hong@test.com',
            content='계좌 관련 문의입니다.'
        )
        self.assertEqual(inquiry.name, '홍길동')
        self.assertEqual(inquiry.status, 'PENDING')
        self.assertFalse(inquiry.is_read)

    def test_inquiry_str(self):
        """Inquiry __str__"""
        inquiry = Inquiry.objects.create(
            name='홍길동',
            phone='010-1234-5678',
            email='hong@test.com',
            content='문의'
        )
        self.assertIn('홍길동', str(inquiry))

    def test_inquiry_with_user(self):
        """로그인 사용자 문의"""
        user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        inquiry = Inquiry.objects.create(
            user=user,
            name='테스트유저',
            phone='010-1111-2222',
            email='test@test.com',
            content='문의'
        )
        self.assertEqual(inquiry.user, user)

    def test_inquiry_without_user(self):
        """비로그인 사용자 문의 (user=None)"""
        inquiry = Inquiry.objects.create(
            name='비회원',
            phone='010-9999-8888',
            email='anon@test.com',
            content='문의'
        )
        self.assertIsNone(inquiry.user)

    def test_inquiry_ordering(self):
        """최신 문의 순 정렬"""
        inquiry1 = Inquiry.objects.create(
            name='첫번째', phone='010', email='a@a.com', content='1'
        )
        inquiry2 = Inquiry.objects.create(
            name='두번째', phone='010', email='b@b.com', content='2'
        )
        inquiries = Inquiry.objects.all()
        self.assertEqual(inquiries[0], inquiry2)


class FAQModelTest(TestCase):
    """FAQ 모델 테스트"""

    def test_faq_creation(self):
        """FAQ 생성"""
        faq = FAQ.objects.create(
            question='비밀번호를 잊었어요',
            answer='비밀번호 재설정 기능을 이용해주세요.',
            order=1
        )
        self.assertEqual(faq.question, '비밀번호를 잊었어요')
        self.assertTrue(faq.is_active)

    def test_faq_str(self):
        """FAQ __str__"""
        faq = FAQ.objects.create(
            question='질문입니다', answer='답변입니다'
        )
        self.assertEqual(str(faq), '질문입니다')

    def test_faq_ordering(self):
        """order 기준 정렬"""
        faq2 = FAQ.objects.create(
            question='두번째', answer='답', order=2
        )
        faq1 = FAQ.objects.create(
            question='첫번째', answer='답', order=1
        )
        faqs = FAQ.objects.all()
        self.assertEqual(faqs[0], faq1)


# ============================================
# 2. 폼 테스트
# ============================================

class InquiryFormTest(TestCase):
    """InquiryForm 테스트"""

    def test_valid_form(self):
        """정상 문의 폼"""
        data = {
            'name': '홍길동',
            'phone': '010-1234-5678',
            'email': 'hong@test.com',
            'content': '문의 내용입니다.',
        }
        form = InquiryForm(data=data)
        self.assertTrue(form.is_valid())

    def test_empty_name(self):
        """이름 비어있으면 실패"""
        data = {
            'name': '',
            'phone': '010-1234-5678',
            'email': 'hong@test.com',
            'content': '문의',
        }
        form = InquiryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_invalid_email(self):
        """잘못된 이메일 형식"""
        data = {
            'name': '홍길동',
            'phone': '010-1234-5678',
            'email': 'not-an-email',
            'content': '문의',
        }
        form = InquiryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_empty_content(self):
        """문의 내용 비어있으면 실패"""
        data = {
            'name': '홍길동',
            'phone': '010-1234-5678',
            'email': 'hong@test.com',
            'content': '',
        }
        form = InquiryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


# ============================================
# 3. 뷰 테스트
# ============================================

class CustomerServiceViewTest(TestCase):
    """고객센터 뷰 테스트"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_customer_service_page_get(self):
        """고객센터 페이지 접근 (비로그인)"""
        response = self.client.get(reverse('report:customer_service'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'report/customer_service.html')

    def test_customer_service_shows_form(self):
        """문의 폼 표시"""
        response = self.client.get(reverse('report:customer_service'))
        self.assertIn('form', response.context)

    def test_customer_service_shows_faqs(self):
        """FAQ 목록 표시"""
        FAQ.objects.create(
            question='질문1', answer='답변1', order=1, is_active=True
        )
        FAQ.objects.create(
            question='질문2', answer='답변2', order=2, is_active=False
        )
        response = self.client.get(reverse('report:customer_service'))
        faqs = response.context['faqs']
        # 활성화된 FAQ만 표시
        self.assertEqual(faqs.count(), 1)

    def test_inquiry_submit_anonymous(self):
        """비로그인 상태 문의 제출"""
        data = {
            'name': '비회원',
            'phone': '010-9999-8888',
            'email': 'anon@test.com',
            'content': '비회원 문의입니다.',
        }
        response = self.client.post(
            reverse('report:customer_service'), data
        )
        self.assertEqual(response.status_code, 302)
        inquiry = Inquiry.objects.first()
        self.assertEqual(inquiry.name, '비회원')
        self.assertIsNone(inquiry.user)

    def test_inquiry_submit_authenticated(self):
        """로그인 상태 문의 제출 시 user 자동 설정"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'name': '테스트유저',
            'phone': '010-1111-2222',
            'email': 'test@test.com',
            'content': '로그인 문의입니다.',
        }
        response = self.client.post(
            reverse('report:customer_service'), data
        )
        self.assertEqual(response.status_code, 302)
        inquiry = Inquiry.objects.first()
        self.assertEqual(inquiry.user, self.user)

    def test_inquiry_submit_invalid(self):
        """잘못된 문의 제출 시 폼 에러"""
        data = {
            'name': '',
            'phone': '',
            'email': '',
            'content': '',
        }
        response = self.client.post(
            reverse('report:customer_service'), data
        )
        # 리다이렉트 되지 않고 폼 다시 렌더링
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inquiry.objects.count(), 0)
