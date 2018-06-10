from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.urls import reverse
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
DATE_FORMAT = "%d %b %Y"

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

# Used when CSV file is uploaded.
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

		# expense.recordedBy = Person.objects.get(email="arnaudboland@gmail.com")
		expense.recordedBy = Person.objects.get(email=expenseDict["recordedBy"])
		expense.recordedOn = expenseDict["recordedOn"]

		log.debug(expenseDict["object"])
		expense.object = expenseDict["object"]

		log.debug(expenseDict["comment"])
		expense.comment = expenseDict["comment"]

		log.debug(expenseDict["price"])
		expense.price = expenseDict["price"]

		expense.currency = Currency.objects.get(code="EUR")
		
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
	log.info("> LOGIN PAGE")
	next = ""
	if "next" in request.GET:
		next = request.GET["next"]
	if "login" in request.POST and "password" in request.POST:
		user = authenticate(username=request.POST["login"], password=request.POST["password"])
		if user is not None:
			login(request, user)
			log.info(">>> %s logged IN." % user)
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
	log.info("<<< %s logged OUT." % request.user)
	logout(request)
	return redirect("/expapp/login/")
        
@login_required(login_url='/expapp/login/')
def index(request, expense_number = 20):
	log.info("> INDEX PAGE, User: %s" % request.user)
	messages.info(request, "Display the %s last expenses." % expense_number)
    
	msg_storage = get_messages(request)
	for msg in msg_storage:
		log.debug("[FLASH]: %s" % msg)
    
	expense_number = min(int(expense_number), 100)
	latest_expenses_list = Expense.objects.order_by('-date')[:expense_number]
	
	context = {'expenses': latest_expenses_list}
    
	return render(request, "expapp/expenseList.html",context)

@login_required(login_url='/expapp/login/')
def shortcuts(request):
	log.info("> SHORTCUTS PAGE, User: %s" % request.user)
	context = {}
	return render(request, "expapp/shortcuts.html",context)
	
@login_required(login_url='/expapp/login/') 
def add(request, expense_id):
	log.info("> ADD PAGE, User: %s" % request.user)
	# Collects all lists and add a field to check of the item is selected.
	allCats = {}
	for cat in Category.objects.all():
		allCats[cat.name] = {"catObject": cat, "active":cat.active, "selected":0}

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
		date = expense.date.strftime("%Y-%m-%d")            # Init date format has to be "%Y-%m-%d"        
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
		date = datetime.date.today().strftime("%Y-%m-%d")   # Init date format has to be "%Y-%m-%d"      
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
	log.info("> DELETE PAGE, User: %s" % request.user)
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

	# django sometimes return a lazy object that can be user or anonymousUser
	# if it's the case, user has to be extracted from lazy object.
	user = request.user
	if hasattr(user, '_wrapped'):
		user = request.user._wrapped
    
	expense.recordedBy = Person.objects.get(email=user.email)
    
	log.debug(request.POST['expense'])
	expense.object = request.POST['expense']
    
	log.debug(request.POST['comment'])
	expense.comment = request.POST['comment']
    
	log.debug(request.POST['date'])
	try:
		date = datetime.datetime.strptime(request.POST['date'], DATE_FORMAT)
		expense.date = datetime.datetime.strftime(date, "%Y-%m-%d")
	except:
		expense.date = datetime.datetime.now()
    
    
	log.debug(request.POST['price'])
	expense.price = request.POST['price']
	
	# Currency is selected with a switch. Switch off = CHF, switch on = EUR.
	if "currency" in request.POST:
		# Switch on
		expense.currency = Currency.objects.get(code="EUR")
		log.debug("Expense in EURO")
	else:
		expense.currency = Currency.objects.get(code="CHF")
		log.debug("Expense in CHF")
		
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
	expense.categories.set(categories)
    
    # Retrieve beneficiaries.
	benefsList = request.POST.getlist('benefs')
	if "0" in benefsList:
		# Tous is selected.
		benefs = [p for p in Person.objects.all()]   
		log.debug(benefs)
	else:
		benefs = [get_object_or_404(Person, pk=b) for b in benefsList]
	log.debug(benefs)
	expense.beneficiaries.set(benefs)
    
	expense.save()
    
	if expense_id:
		message = "Expense %s has been edited." % expense.object
	else:
		message = "Expense %s has been added." % expense.object
        
	log.info(message)
	messages.info(request, message)
    
	return redirect('/expapp/list/')

