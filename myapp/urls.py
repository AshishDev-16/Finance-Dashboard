from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('set-monthly-income/', views.set_monthly_income, name='set_monthly_income'),
    path('monthly-income-history/', views.monthly_income_history, name='monthly_income_history'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('edit-expense/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete-expense/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('categories/', views.category_list, name='categories'),
    path('savings/', views.savings_list, name='savings_list'),
    path('savings/add/', views.savings_add, name='savings_add'),
    path('savings/edit/<int:pk>/', views.savings_edit, name='savings_edit'),
    path('savings/delete/<int:pk>/', views.savings_delete, name='savings_delete'),
    path('savings/update/<int:pk>/', views.update_savings_progress, name='update_savings_progress'),
] 