from django.contrib import admin
from .models import TrustScore, Savings, Item, SavingsItem, SavingsTransaction, PaymentMethod
# from .models import TrustScore, Savings, Loan, Item, Payment, SavingsItem
from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth.admin import UserAdmin

admin.site.register(TrustScore)
# admin.site.register(Payment)
# admin.site.register(Transaction)
# admin.site.register(LoanItem)
admin.site.register(SavingsTransaction)
admin.site.register(PaymentMethod)
admin.site.register(Item)
admin.site.register(Savings)
admin.site.register(SavingsItem)   


from .models import UserDetails

@admin.register(UserDetails)
class UserDetailsAdmin(admin.ModelAdmin):
    list_display = ['user', 'identification_number', 'phone_number', 'nationality', 'physical_address']
    search_fields = ['user__username', 'identification_number', 'phone_number']