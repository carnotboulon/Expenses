# coding: utf8 
import requests
import BeautifulSoup as bs
import sys
import bleach
import datetime
import string

# import os
# os.chdir(r"D:\Arnaud\Github\Expenses")
# import googleAuth
# b = googleAuth.CSVSaver(email,pwd,csvFileName,delimiter)
# b.saveExpenses()


class SessionGoogle:
    
    url = "http://bandpmoney.appspot.com"
    url_login = "https://accounts.google.com/ServiceLogin"
    url_auth = "https://accounts.google.com/ServiceLoginAuth"
    dateFormat = "%Y-%m-%d"
    
    def __init__(self, email, mdp):
        # Connect to Google.
        print "Connecting to Google...",
        self.ses = requests.session()
        login_html = self.ses.get(SessionGoogle.url_login)
        soup_login = bs.BeautifulSoup(login_html.content).find('form').findAll('input')
        my_dict = {}
        for u in soup_login:
            if u.has_key('value') and u.has_key('name'):
                my_dict[u['name']] = u['value']
        # override the inputs without login and pwd:
        my_dict['Email'] = email
        my_dict['Passwd'] = mdp
        response = self.ses.post(SessionGoogle.url_auth, data=my_dict)
        if response.status_code == 200:
            print "Done."
        else:
            print r"Failed - % - %" % (response.status_code, reponse.reason)
            sys.exit(0)
        # Access to URL
        print "Accessing BandPMoney...",
        form = self.ses.get(SessionGoogle.url)
        if form.status_code == 200:
            print "Done."
        else:
            print r"Failed - % - %" % (form.status_code, form.reason)
            sys.exit(0)
        print "Extract infos...",
        self.formSoup = bs.BeautifulSoup(form.content).find('form')
        self._getCategories()
        self._getShops()
        self._getPersons()
        self._getAccounts()
        self._getPayTypes()
        print "Done."
        print "Ready."
    
    def saveExpense(self, what, when, price, cats, shop, account, benefs, payType):
        what = what.decode("latin-1")
        cats = [c.decode("latin-1") for c in cats]
        shop = shop.decode("latin-1")
        account = account.decode("latin-1")
        benefs = [b.decode("latin-1") for b in benefs]
        payType = payType.decode("latin-1")
        
        # Clean Object
        object = bleach.clean(what, 
                       tags = bleach.ALLOWED_TAGS,
                       attributes = bleach.ALLOWED_ATTRIBUTES, 
                       styles = bleach.ALLOWED_STYLES, 
                       strip = False, strip_comments = True)

        # Check and clean date
        try:
            d = when.split("-")
            date = datetime.date(int(d[0]),int(d[1]),int(d[2])).strftime(SessionGoogle.dateFormat)
          
        except:
            date = datetime.date.today().strftime(SessionGoogle.dateFormat)
        
        # Check and clean price
        try:
            p = float(price)
        except:
            p = 0.
        
        # Find Category Key
        catsKeys = []
        for c in cats:
            if string.lower(c) in self.categories.keys():
                catsKeys.append(self.categories[string.lower(c)])
            else:
                catsKeys.append(self.categories["autre"])
        
        # Find Shop Key
        if string.lower(shop) in self.shops.keys():
            shopKey = self.shops[string.lower(shop)]
        else:
            shopKey = self.shops["autre"]

        # Find Account Key
        if string.lower(account) in self.accounts.keys():
            accountKey = self.accounts[string.lower(account)]
        else:
            accountKey = self.accounts["arn courant"]

        # Find Benefs Key
        benefsKeys = []
        for b in benefs:
            if string.lower(b) in self.persons.keys():
                benefsKeys.append(self.persons[string.lower(b)])
            else:
                benefsKeys.append(self.persons["arnaud boland"])
        
        # Find PayType Key
        if string.lower(payType) in self.payTypes.keys():
            payTypeKey = self.payTypes[string.lower(payType)]
        else:
            payTypeKey = self.payTypes["Cash"]
        
        myData = {
            "whatValue":object,
            "priceValue": p,
            "catValues": catsKeys,
            "whenValue": date,
            "shopValue": shopKey,
            "accountValue": accountKey,
            "benefsValue": benefsKeys,
            "payTypeValue": payTypeKey,
        }
        # print myData
        return self.ses.post(self.url, myData)
        
    def _getCategories(self):
        self.categories = {}
        cats = self.formSoup.findAll("input", attrs={"name": "catValues"})
        for c in cats:
            if type(c.previous.previous) != bs.Comment:
                self.categories[string.lower(c.previous.previous)] = c.attrMap["value"]
        return self.categories
        
    def _getShops(self):
        self.shops = {}
        shops = self.formSoup.findAll("input", attrs={"name": "shopValue"})
        for s in shops:
            if type(s.next.next.text) != bs.Comment:
                self.shops[string.lower(s.next.next.text)] = s.attrMap["value"]
        return self.shops
        
    def _getPersons(self):
        self.persons = {}
        pers = self.formSoup.findAll("input", attrs={"name": "benefsValue"})
        for p in pers:
            if type(p.next.next) != bs.Comment:
                self.persons[string.lower(p.next.next.text)] = p.attrMap["value"]
        return self.persons
                
    def _getAccounts(self):
        self.accounts = {}
        accs = self.formSoup.find("select", attrs={"name": "accountValue"}).findAll("option")
        for a in accs:
            if type(a) != bs.Comment:
                self.accounts[string.lower(a.text)] = a.attrs[0][1]
        return self.accounts

    def _getPayTypes(self):
        self.payTypes = {}
        pts = self.formSoup.find("select", attrs={"name": "payTypeValue"}).findAll("option")
        for p in pts:
            if type(p) != bs.Comment:
                self.payTypes[string.lower(p.text)] = p.attrs[0][1]
        return self.payTypes

        
import csv

class CSVSaver:
    def __init__(self, email, mdp, filename, delimiter):
        self.filename = filename
        self.rawExpenses = []
        reader = csv.DictReader(open(self.filename),delimiter=delimiter)
        for exp in reader:
            self.rawExpenses.append(exp)
        self.cleanExpenses()
        self.ses = SessionGoogle(email, mdp)
        self.saveExpenses()
        
    # Takes care of the lists in the raw data (categories and benefs).
    def cleanExpenses(self):
        self.expenses = self.rawExpenses
        for exp in self.expenses:
            exp["cats"] = exp["cats"].split(",")
            exp["benefs"] = exp["benefs"].split(",")
    
    # Saves all the expenses stored in the CSV file on the website.
    def saveExpenses(self):
        count = 0
        for idx,exp in enumerate(self.expenses):
            response = self.ses.saveExpense(exp["what"], exp["when"], exp["price"], exp["cats"], exp["shop"], exp["account"], exp["benefs"], exp["payType"])
            if response.status_code == 200:
                count += 1
                print "Expense #%d saved." % (idx+1)
            else:
                print "Problem with expense line %d" % (idx+1)
        if len(self.expenses) == count:
            print "All Expenses saved succesfully."
        else:
            print "%s expenses on % were saved succesfully." % (count, len(self.expenses))   
    
