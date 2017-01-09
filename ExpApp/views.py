from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from ExpApp.models import Expense,Category,PayementType,BankAccount,Person

import time, datetime

DATE_FORMAT = "%d %B, %Y"

# Create your views here.
def index(request, expense_number = 20):
    output = ""
    expense_number = min(expense_number, 100)
    
    latest_expenses_list = Expense.objects.order_by('-date')[:expense_number]
    
    template = loader.get_template('expapp/expenseList.html')
    context = {'expenses': latest_expenses_list}
    
    return render(request, "expapp/expenseList.html",context)
    
def add(request, expense_id):
    # Collects all lists and add a field to check of the item is selected.
    allCats = {}
    for cat in Category.objects.all():
        allCats[cat.name] = {"catObject": cat, "selected":0}

    allPers = {}
    for pers in Person.objects.all():
        allPers[pers.email] = {"persObject":pers, "selected":0}
        
    allAccounts = {}
    for bank in BankAccount.objects.all():
        allAccounts[bank.name] = {"bankObject":bank, "selected":0}
        
    allPayTypes = {}
    for payT in PayementType.objects.all():
        allPayTypes[payT.name] = {"payTObject":payT, "selected":0}
             
    # If expenseId is specified, tries to retrieve expense.
    if expense_id:
        expense = Expense.objects.filter(id=expense_id)
        if expense.exists():
            expense = expense.first()
            object = expense.object
            comment = expense.comment
            price = expense.price
            date = expense.date
            for cat in expense.categories.all():
                if cat.name in allCats.keys():
                    allCats[cat.name]["selected"] = 1
            
            for pers in expense.beneficiaries.all():
                if pers.email in allPers.keys():
                    allPers[pers.email]["selected"] = 1        
            
            if expense.account.name in allAccounts.keys():
                allAccounts[expense.account.name]["selected"] = 1

            if expense.payType.name in allPayTypes.keys():
                allPayTypes[expense.payType.name]["selected"] = 1
    
    else:     #expense_id not provided, initialize with empty fields.
        object = comment = price = ""
        date = (datetime.date.today() + datetime.timedelta(days=0)).strftime(DATE_FORMAT)     
            
    context = {
        'object': object,
        'categoryList': sorted(allCats.items()),
        'comment': comment,
        'date': date,
        'price': price,
        'personList': sorted(allPers.items()),
        'accountList': sorted(allAccounts.items()),
        'payTypes': sorted(allPayTypes.items()),
        'expId': expense_id    
    }
        
    return render(request, "expapp/expenseAdd.html",context)    
    
def download(request):
    return HttpResponse("Hello, this is the download page.")

def balance(request):
    return HttpResponse("Hello, this is the balance page.")    