@login_required(login_url='/expapp/login/')
def report(request):
	log.info("> REPORT PAGE, User: %s" % request.user)
	
	# Daily Expenses
	daily_expenses = Expense.objects.filter(date__exact=datetime.date.today()).exclude(categories__name= "SWISSto12")
	dailyExpEUR = 0
	dailyExpCHF = 0
	for exp in daily_expenses:
		if exp.currency.code == "EUR":
			dailyExpEUR += exp.price
		else:
			dailyExpCHF += exp.price
			
	# Weekly Expenses
	weekly_expenses = Expense.objects.filter(date__week=datetime.date.today().strftime("%V")).filter(date__year=datetime.date.today().strftime("%Y")).exclude(categories__name= "SWISSto12")
	weeklyExpEUR = 0
	weeklyExpCHF = 0
	for exp in weekly_expenses:
		if exp.currency.code == "EUR":
			weeklyExpEUR += exp.price
		else:
			weeklyExpCHF += exp.price
	
	# Monthly Expenses
	monthly_expenses = Expense.objects.filter(date__month=datetime.date.today().strftime("%m")).filter(date__year=datetime.date.today().strftime("%Y")).exclude(categories__name= "SWISSto12")
	monthlyExpEUR = 0
	monthlyExpCHF = 0
	for exp in monthly_expenses:
		if exp.currency.code == "EUR":
			monthlyExpEUR += exp.price
		else:
			monthlyExpCHF += exp.price
	
	context = {"dayCHF": dailyExpCHF, "dayEUR": dailyExpEUR, "weekCHF": weeklyExpCHF, "weekEUR": weeklyExpEUR, "monthCHF": monthlyExpCHF, "monthEUR": monthlyExpEUR}
	log.debug(context)
	return render(request, "expapp/report.html",context)
	
@login_required(login_url='/expapp/login/')    
def download(request):
	log.info("> DOWNLOAD PAGE, User: %s" % request.user)
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
		expItem["currency"] = exp.currency.code
		expItem["categories"] = [e.name for e in exp.categories.all()]
		expItem["account"] = exp.account.name
		expItem["beneficiaries"] = [e.email for e in exp.beneficiaries.all()]
		expItem["payType"] = exp.payType.name
		expItem["recordedBy"] = exp.recordedBy.email
		expItem["recordedOn"] = exp.recordedOn
		expList.append(expItem)
    
	# Generates the file content (header + expenses).
	fileContent = ""
	fileContent += "object;comment;date;price;currency;categories;account;beneficiaries;payType;recordedBy;recordedOn\n"
	for exp in expList:
		extStr = "%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (exp["object"],exp["comment"],exp["date"],("%.2f" % exp["price"]).replace(".",","),exp["currency"], ",".join(exp["categories"]), exp["account"], ",".join(exp["beneficiaries"]), exp["payType"], exp["recordedBy"],exp["recordedOn"]) 
		fileContent += extStr
	response = HttpResponse(fileContent, content_type='text/csv')
	response['Content-Disposition'] = "attachment; filename=ExportDB-%s.csv" % time.strftime("%d%b%y")
    
	return response

@login_required(login_url='/expapp/login/')    
def balance(request):
	log.info("> BALANCE PAGE, User: %s" % request.user)
	balance = computeBalance()
	log.debug(balance)
    
	messages = {}
	for p in balance.keys():
		pName = Person.objects.get(email=p).surname
		msgExpense = "%s spent %.2f EUR" % (pName, balance[p]["exp"])
		msgBenefs = "%.2f EUR of the expenses were for %s" % (balance[p]["benef"], pName)
        
		log.debug(msgExpense)
		log.debug(msgBenefs)
        
		messages[pName] = []
		messages[pName].append(msgExpense)
		messages[pName].append(msgBenefs)
        
		personalBalance = balance[p]["exp"] - balance[p]["benef"]
		if personalBalance > 0.01:
			message = "%s needs %.2f EUR back." % (pName, abs(personalBalance)) 
			messages[pName].append(message)
		elif personalBalance < 0.01:
			message = "%s ows %.2f EUR." % (pName, abs(personalBalance)) 
			messages[pName].append(message)
		else:
			message.append("Accounts are balanced!")
			messages[pName].append(message)
    
	messages = messages.items()
	context = {'balanceMessages': messages}
	log.debug(messages)
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
    
    
    