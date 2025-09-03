from finance.models import *
from django.shortcuts import redirect,get_object_or_404
from django.contrib import messages


class ExpenseCategoryManager:

    @staticmethod
    def create_expense_category(request):
        """
        Already provided in your snippet. Creates a new category.
        """
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        status = True

        new_category = ExpenseCategory.objects.create(
            name=name,
            description=description,
            status=status
        )
        messages.success(request, "New expense category created successfully")
        return redirect('finance:expense-categories')

    @staticmethod
    def edit_expense_category(request, category_id):
        
        category = get_object_or_404(ExpenseCategory, id=category_id)

        new_name = request.POST.get('name', '').strip()
        new_description = request.POST.get('description', '').strip()
        new_status = request.POST.get('status') == 'on'

        # Update fields
        category.name = new_name
        category.description = new_description
        category.status = new_status

        category.save()
        messages.success(request, f"Expense category “{category.name}” updated successfully")
        return redirect('finance:expense-categories')

    @staticmethod
    def delete_expense_category(request, category_id):
      
        category = get_object_or_404(ExpenseCategory, id=category_id)

        category.delete()

        messages.success(request, f"Expense category “{category.name}” deleted successfully")
        return redirect('finance:expense-categories')
    

class ExpenseManager:

    @staticmethod
    def create_expense(request):
        """
        Creates a new Expense from POST data: 'name', 'description',
        'category', 'date', 'status', and 'amount'.
        """
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category', '').strip()
        date = request.POST.get('date', '').strip()              
        status = request.POST.get('status', '').strip()
        amount = request.POST.get('amount', '').strip()

        category = get_object_or_404(ExpenseCategory, id=category_id)

        Expense.objects.create(
            name=name,
            description=description,
            category=category,
            date=date,
            status=status,
            amount=amount
        )

        messages.success(request, "Expense created successfully")
        return redirect('finance:expenses')

    @staticmethod
    def edit_expense(request, expense_id):
       
        expense = get_object_or_404(Expense, id=expense_id)

        new_name = request.POST.get('name', '').strip()
        new_description = request.POST.get('description', '').strip()
        new_category_id = request.POST.get('category', '').strip()
        new_date = request.POST.get('date', '').strip()
        new_status = request.POST.get('status', '').strip()
        new_amount = request.POST.get('amount', '').strip()

        new_category = get_object_or_404(ExpenseCategory, id=new_category_id)

        expense.name = new_name
        expense.description = new_description
        expense.category = new_category
        expense.date = new_date
        expense.status = new_status
        expense.amount = new_amount

        expense.save()
        messages.success(request, f"Expense “{expense.name}” updated successfully")
        return redirect('finance:expenses')

    @staticmethod
    def delete_expense(request, expense_id):
        
        expense = get_object_or_404(Expense, id=expense_id)

        # HARD delete:
        expense.delete()

        messages.success(request, f"Expense “{expense.name}” deleted successfully")
        return redirect('finance:expenses')

    