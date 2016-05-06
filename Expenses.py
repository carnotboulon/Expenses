# [START imports]
from google.appengine.api import users
from google.appengine.ext import ndb
import os, datetime, webapp2, logging, urllib

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

def props(cls):
    """ Returns a list of tuples. Each tuple contains the class attribute name and its value.
    """
    keys = [i for i in cls.__dict__.keys() if i[:1] != '_' and not hasattr(cls.__dict__[i],"__call__")]
    props = []
    for k in keys:
        props.append((k, cls.__dict__[k]))
    return props
    
class RenderModel(ndb.Model):
    """ Class that extends ndb.Model to add it a rendering function. This function converts the entity into a dictionary.
    It's used to print an entity in a readable way.  
    """
    def __init__(self, **kwargs):
        ndb.Model.__init__(self, **kwargs)
    
    def render(self):
        """ Represents the entity in a dictionary. Each key is an attribute name and its value is the attribute value.
        It works recursively. So if an attribute value is another entity, it will be rendered as well.
        """
        attr = {}            
        # for each entity attribute, get the attribute name and its value.
        for a in props(self.__class__):
            key = a[0]
            val = a[1]._get_value(self)
            # if atribute is not a list, make it a list. This is just to be able to treat list and non list in the same way.
            isList = True
            if type(val) is not list:
                val = [val]
                isList = False
            elements = []
            for el in val:
                # if attribute value is a string, a float, a date or a time, use it as it is.
                if type(el) == unicode or type(el) == float or type(el) == datetime.date or type(el) == datetime.datetime or type(el) == int:
                    elements.append(el)
                # else if attribute value is not none, it is a key (a reference to another entity) => get its value from Datastore.
                elif el is not None:
                    elements.append(el.get().render())
                else:
                    elements.append("")
            # if list contains only 1 element, remove it from the list.
            # if len(elements) == 1:
                # attr[key] = elements[0]
            # else:
                # attr[key] = elements
            # If was not a list, remove list. 
            if not isList:
                attr[key] = elements[0]
            else:
                attr[key] = elements
        return attr
    
class Person(RenderModel):
    _use_cache = False
    _use_memcache = False
    firstName = ndb.StringProperty(indexed=True)
    lastName = ndb.StringProperty(indexed=True)
    surname = ndb.StringProperty(indexed=True)		
    email = ndb.StringProperty(indexed=True)	# Key Name

class Currency(RenderModel):
    _use_cache = False
    _use_memcache = False
    name = ndb.StringProperty(indexed = False, required = True)
    code = ndb.StringProperty(indexed = True, required = True)
        
class Shop(RenderModel):
    _use_cache = False
    _use_memcache = False
    name = ndb.StringProperty(indexed=True, required = True)
    location = ndb.GeoPtProperty(indexed=False)

class ExpenseCategory(RenderModel):
    _use_cache = False
    _use_memcache = False
    name = ndb.StringProperty(indexed=True, required = True)

class BankAccount(RenderModel):
    _use_cache = False
    _use_memcache = False
    owner = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    name = ndb.StringProperty(indexed = True, required = True)
    number = ndb.StringProperty(indexed = True, required = True)
    bank = ndb.StringProperty(indexed = False, required = True)
    
class PayementType(RenderModel):
    _use_cache = False
    _use_memcache = False
    type = ndb.StringProperty(indexed = True, required = True)

class Expense(RenderModel):
    _use_cache = False
    _use_memcache = False
    date = ndb.DateProperty(auto_now_add = True, indexed =  True, required = True)	# Expense date.
    object = ndb.StringProperty(indexed = True, required = True)
    price = ndb.FloatProperty(indexed = True, required = True)
    currency = ndb.KeyProperty(kind='Currency', required = True)

    shop = ndb.KeyProperty(kind='Shop', indexed = True, required = True)
    categories = ndb.KeyProperty(kind='ExpenseCategory', indexed = True, repeated = True)
    account = ndb.KeyProperty(kind='BankAccount', indexed = True, required = True)

    buyers = ndb.KeyProperty(kind='Person', indexed = True, repeated = True )
    nb_buyers = ndb.ComputedProperty(lambda e: len(e.buyers))
    beneficiaries = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    nb_beneficiaries =  ndb.ComputedProperty(lambda e: len(e.beneficiaries))
                        
    payType = ndb.KeyProperty(kind='PayementType', indexed = True, required = True)

    recordedBy = ndb.KeyProperty(kind='Person', indexed = True, required = True)
    recordedOn = ndb.DateTimeProperty(auto_now_add=True, indexed = True, required = True)
 
