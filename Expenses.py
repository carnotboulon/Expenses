# [START imports]
from google.appengine.api import users
from google.appengine.ext import ndb
import os, datetime, webapp2, logging

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_EXPENSEBOOK_NAME = 'BandP'

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.
def expensebook_key(expensebook_name=DEFAULT_EXPENSEBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.
    We use expensebook_name as the key.
    """
    return ndb.Key('Expensebook', expensebook_name)

class Person(ndb.Model):
    _use_cache = False
    _use_memcache = False
    firstName = ndb.StringProperty(indexed=True)
    lastName = ndb.StringProperty(indexed=True)
    surname = ndb.StringProperty(indexed=True)		
    email = ndb.StringProperty(indexed=True)	# Key Name

class Currency(ndb.Model):
    _use_cache = False
    _use_memcache = False
    name = ndb.StringProperty(indexed = False, required = True)
    code = ndb.StringProperty(indexed = True, required = True) 

class Shop(ndb.Model):
    _use_cache = False
    _use_memcache = False
    name = ndb.StringProperty(indexed=True, required = True)
    location = ndb.GeoPtProperty(indexed=False)

class ExpenseCategory(ndb.Model):
    _use_cache = False
    _use_memcache = False
    name = ndb.StringProperty(indexed=True, required = True)

class BankAccount(ndb.Model):
    _use_cache = False
    _use_memcache = False
    owner = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    name = ndb.StringProperty(indexed = True, required = True)
    number = ndb.StringProperty(indexed = True, required = True)
    bank = ndb.StringProperty(indexed = False, required = True)
    
class PayementType(ndb.Model):
    _use_cache = False
    _use_memcache = False
    type = ndb.StringProperty(indexed = True, required = True)

class Expense(ndb.Model):
    _use_cache = False
    _use_memcache = False
    date = ndb.DateProperty(auto_now_add = True, indexed =  True, required = True)	# Expense date.
    object = ndb.StringProperty(indexed = True, required = True)
    price = ndb.FloatProperty(indexed = True, required = True)
    currency = ndb.KeyProperty(kind='Currency', required = True)

    shop = ndb.KeyProperty(kind='Shop', indexed = True, required = True)
    category = ndb.KeyProperty(kind='ExpenseCategory', indexed = True, repeated = True)
    account = ndb.KeyProperty(kind='BankAccount', indexed = True, required = True)

    buyer = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    beneficiary = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    payType = beneficiary = ndb.KeyProperty(kind='PayementType', indexed = True, required = True)

    recordedBy = ndb.KeyProperty(kind='Person', indexed = True, required = True)
    recordedOn = ndb.DateTimeProperty(auto_now_add=True, indexed = True, required = True)

    def render(self):
        expense = {}
        expense["key"] = self.key.id()
        expense["pk"] = self.key.urlsafe()
        expense["date"] = self.date.strftime("%d-%m-%y")
        expense["object"] = self.object
        # expense["price"] = "%.2f %s" % (self.price,self.currency.code)
        expense["price"] = "%.2f" % (self.price)
        expense["currency"] = self.currency.get().code														# Key
        expense["shop"] = self.shop.get().name																# Key
        expense["category"] = ",".join(sorted([cat.get().name for cat in self.category]))						# Key
        expense["account"] = self.account.get().name															# Key
        expense["buyer"] = ",".join(sorted([buyer.get().firstName for buyer in self.buyer]))					# Key
        expense["beneficiary"] = ",".join(sorted([benef.get().firstName for benef in self.beneficiary])) 		# Key
        expense["recordedBy"] = self.recordedBy.get().surname													# Key
        expense["recordedOn"] = self.date.strftime("%d-%m-%y %H:%M")
        return expense

#  [START PAGES]
class ExpensesPage(webapp2.RequestHandler):

    def get(self):
        # Checks for active Google account session
        user = users.get_current_user()

        if user:
            self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
            #self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
        expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
        expenses_query = Expense.query(ancestor=expensebook_key(expensebook_name)).order(-Expense.date)
        expenses = expenses_query.fetch()
        expenseList = []
        for exp in expenses:
            # self.response.write(str(exp.object)+"<BR />")
            # self.response.write(str(exp.price)+"<BR />")
            # self.response.write(str(exp.category[0].get().name)+"<BR />")
            # self.response.write(str(exp.buyer[0].get().firstName)+"<BR />")
            expenseList.append(exp.render())
        
        logging.info("Bonjour")
        logging.info(expenseList)
        
        template_values = {
            'expenses': expenseList,
            'shopList': "",
            'categoryList': "",
            'personList': "",
            'accountList': ""
        }
        template = JINJA_ENVIRONMENT.get_template('expenses.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', ExpensesPage),
    
], debug=True)