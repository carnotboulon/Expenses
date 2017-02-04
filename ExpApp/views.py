from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.messages import get_messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from ExpApp.models import Expense,Category,PayementType,BankAccount,Person, Currency

import time, datetime, csv, os, sys
import logging
DATE_FORMAT = "%d %B, %Y"

log = logging.getLogger(__name__)

# TODO: Upload CSV -> Done
# TODO: Balance -> Done
# TODO: Mobile friendly -> Done
# TODO: Download CSV -> Done
# TODO: login -> Done
# TODO: show more, dynamic loading.
# TODO: auto complete
# TODO: Filter
# TODO: internal navigation with Ajax for quicker response 

def getExpense(**kwargs):
    for k in kwargs:
        log.info("%s >> %s" % (k,kwargs[k]))

def saveExpense(expenseDict):
    # Check if similar expense exists.
    # log.info("*** Saving Expense ***")
    similarExpenses = Expense.objects.filter(date=expenseDict["date"], price=expenseDict["price"])
    if len(similarExpenses) > 0:
        # log.info("Similar expense found.")
        raise ImportError
    else:
        # log.info("No similar expense found.")
        expense = Expense()
        expense.currency = Currency.objects.get(code="EUR")
        expense.recordedBy = Person.objects.get(email="arnaudboland@gmail.com")
        
        log.debug(expenseDict["object"])
        expense.object = expenseDict["object"]

        log.debug(expenseDict["comment"])
        expense.comment = expenseDict["comment"]

        log.debug(expenseDict["price"])
        expense.price = expenseDict["price"]

        log.debug(expenseDict["date"])
        expense.date = expenseDict["date"]
                
        log.debug(expenseDict["account"])
        account = BankAccount.objects.get(name=expenseDict["account"])
        expense.account = account
        
        log.debug(expenseDict["payType"])
        payType = PayementType.objects.get(name=expenseDict['payType'])
        expense.payType = payType
        
        expense.save()      # Must be saved before assigning many-to-many fields.
        log.debug("First Save")
        
        benefsList = expenseDict["beneficiaries"].split(",")
        benefs = [Person.objects.get(email=b) for b in benefsList]
        log.debug(benefs)
        expense.beneficiaries = benefs
        
        catList = expenseDict["categories"].split(",")
        cats = []
        for c in catList:
            try:
                cat = Category.objects.get(name=c)
            except ObjectDoesNotExist:
                log.info("Creating Catgeory %s" % c)
                cat = Category(name=c).save()
        
        cats.append(cat)
        expense.categories = cats
        
        expense.save()

def computeBalance():
    pers = Person.objects.all()
    log.debug(pers)
    persDict = {}
    
    # Initialize personal counts.
    for p in pers:
        persDict[p.email] = {"exp": 0., "benef": 0.}
    
    expenses = Expense.objects.all()
    
    for exp in expenses:
        # for each expense,
        # compute each buyer's apport,
        buyers = exp.account.owner.all()
        for buyer in buyers:
            persDict[buyer.email]["exp"] += float(exp.price / exp.nb_buyers)
        # compute each beneficiary part.
        for benef in exp.beneficiaries.all():
            persDict[benef.email]["benef"] += float(exp.price / exp.nb_beneficiaries)
            
    return persDict        

# Create your views here.

def loginView(request):
    next = ""
    if "next" in request.GET:
        next = request.GET["next"]
    if "login" in request.POST and "password" in request.POST:
        user = authenticate(username=request.POST["login"], password=request.POST["password"])
        if user is not None:
            login(request, user)
            # A backend authenticated the credentials
            if next:
                log.debug("Redirecting to next: %s" % next)
                return redirect(next)
            else:
                log.debug("next not specified, redirect to index.")
                return redirect("/expapp/")
        else:
            # No backend authenticated the credentials
            return redirect("/expapp/login/")
        
    else:
        log.debug(next)
        context = {"next": next}
        return render(request, "expapp/login.html", context)