def sumAttribute(itemList, attribute):
    sum = 0
    for item in itemList:
        sum += float(getattr(item, attribute))
    return sum

def getExpenseByPerson(personEmail):
    p = Person.query(Person.email == personEmail).get()
    logging.info("Expenses from : %s %s" % (p.firstName, p.lastName))
    expenses = Expense.query(Expense.buyers == p.key).fetch()
    
    amount = 0.
    weight = 0.
    for exp in expenses:
        weight = 0
        if p.key in exp.beneficiaries:
            weight = 1. / exp.nb_beneficiaries
        else:
            weight = 1.
        part = exp.price * weight
        logging.info("Sub total =  %s" % (part))
        amount += part
    
    logging.info("Total Amount = %s" % (amount))
    return amount


def computeBalance(expensebook_name):
    pers = Person.query().fetch()
    # logging.info([p.key.id() for p in pers])
    persDict = {}
    for p in pers:
        persDict[p.key.id()] = {"exp": 0., "benef": 0.}
    
    # logging.info(persDict)
    expenses = Expense.query(ancestor = expensebook_key(expensebook_name))
    
    for exp in expenses:
        # for each expense,
        # compute each buyer's apport,
        # logging.info("*** DEPENSE")
        for buyer in exp.buyers:
            # logging.info("Comptes %s = %s avant: %s" % (buyer.get().email, buyer.id(), persDict[buyer.id()]))
            # logging.info("Exp: %s EUR" % (float(exp.price / exp.nb_buyers)))
            persDict[buyer.id()]["exp"] += float(exp.price / exp.nb_buyers)
            # logging.info("Comptes %s apres: %s" % (buyer.get().email, persDict[buyer.id()]))
               
        # compute each beneficiary part.
        for benef in exp.beneficiaries:
            # logging.info("Comptes %s = %s avant: %s" % (benef.get().email, benef.id(), persDict[benef.id()]))
            # logging.info("Benef: %s EUR" % (float(exp.price / exp.nb_beneficiaries)))
            persDict[benef.id()]["benef"] += float(exp.price / exp.nb_beneficiaries)
            # logging.info("Comptes %s apres: %s" % (benef.get().email, persDict[benef.id()]))
            
    return persDict
    
def getBalanceBetweenPersons(personA, personB):
    pass
    
#  [START PAGES]
class ExpensesPage(webapp2.RequestHandler):

    def get(self):
        # Checks for active Google account session
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
        expenses_query = Expense.query(ancestor=expensebook_key(expensebook_name)).order(-Expense.date)
        expenses = expenses_query.fetch()
        expenseList = []
        for exp in expenses:
            expenseList.append(exp.render())
        
        # logging.info("Voici les expenses:")
        # for exp in expenseList:
            # logging.info(exp)
            # # for k in exp.keys():
                # # logging.info("%s => %s" % (k,exp[k]))
        
        template_values = {
            'expenses': expenseList,
            'shopList': "",
            'categoryList': "",
            'personList': "",
            'accountList': "",
            'typeList':""
        }
        template = JINJA_ENVIRONMENT.get_template('expenses.html')
        self.response.write(template.render(template_values))

class BalancePage(webapp2.RequestHandler):

    def get(self):
        expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
        
        comptes = computeBalance(expensebook_name)
        # logging.info("%s" % (comptes))
        for k in comptes.keys():
            logging.info("%s" % (k))
            logging.info("\ta paye : %s" % (comptes[k]["exp"]))
            logging.info("\ta beneficie : %s" % (comptes[k]["benef"]))
        
        # logging.info(stephanieForArnaud.fetch())
        # for exp in stephanieExpenses:
            # logging.info("%s: %s buyers, %s benefs" % (exp.object, exp.nb_buyers, exp.nb_beneficiaries))
        
        # template_values = {
            # 'expenses': expenseList,
            # 'shopList': "",
            # 'categoryList': "",
            # 'personList': "",
            # 'accountList': "",
            # 'typeList':""
        # }
        # template = JINJA_ENVIRONMENT.get_template('expenses.html')
        # self.response.write(template.render(template_values))
        
