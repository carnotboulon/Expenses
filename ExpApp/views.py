from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.messages import get_messages

from ExpApp.models import Expense,Category,PayementType,BankAccount,Person, Currency

import time, datetime
import logging
DATE_FORMAT = "%d %B, %Y"

log = logging.getLogger(__name__)

# TODO: Mobile friendly
# TODO: Filter
# TODO: Balance
# TODO: Drop Excel

# Create your views here.
def index(request, expense_number = 20, ):
    log.info("*** INDEX PAGE ***")
    msg_storage = get_messages(request)
    for msg in msg_storage:
        log.info("[MESSAGE]: %s" % msg)
    # msg = kwargs["msg"]
    msg = ""
    expense_number = min(expense_number, 100)
    latest_expenses_list = Expense.objects.order_by('-date')[:expense_number]
    
    template = loader.get_template('expapp/expenseList.html')
    
    context = {'expenses': latest_expenses_list, "message" : msg}
    
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
        expense = get_object_or_404(Expense, pk=expense_id)
        log.info(expense)
        object = expense.object
        comment = expense.comment
        price = expense.price
        date = expense.date.strftime(DATE_FORMAT)
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
        date = datetime.date.today().strftime(DATE_FORMAT)     
        log.info(date)
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

def delete(request, expense_id):
    if expense_id:
        log.info("*** REMOVING Expense %s ***" % expense_id)
        expense = get_object_or_404(Expense, pk=expense_id)
        message = "Expense %s has been removed." % expense.object
        log.info(message)
        messages.info(request, message)
        expense.delete()
    else:
        raise Http404("Missing argument: Expense ID must be specified.")
    return redirect("/expapp/")

def save(request, expense_id):
    log.info("*** SAVING Expense ***")
    # log.info(request.META['HTTP_REFERER'])
    # log.info(dir(request.POST))
       
    if expense_id:
        expense = get_object_or_404(Expense, pk=expense_id)
        log.info("Expense %s retrieved." % expense_id)
    else:
        expense = Expense()
        log.info(">> Creating new expense.")
    
    expense.currency = Currency.objects.get(code="EUR")
    expense.recordedBy = Person.objects.get(email="arnaudboland@gmail.com")
    log.info(request.POST['expense'])
    expense.object = request.POST['expense']
    
    log.info(request.POST['comment'])
    expense.comment = request.POST['comment']
    
    log.info(request.POST['date'])
    date = datetime.datetime.strptime(request.POST['date'], DATE_FORMAT)
    expense.date = datetime.datetime.strftime(date, "%Y-%m-%d")
    
    log.info(request.POST['price'])
    expense.price = request.POST['price']
    
    account = get_object_or_404(BankAccount, pk=request.POST['account'])
    log.info(account)
    expense.account = account
    
    payType = get_object_or_404(PayementType, pk=request.POST['payType'])
    log.info(payType)
    expense.payType = payType
    
    expense.save()      # Must be saved before assigning many-to-many fields.
    
    catList = request.POST.getlist('categories')
    categories = [get_object_or_404(Category, pk=c) for c in catList]
    log.info(categories)
    expense.categories = categories
    
    # Retrieve beneficiaries.
    benefsList = request.POST.getlist('benefs')
    if "0" in benefsList:
        # Tous is selected.
        benefs = [p for p in Person.objects.all()]   
        log.info(benefs)
    else:
        benefs = [get_object_or_404(Person, pk=b) for b in benefsList]
    log.info(benefs)
    expense.beneficiaries = benefs
    
    expense.save()
    
    if expense_id:
        message = "Expense %s has been edited." % expense.object
    else:
        message = "Expense %s has been added." % expense.object
        
    log.info(message)
    messages.info(request, message)
    
    return redirect('/expapp/')
    
def download(request):
    return HttpResponse("Hello, this is the download page.")

def balance(request):
    return HttpResponse("Hello, this is the balance page.")    