@login_required(login_url='/expapp/login/')
def logoutView(request):
    logout(request)
    return redirect("/expapp/login/")
        
@login_required(login_url='/expapp/login/')
def index(request, expense_number = 20):
    messages.info(request, "Display the %s last expenses." % expense_number)
    log.info("*** INDEX PAGE ***")
    log.info("User: %s" % request.user)
    
    msg_storage = get_messages(request)
    for msg in msg_storage:
        log.debug("[MESSAGE]: %s" % msg)
    
    expense_number = min(int(expense_number), 1000)
    latest_expenses_list = Expense.objects.order_by('-date')[:expense_number]
    template = loader.get_template('expapp/expenseList.html')
    
    context = {'expenses': latest_expenses_list}
    
    return render(request, "expapp/expenseList.html",context)

@login_required(login_url='/expapp/login/') 
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

@login_required(login_url='/expapp/login/')
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

@login_required(login_url='/expapp/login/')
def save(request, expense_id):
    log.debug("*** SAVING Expense ***")
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
    log.debug(request.POST['expense'])
    expense.object = request.POST['expense']
    
    log.debug(request.POST['comment'])
    expense.comment = request.POST['comment']
    
    log.debug(request.POST['date'])
    date = datetime.datetime.strptime(request.POST['date'], DATE_FORMAT)
    expense.date = datetime.datetime.strftime(date, "%Y-%m-%d")
    
    log.debug(request.POST['price'])
    expense.price = request.POST['price']
    
    account = get_object_or_404(BankAccount, pk=request.POST['account'])
    log.debug(account)
    expense.account = account
    
    payType = get_object_or_404(PayementType, pk=request.POST['payType'])
    log.debug(payType)
    expense.payType = payType
    
    expense.save()      # Must be saved before assigning many-to-many fields.
    
    catList = request.POST.getlist('categories')
    categories = [get_object_or_404(Category, pk=c) for c in catList]
    log.debug(categories)
    expense.categories = categories
    
    # Retrieve beneficiaries.
    benefsList = request.POST.getlist('benefs')
    if "0" in benefsList:
        # Tous is selected.
        benefs = [p for p in Person.objects.all()]   
        log.debug(benefs)
    else:
        benefs = [get_object_or_404(Person, pk=b) for b in benefsList]
    log.debug(benefs)
    expense.beneficiaries = benefs
    
    expense.save()
    
    if expense_id:
        message = "Expense %s has been edited." % expense.object
    else:
        message = "Expense %s has been added." % expense.object
        
    log.info(message)
    messages.info(request, message)
    
    return redirect('/expapp/')

@login_required(login_url='/expapp/login/')    
def download(request):
    expenses = Expense.objects.all()
    expList = []
    # Go through expenses and store them in a dict. 
    # Possible improvement: could be done via render function.
    for exp in expenses:
        expItem = {}
        expItem["date"] = exp.date
        expItem["object"] = exp.object
        expItem["comment"] = exp.comment
        expItem["price"] = exp.price
        expItem["categories"] = [e.name for e in exp.categories.all()]
        expItem["account"] = exp.account.name
        expItem["buyers"] = [e.email for e in exp.account.owner.all()]
        expItem["beneficiaries"] = [e.email for e in exp.beneficiaries.all()]
        expItem["payType"] = exp.payType.name
        expList.append(expItem)
    
    # Generates the file content (header + expenses).
    fileContent = ""
    fileContent += "object;comment;date;price;categories;account;beneficiaries;payType\n"
    for exp in expList:
        extStr = "%s ; %s ; %s ; %s ; %s ; %s ; %s ; %s\n" % (exp["object"],exp["comment"],exp["date"],("%.2f" % exp["price"]).replace(".",","), ",".join(exp["categories"]), exp["account"], ",".join(exp["beneficiaries"]), exp["payType"]) 
        fileContent += extStr.encode("utf-8")
    
    response = HttpResponse(fileContent, content_type='text/csv')
    response['Content-Disposition'] = "attachment; filename=ExportDB-%s.csv" % time.strftime("%d%b%y")
    
    return response

