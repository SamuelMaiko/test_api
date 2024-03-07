from rest_framework import serializers
from newmamapesa.models import Loan,Savings, SavingsItem,SavingsTransaction, Item, LoanTransaction, CustomUser

class SavingsAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model=Savings
        fields=["id","amount_saved","start_date"]
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=Item
        fields=["id","name","description"]
class SavingsItemSerializer(serializers.ModelSerializer):
    item=ItemSerializer()
    class Meta:
        model=SavingsItem
        fields=["id","item","amount_saved","target_amount","start_date","remaining_amount","installment","days_payment","remaining_days", "due_date","saving_period","is_achieved","in_progress"]

class SavingsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model=SavingsTransaction
        fields=["id", "type", "amount","timestamp"]
class LoanRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['amount', 'purpose']
class LoanTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanTransaction
        fields = '__all__'
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        print(f"User: {self.request.user.username}")
        print(response.data) 
        return response
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['loan_owed', 'loan_limit']
