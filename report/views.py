"""
고객센터 뷰
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy

from .models import Inquiry, FAQ
from .forms import InquiryForm


class CustomerServiceView(TemplateView):
    """
    고객센터 메인 뷰
    - 문의 폼
    - FAQ 목록
    """
    template_name = 'report/customer_service.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = InquiryForm()
        context['faqs'] = FAQ.objects.filter(is_active=True)
        return context

    def post(self, request, *args, **kwargs):
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            if request.user.is_authenticated:
                inquiry.user = request.user
            inquiry.save()

            # 성공 메시지
            messages.success(
                request,
                '전송 되었습니다. 확인 후 빠르게 답변드리겠습니다.'
            )
            return redirect('report:customer_service')

        # 폼이 유효하지 않으면 에러와 함께 다시 렌더링
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)