@login_required(login_url='/expapp/login/')    
def balance(request):
    balance = computeBalance()
    log.info(balance)
    
    messages = {}
    for p in balance.keys():
        pName = Person.objects.get(email=p).surname
        msgExpense = "%s spent %.2f EUR" % (pName, balance[p]["exp"])
        msgBenefs = "%.2f EUR of the expenses were for %s" % (balance[p]["benef"], pName)
        
        log.info(msgExpense)
        log.info(msgBenefs)
        
        messages[pName] = []
        messages[pName].append(msgExpense)
        messages[pName].append(msgBenefs)
        
        personalBalance = balance[p]["exp"] - balance[p]["benef"]
        if personalBalance > 0.01:
            message = "%s needs %.2f EUR back." % (pName, abs(personalBalance)) 
            log.info(message)
            messages[pName].append(message)
        elif personalBalance < 0.01:
            message = "%s ows %.2f EUR." % (pName, abs(personalBalance)) 
            log.info(message)
            messages[pName].append(message)
        else:
            message.append("Accounts are balanced!")
            log.info(message)
            messages[pName].append(message)
    
    messages = messages.items()
    context = {'balanceMessages': messages}
    log.info(messages)
    return render(request, "expapp/balance.html",context)

@login_required(login_url='/expapp/login/')
def uploadCSV(request):
    return render(request, "expapp/expenseFeed.html")

# Clean expense line read in the document.
def cleanExpense(expenseDict):
    for key in expenseDict:
        # log.debug(key)
        if key == "beneficiaries" or key == "categories":
            cleanList = [b.strip() for b in expenseDict[key].split(",")] 
            if len(cleanList) ==1:
                expenseDict[key] = expenseDict[key].strip()
            else:
                expenseDict[key] = ",".join(cleanList)
        elif key == "date":
            # dateStr = expenseDict[key][:-2] +"20"+expenseDict[key][-2:]
            # date = datetime.datetime.strptime(dateStr, "%d-%m-%Y")
            # expenseDict[key] = datetime.datetime.strftime(expenseDict[key], "%Y-%m-%d")
            expenseDict[key] = expenseDict[key].strip()
        elif key == "price":
            expenseDict[key] = expenseDict[key].strip().replace(",",".")
        
        else:
            expenseDict[key] = expenseDict[key].strip()
            
    return expenseDict

def feed(request):
    success = 0
    total = 0
    
    myfile = request.FILES['csvfile']
    fs = FileSystemStorage()
    filename = fs.save(myfile.name, myfile)
    uploaded_file_url = fs.url(filename)
    uploaded_file_path = os.path.join(settings.MEDIA_ROOT,filename)
    log.info("*** FILE %s ***" % filename)
    log.info("Processing: %s" % uploaded_file_path)
    
    with open(uploaded_file_path, 'rb') as csvfile:
        expenseReader = csv.DictReader(csvfile, delimiter=";")
        for row in expenseReader:
            row = cleanExpense(row)
            try:
                time.sleep(0.1)
                saveExpense(row)
            except ImportError as error:
                log.warning("DUPLICATED: Adding expense %s on %s FAILED: a similar expense already exists." % (row["object"], row["date"]))
                total += 1
            except:
                log.warning("FAILED: Adding expense %s on %s FAILED: an unexpected expense occurred: %s." % (row["object"], row["date"], sys.exc_info()[1]))
                total += 1
            else:            
                success += 1
                total += 1

    message = "%s/%s new expenses added." % (success, total)
    log.info(message)
    messages.info(request, message)
    return redirect('/expapp/')    
    
    
    