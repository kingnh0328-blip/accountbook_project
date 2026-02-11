from django.urls import path
from . import views


app_name = 'transactions'

urlpatterns = [
  # 거래 내역
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('create/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('<int:pk>/update/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    
    # 영수증 업로드/삭제 (팀원 C 지원)
    path('<int:pk>/upload/', views.AttachmentUploadView.as_view(), name='attachment_upload'),
    path('attachment/<int:pk>/delete/', views.AttachmentDeleteView.as_view(), name='attachment_delete'),
    path('api/categories/', views.CategoryByTypeView.as_view(), name='api_categories_by_type'),
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/create/ajax/', views.category_create_ajax, name='category_create_ajax'),
    path('category/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
]

