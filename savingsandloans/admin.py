from django.contrib import admin

# Register your models here.

from newmamapesa.models import Loan, LoanTransaction, CustomUser

admin.site.register(Loan)
admin.site.register(CustomUser)
admin.site.register(LoanTransaction)
