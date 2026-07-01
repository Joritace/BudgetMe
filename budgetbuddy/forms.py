"""Budget setup and transfer forms."""

from django import forms
from django.forms import modelformset_factory

from budgetbuddy.constants import INCOME_FREQUENCY_CHOICES, SUGGESTED_BUDGET_CATEGORIES, UGX_AMOUNT_STEP
from budgetbuddy.models import BudgetCategory, BudgetProfile, MobileMoneyTransaction
from budgetbuddy.services.transfers import MIN_TRANSFER_AMOUNT, normalize_phone, phone_for_provider


def _ugx_number_attrs(**extra):
    """UGX inputs: type any whole amount; arrows/spinner step by UGX_AMOUNT_STEP via JS."""
    attrs = {
        'class': 'form-input ugx-amount-input',
        'step': '1',
        'min': '0',
        'inputmode': 'numeric',
        'data-ugx-step': str(UGX_AMOUNT_STEP),
    }
    attrs.update(extra)
    return attrs


class BudgetProfileForm(forms.ModelForm):
    income_amount = forms.DecimalField(
        min_value=0,
        max_digits=12,
        decimal_places=0,
        label='Income amount (UGX)',
        widget=forms.NumberInput(attrs=_ugx_number_attrs(
            placeholder='e.g. 2500000',
            min=0,
            **{'data-ugx-step-arrows': 'false'},
        )),
    )
    income_frequency = forms.ChoiceField(
        choices=INCOME_FREQUENCY_CHOICES,
        label='How often do you receive this income?',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    saving_goal_amount = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=0,
        label='Saving goal per pay period (UGX, optional)',
        widget=forms.NumberInput(attrs=_ugx_number_attrs(
            placeholder='Leave blank if none',
            min=0,
            **{'data-ugx-step-arrows': 'false'},
        )),
    )

    class Meta:
        model = BudgetProfile
        fields = ['name', 'income_amount', 'income_frequency', 'saving_goal_amount']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your name',
            }),
        }


class ProfileForm(forms.ModelForm):
    mtn_phone = forms.CharField(
        required=False,
        max_length=15,
        label='MTN Mobile Money',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. 0770123456',
            'inputmode': 'tel',
        }),
    )
    airtel_phone = forms.CharField(
        required=False,
        max_length=15,
        label='Airtel Money',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. 0750123456',
            'inputmode': 'tel',
        }),
    )

    class Meta:
        model = BudgetProfile
        fields = ['name', 'mtn_phone', 'airtel_phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your name',
            }),
        }

    def clean_mtn_phone(self):
        return self._clean_phone(self.cleaned_data.get('mtn_phone'))

    def clean_airtel_phone(self):
        return self._clean_phone(self.cleaned_data.get('airtel_phone'))

    def _clean_phone(self, raw):
        if not raw:
            return ''
        normalized = normalize_phone(raw)
        if not normalized:
            raise forms.ValidationError(
                'Enter a valid Ugandan number (e.g. 0770123456 or +256770123456).'
            )
        return normalized


class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ['name', 'allocated_amount']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Category name',
            }),
            'allocated_amount': forms.NumberInput(attrs=_ugx_number_attrs(
                placeholder='UGX amount',
                min=0,
            )),
        }


BudgetCategoryFormSet = modelformset_factory(
    BudgetCategory,
    form=BudgetCategoryForm,
    extra=2,
    can_delete=True,
)


def suggested_category_initial():
    return [
        {'name': name, 'allocated_amount': amount}
        for name, amount in SUGGESTED_BUDGET_CATEGORIES.items()
    ]


class TransferForm(forms.Form):
    direction = forms.ChoiceField(
        choices=MobileMoneyTransaction.DIRECTION_CHOICES,
        label='Type',
        initial='withdraw',
        widget=forms.RadioSelect(attrs={'class': 'direction-toggle'}),
    )
    provider = forms.ChoiceField(
        choices=MobileMoneyTransaction.PROVIDER_CHOICES,
        label='Payment method',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_provider'}),
    )
    amount = forms.DecimalField(
        min_value=MIN_TRANSFER_AMOUNT,
        max_digits=12,
        decimal_places=0,
        label='Amount (UGX)',
        widget=forms.NumberInput(attrs=_ugx_number_attrs(
            placeholder='Enter amount',
        )),
    )
    category = forms.ChoiceField(
        label='Budget category',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    note = forms.CharField(
        required=False,
        max_length=255,
        label='Note (optional)',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. School fees payment',
        }),
    )

    def __init__(self, profile=None, available_balance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.available_balance = available_balance
        if profile:
            categories = profile.categories.order_by('name')
            self.fields['category'].choices = [(c.name, c.name) for c in categories]
        if not self.fields['provider'].initial:
            self.fields['provider'].initial = 'mtn'

    def clean(self):
        cleaned = super().clean()
        provider = cleaned.get('provider')
        if provider == 'cash':
            cleaned['phone_number'] = ''
            return cleaned

        if not self.profile:
            raise forms.ValidationError('No budget profile found.')

        phone = phone_for_provider(self.profile, provider)
        if not phone:
            provider_label = dict(MobileMoneyTransaction.PROVIDER_CHOICES).get(provider, provider)
            raise forms.ValidationError(
                f'Add your {provider_label} number in Profile before using this method.'
            )
        cleaned['phone_number'] = phone
        return cleaned

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        direction = self.data.get('direction', 'withdraw')
        if direction == 'withdraw' and self.available_balance is not None and amount > self.available_balance:
            raise forms.ValidationError(
                f'Insufficient balance. Available: UGX {self.available_balance:,.0f}.'
            )
        return amount

    def clean_category(self):
        category = self.cleaned_data['category']
        if self.profile and not self.profile.categories.filter(name=category).exists():
            raise forms.ValidationError('Choose a category from your budget.')
        return category


class SavingsDepositForm(forms.Form):
    amount = forms.DecimalField(
        min_value=MIN_TRANSFER_AMOUNT,
        max_digits=12,
        decimal_places=0,
        label='Amount to save (UGX)',
        widget=forms.NumberInput(attrs=_ugx_number_attrs(
            placeholder='From your available balance',
            **{'data-ugx-step-arrows': 'false'},
        )),
    )
    note = forms.CharField(
        required=False,
        max_length=255,
        label='Note (optional)',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. SACCO contribution',
        }),
    )

    def __init__(self, available_balance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_balance = available_balance

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.available_balance is not None and amount > self.available_balance:
            raise forms.ValidationError(
                f'Insufficient balance. Available: UGX {self.available_balance:,.0f}.'
            )
        return amount