class AddExpense(webapp2.RequestHandler):
    def get(self):
        # Get data.
        expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
        
        shops = [s.render() for s in Shop.query().fetch()]
        # logging.info("Shops: %s" % shops)
        
        cur = [c.render() for c in Currency.query().fetch()]
        # logging.info("Currencies: %s" % cur)
        
        cat = [c.render() for c in ExpenseCategory.query().fetch()]
        # logging.info("Cats: %s" % cat)
        
        pers = [p.render() for p in Person.query().fetch()]
        # logging.info("Persons: %s" % pers)
        
        accounts = [a.render() for a in BankAccount.query().fetch()]
        # logging.info("Accounts: %s" % accounts)
        
        payTypes = [t.render() for t in PayementType.query().fetch()]
        
        template_values = {
            'shopList': shops,
            'categoryList': cat,
            'personList': pers,
            'accountList': accounts,
            'typeList': payTypes
        }
        template = JINJA_ENVIRONMENT.get_template('add.html')
        self.response.write(template.render(template_values))
        
    def post(self):
        # expense = Expense(parent=expensebook_key(self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)))
        user = users.get_current_user()
        if user:
            self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
            self.response.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
        
        expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
        
        # logging.info("User: %s" % user.email())
        # logging.info("Expense Book Key: %s" % expensebook_key(expensebook_name))
        
        expense = Expense(parent=expensebook_key(expensebook_name))
        # logging.info("Object: %s" % self.request.get('object'))
        # logging.info("Price: %s" % float("%s.%s" % (self.request.get('price'), self.request.get('decimalPrice'))))
        # logging.info("Shop: %s" % self.request.get('shop'))
        # logging.info("Categories: %s" % self.request.get_all('categories'))
        # logging.info("Accounts: %s" % self.request.get_all('account'))
        # logging.info("Beneficiaries: %s" % self.request.get_all('paidFor'))
        
        expense.object = self.request.get('object')
        expense.price = float("%s.%s" % (self.request.get('price'), self.request.get('decimalPrice')))
        expense.currency = Currency.query(Currency.code == "EUR").get().key
        expense.shop = Shop.query(Shop.name == self.request.get('shop')).get().key
        
        cats = self.request.get_all('categories')
        catObjects = [ExpenseCategory.query(ExpenseCategory.name == c) for c in cats]
        expense.categories = [cat.get().key for cat in catObjects]
        expense.account = BankAccount.query(BankAccount.name == self.request.get('account')).get().key
        
        benefs = self.request.get_all('paidFor')
        benefObjects = [Person.query(ndb.AND(Person.firstName == b.split()[0], Person.lastName == b.split()[1])) for b in benefs]
        benefKeys = [pers.get().key for pers in benefObjects]
        expense.beneficiaries = benefKeys
        
        # logging.info("Account owner: %s" % BankAccount.query(BankAccount.name == self.request.get('account')).get().owner)
        expense.buyers = BankAccount.query(BankAccount.name == self.request.get('account')).get().owner
        
        expense.payType = PayementType.query(PayementType.type == self.request.get('payType')).get().key
        expense.recordedBy = Person.query(Person.email == user.email()).get().key
        
        # logging.info("Expense: %s" % expense.render())
        expense.put()
        
        query_params = {'expensebook_name': expensebook_name}
        self.redirect('/?' + urllib.urlencode(query_params))
        
class FeedData(webapp2.RequestHandler):

    def get(self):
        self.response.write("Bonjour c'est dans la boite.")
        
        p1 = Person(firstName ="Stephanie",lastName ="Thys",surname ="STH",email = "stephanie.thys@gmail.com")
        p1.put()
        c1 = Currency(name="Dollar US",code="USD")
        c1.put()
        s1 = Shop(name="Carrefour")
        s1.put()
        e1 = ExpenseCategory(name = "Travaux")
        e1.put()
        pt1 = PayementType(type = "Maestro")
        pt1.put()
        a1 = BankAccount(owner = [p1.key], name = "Steph Prive", number = "123-456789-11", bank = "Fortis")
        a1.put()
        
        exp1 = Expense(parent=expensebook_key())
        exp1.object = "Sandwich"
        exp1.price = 1.5
        exp1.currency = c1.key
        exp1.shop = s1.key
        exp1.category = [e1.key]
        exp1.account = a1.key
        exp1.buyer = [p1.key]
        exp1.beneficiary = [p1.key]    
        exp1.payType = pt1.key
        exp1.recordedBy = p1.key
        exp1.put()
        
app = webapp2.WSGIApplication([
    ('/', ExpensesPage),
    # ('/feed', FeedData),
    ('/add', AddExpense),
    ('/balance', BalancePage),
    
], debug=True)