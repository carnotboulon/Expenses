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
        attr["id"] = self.key.urlsafe()              #self.key.id()
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
    date = ndb.DateProperty(indexed =  True, required = True)	# Expense date.
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
    recordedOn = ndb.DateTimeProperty(indexed = True, required = True)
 
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
        template = JINJA_ENVIRONMENT.get_template('expensesMobile.html')
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
        
        template_values = {
            'expenses': "",
            'shopList': "",
            'categoryList': "",
            'personList': "",
            'accountList': "",
            'typeList':""
        }
        template = JINJA_ENVIRONMENT.get_template('balanceMobile.html')
        self.response.write(template.render(template_values))
        
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
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        template_values = {
            'shopList': shops,
            'categoryList': cat,
            'personList': pers,
            'accountList': accounts,
            'typeList': payTypes,
            'today': today,
            'payTypes': payTypes
        }
        template = JINJA_ENVIRONMENT.get_template('addMobile.html')
        self.response.write(template.render(template_values))
        
    def post(self):
          
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
        
        # logging.info("Date: %s" % self.request.get('whenValue'))
        expense.date = datetime.datetime.strptime(self.request.get('whenValue'), '%Y-%m-%d')   
        
        # logging.info("Object: %s" % self.request.get('whatValue'))
        expense.object = self.request.get('whatValue')
        
        # logging.info("Price: %s" % self.request.get('priceValue'))
        expense.price = float(self.request.get('priceValue'))
        expense.currency = Currency.query(Currency.code == "EUR").get().key
        
        # logging.info("Shop: %s" % self.request.get_all('shopValue'))
        expense.shop = ndb.Key(urlsafe=self.request.get_all('shopValue')[0])
        #expense.shop = Shop.query(Shop.name == self.request.get('shop')).get().key
        
        # logging.info("Categories: %s" % self.request.get_all('catValues'))
        cats = self.request.get_all('catValues')
        expense.categories = [ndb.Key(urlsafe=cat) for cat in cats]
        
        # logging.info("Account: %s" % self.request.get_all('accountValue'))
        account = ndb.Key(urlsafe=self.request.get_all('accountValue')[0])
        expense.account = account
        expense.buyers = account.get().owner
        
        # logging.info("Benefs: %s" % self.request.get_all('benefsValue'))
        benefs = self.request.get_all('benefsValue')
        # benefObjects = [Person.query(ndb.AND(Person.firstName == b.split()[0], Person.lastName == b.split()[1])) for b in benefs]
        # benefKeys = [pers.get().key for pers in benefObjects]
        expense.beneficiaries = [ndb.Key(urlsafe=pers) for pers in benefs]
        
        expense.payType = ndb.Key(urlsafe=self.request.get('payTypeValue'))
        #expense.payType = PayementType.query(PayementType.type == self.request.get('payType')).get().key
        
        expense.recordedOn = datetime.datetime.now()
        logging.info(datetime.datetime.now())
        expense.recordedBy = Person.query(Person.email == user.email()).get().key
        
        # logging.info("Expense: %s" % expense.render())
        expense.put()
        
        query_params = {'expensebook_name': expensebook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

class RemoveExpense(webapp2.RequestHandler):
    def get(self):
        exp = ndb.Key(urlsafe=self.request.get('exp'))
        logging.info(exp.get().render())
        logging.info("Removing: %s" % exp.id())
        exp.delete()
        
        
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
    ('/remove', RemoveExpense),
    
    
], debug=True)