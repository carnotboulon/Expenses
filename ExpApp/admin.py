from django.contrib import admin

from .models import Person, Currency, Category, BankAccount, PayementType, Expense 

# Register your models here.

admin.site.register(Person)
admin.site.register(Currency)
admin.site.register(Category)
admin.site.register(BankAccount)
admin.site.register(PayementType)
admin.site.register(Expense)