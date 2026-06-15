from django.contrib import admin

from .models import BudgetCategory, BudgetProfile, Expense, MobileMoneyTransaction, Transaction


class BudgetCategoryInline(admin.TabularInline):
    model = BudgetCategory
    extra = 0


@admin.register(BudgetProfile)
class BudgetProfileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'income_amount', 'income_frequency', 'monthly_income',
        'mtn_phone', 'airtel_phone', 'currency',
    )
    list_filter = ('income_frequency',)
    search_fields = ('name', 'mtn_phone', 'airtel_phone')
    inlines = [BudgetCategoryInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('label', 'txn_type', 'amount', 'category', 'occurred_at', 'profile')
    list_filter = ('txn_type', 'category', 'occurred_at')
    search_fields = ('label', 'category', 'note')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'profile')
    list_filter = ('category', 'date')


@admin.register(MobileMoneyTransaction)
class MobileMoneyTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'provider', 'direction', 'amount', 'status', 'timestamp')
    list_filter = ('provider', 'direction', 'status')
