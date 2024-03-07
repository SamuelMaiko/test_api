from django.dispatch import receiver, Signal
from newmamapesa.models import SavingsItem, SavingsTransaction, LoanTransaction
from django.db.models.signals import post_save
from decimal import Decimal

@receiver(post_save, sender=SavingsItem)
def update_saving_account_total_amount(sender, instance, created, **kwargs):
    all_savings_items=instance.savings.savings_items.all()
    total_price=Decimal("0.00")
    for each in all_savings_items:
        total_price+=each.amount_saved
        
    instance.savings.amount_saved=total_price
    instance.savings.save()
    
# after_deposit - signal sent after a deposit is made 
after_deposit=Signal()
@receiver(after_deposit)
def create_a_transaction(sender, **kwargs):
    amount=kwargs["amount"]
    savings_item=kwargs["savings_item"]
    payment_method=kwargs["payment_method"]
    type=kwargs["type"]

    new_transaction=SavingsTransaction(amount=amount, savings_item_id=savings_item, payment_method_id=payment_method, type=type)
    new_transaction.save()


loan_disbursed=Signal()
@receiver(loan_disbursed, sender=None)
def create_loan_transaction(sender, **kwargs):
    LoanTransaction.objects.create(
        user=kwargs["user"],
        amount=kwargs["amount"],
        description=f"Loan disbursed for Kshs. {kwargs['amount']}",
        type='loan_disbursement',
        loan=kwargs["loan"]
    )
    loan=kwargs["loan"]
    loan.is_disbursed=True
    loan.save()


after_repay_loan=Signal()
@receiver(after_repay_loan, sender=None)
def create_transaction_after_repay(sender, **kwargs):
    user=kwargs["user"]
    loan=kwargs["loan"]
    amount=kwargs["amount"]
    
    new_loan_transaction=LoanTransaction(user=user, loan=loan, amount=amount, type="loan_repayment")
    new_loan_transaction.save()