from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import MonthlyIncome, Transaction, Category, SavingsGoal
from .forms import MonthlyIncomeForm, ExpenseForm, SavingsGoalForm, SignUpForm
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.contrib.auth import views as auth_views
from django.contrib.auth import login

# Add this at the top with other imports
DEFAULT_CATEGORIES = [
    'Salary',
    'Rent/Mortgage',
    'Utilities',
    'Groceries',
    'Transportation',
    'Healthcare',
    'Entertainment',
    'Shopping',
    'Dining Out',
    'Education',
    'Savings',
    'Investments',
    'Insurance',
    'Phone/Internet',
    'Gifts',
]

# Add this at the top with other constants
DEFAULT_SAVINGS_GOALS = [
    {
        'name': 'Emergency Fund',
        'target_amount': 5000.00,
        'current_amount': 0.00,
        'target_date': timezone.now().date() + timezone.timedelta(days=180),
    },
    {
        'name': 'Vacation Fund',
        'target_amount': 2000.00,
        'current_amount': 0.00,
        'target_date': timezone.now().date() + timezone.timedelta(days=365),
    },
    {
        'name': 'New Car Down Payment',
        'target_amount': 10000.00,
        'current_amount': 0.00,
        'target_date': timezone.now().date() + timezone.timedelta(days=730),
    },
]

@login_required
def index(request):
    current_month = timezone.now().replace(day=1)
    
    # Get or create monthly income
    monthly_income, created = MonthlyIncome.objects.get_or_create(
        user=request.user,
        month=current_month,
        defaults={'amount': 0}
    )
    
    # Get monthly expenses
    monthly_expenses = Transaction.objects.filter(
        user=request.user,
        date__year=current_month.year,
        date__month=current_month.month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate remaining balance
    remaining_balance = monthly_income.amount - monthly_expenses
    
    # Get recent expenses
    recent_expenses = Transaction.objects.filter(
        user=request.user
    ).order_by('-date')[:5]
    
    # Get expenses by category
    expenses_by_category = Transaction.objects.filter(
        user=request.user,
        date__year=current_month.year,
        date__month=current_month.month
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'remaining_balance': remaining_balance,
        'recent_expenses': recent_expenses,
        'expenses_by_category': expenses_by_category,
    }
    return render(request, 'dashboard.html', context)

@login_required
def set_monthly_income(request):
    month = request.GET.get('month')
    if month:
        target_month = datetime.strptime(month, '%Y-%m-%d').date().replace(day=1)
    else:
        target_month = timezone.now().replace(day=1)
    
    monthly_income, created = MonthlyIncome.objects.get_or_create(
        user=request.user,
        month=target_month,
        defaults={'amount': 0}
    )
    
    if request.method == 'POST':
        form = MonthlyIncomeForm(request.POST, instance=monthly_income)
        if form.is_valid():
            form.save()
            messages.success(request, f'Monthly income for {monthly_income.get_month_display()} updated successfully!')
            return redirect('monthly_income_history')
    else:
        form = MonthlyIncomeForm(instance=monthly_income)
    
    return render(request, 'monthly_income_form.html', {
        'form': form,
        'month_display': monthly_income.get_month_display()
    })

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.transaction_type = 'expense'
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('index')
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'expense_form.html', {'form': form})

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    
    # Add default categories if user has no categories
    if not categories.exists():
        for category_name in DEFAULT_CATEGORIES:
            Category.objects.create(name=category_name, user=request.user)
        categories = Category.objects.filter(user=request.user)
        messages.success(request, 'Default categories have been added!')
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            category_id = request.POST.get('delete')
            Category.objects.filter(id=category_id, user=request.user).delete()
            messages.success(request, 'Category deleted successfully!')
        else:
            name = request.POST.get('name')
            if name:
                # Check if category already exists
                if not Category.objects.filter(user=request.user, name=name).exists():
                    Category.objects.create(name=name, user=request.user)
                    messages.success(request, 'Category added successfully!')
                else:
                    messages.warning(request, 'Category already exists!')
        return redirect('categories')
    
    # Get suggested categories (ones that don't exist for the user yet)
    existing_categories = set(categories.values_list('name', flat=True))
    suggested_categories = [cat for cat in DEFAULT_CATEGORIES if cat not in existing_categories]
    
    return render(request, 'category_list.html', {
        'categories': categories,
        'suggested_categories': suggested_categories
    })

@login_required
def monthly_income_history(request):
    incomes = MonthlyIncome.objects.filter(user=request.user)
    context = {
        'incomes': incomes,
        'current_month': timezone.now().replace(day=1)
    }
    return render(request, 'monthly_income_history.html', context)

@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('index')
    else:
        form = ExpenseForm(user=request.user, instance=expense)
    return render(request, 'expense_form.html', {'form': form, 'edit': True})

@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
    return redirect('index')

@login_required
def savings_list(request):
    savings_goals = SavingsGoal.objects.filter(user=request.user)
    
    # Add default savings goals if user has no goals
    if not savings_goals.exists():
        for goal in DEFAULT_SAVINGS_GOALS:
            SavingsGoal.objects.create(
                user=request.user,
                name=goal['name'],
                target_amount=goal['target_amount'],
                current_amount=goal['current_amount'],
                target_date=goal['target_date']
            )
        savings_goals = SavingsGoal.objects.filter(user=request.user)
        messages.success(request, 'Default savings goals have been added!')
    
    # Calculate progress for each goal
    for goal in savings_goals:
        goal.progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        goal.remaining = goal.target_amount - goal.current_amount
        goal.days_left = (goal.target_date - timezone.now().date()).days
        
        # Add status based on progress and days left
        if goal.progress >= 100:
            goal.status = 'Completed'
            goal.status_class = 'success'
        elif goal.days_left < 0:
            goal.status = 'Overdue'
            goal.status_class = 'danger'
        elif goal.progress >= 75:
            goal.status = 'On Track'
            goal.status_class = 'info'
        elif goal.progress >= 50:
            goal.status = 'In Progress'
            goal.status_class = 'primary'
        else:
            goal.status = 'Getting Started'
            goal.status_class = 'warning'
    
    context = {
        'savings_goals': savings_goals,
        'total_saved': sum(goal.current_amount for goal in savings_goals),
        'total_target': sum(goal.target_amount for goal in savings_goals),
    }
    return render(request, 'savings_list.html', context)



@login_required
def savings_add(request):
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            savings = form.save(commit=False)
            savings.user = request.user
            savings.save()
            messages.success(request, 'Savings goal added successfully!')
            return redirect('savings_list')
    else:
        form = SavingsGoalForm()
    return render(request, 'savings_form.html', {'form': form})

@login_required
def savings_edit(request, pk):
    savings = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST, instance=savings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Savings goal updated successfully!')
            return redirect('savings_list')
    else:
        form = SavingsGoalForm(instance=savings)
    return render(request, 'savings_form.html', {'form': form, 'edit': True})

@login_required
def savings_delete(request, pk):
    savings = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        savings.delete()
        messages.success(request, 'Savings goal deleted successfully!')
    return redirect('savings_list')

@login_required
def update_savings_progress(request, pk):
    savings = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        amount = request.POST.get('amount', '0')
        try:
            amount = Decimal(amount)
            savings.current_amount += amount
            savings.save()
            messages.success(request, f'Added ${amount} to {savings.name}')
        except (ValueError, InvalidOperation):
            messages.error(request, 'Invalid amount')
    return redirect('savings_list')

def signup(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please login to continue.')
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
  
