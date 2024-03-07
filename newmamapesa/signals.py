from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from newmamapesa.models import Savings, SavingsItem, Loan

CustomUser=settings.AUTH_USER_MODEL

@receiver(post_save, sender=CustomUser)
def create_savings_account_on_user_creation(sender, instance, created, **kwargs):
    if created:
        Savings.objects.create(user=instance)

@receiver(post_save, sender=SavingsItem)
def create_savings_account_on_user_creation(sender, instance, created, **kwargs):
    if created:
        instance.target_amount=instance.item.price
        instance.save() 

@receiver(post_save, sender=Loan)
def create_savings_account_on_user_creation(sender, instance, created, **kwargs):
    if created:
        instance.user.loan_owed+=instance.amount
        instance.user.save() 
        
               
        
