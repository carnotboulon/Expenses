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
    def __init__(self):
        ndb.Model.__init__(self)
    
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
            if type(val) is not list:
                val = [val]
            elements = []
            for el in val:
                # if attribute value is a string, a float, a date or a time, use it as it is.
                if type(el) == unicode or type(el) == float or type(el) == datetime.date or type(el) == datetime.datetime:
                    elements.append(el)
                # else if attribute value is not none, it is a key (a reference to another entity) => get its value from Datastore.
                elif el is not None:
                    elements.append(el.get().render())
                else:
                    elements.append("")
            # if list conatins only 1 element, remove it from the list.
            if len(elements) == 1:
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
    category = ndb.KeyProperty(kind='ExpenseCategory', indexed = True, repeated = True)
    account = ndb.KeyProperty(kind='BankAccount', indexed = True, required = True)

    buyer = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    beneficiary = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    payType = ndb.KeyProperty(kind='PayementType', indexed = True, required = True)

    recordedBy = ndb.KeyProperty(kind='Person', indexed = True, required = True)
    recordedOn = ndb.DateTimeProperty(auto_now_add=True, indexed = True, required = True)

    

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
        logging.info(expensebook_name)
        expenses_query = Expense.query(ancestor=expensebook_key(expensebook_name)).order(-Expense.date)
        expenses = expenses_query.fetch()
        expenseList = []
        for exp in expenses:
            # self.response.write(str(exp.object)+"<BR />")
            # self.response.write(str(exp.price)+"<BR />")
            # self.response.write(str(exp.category[0].get().name)+"<BR />")
            # self.response.write(str(exp.buyer[0].get().firstName)+"<BR />")
            expenseList.append(exp.render())
        
        logging.info("Voici les expenses:")
        for exp in expenseList:
            for k in exp.keys():
                logging.info("%s => %s" % (k,exp[k]))
                
        
        template_values = {
            'expenses': expenseList,
            'shopList': "",
            'categoryList': "",
            'personList': "",
            'accountList': ""
        }
        template = JINJA_ENVIRONMENT.get_template('expenses.html')
        self.response.write(template.render(template_values))

class AddExpense(webapp2.RequestHandler):
    def get(self):
        # Get data.
        expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
        
        shops = Shop.query().fetch()
        logging.info("Shops: %s" % shops)
        cur = Currency.query().fetch()
        logging.info("Currencies: %s" % cur)
        cat = ExpenseCategory.query().fetch()
        logging.info("Cats: %s" % cat)
        pers = Person.query().fetch()
        logging.info("Persons: %s" % pers)
        accounts = BankAccount.query().fetch()
        logging.info("Accounts: %s" % accounts)
        
        template_values = {
            'shopList': shops,
            'categoryList': cat,
            'personList': pers,
            'accountList': accounts
        }
        template = JINJA_ENVIRONMENT.get_template('add.html')
        self.response.write(template.render(template_values))
        
        
        
    
    # def post(self):
        # pass
        
class FeedData(webapp2.RequestHandler):

    def get(self):
        self.response.write("Bonjour c'est dans la boite.")
        
        # p1 = Person(firstName ="Stephanie",lastName ="Thys",surname ="STH",email = "stephanie.thys@gmail.com")
        # p1.put()
        # c1 = Currency(name="Dollar US",code="USD")
        # c1.put()
        # s1 = Shop(name="Carrefour")
        # s1.put()
        # e1 = ExpenseCategory(name = "Travaux")
        # e1.put()
        # pt1 = PayementType(type = "Maestro")
        # pt1.put()
        # a1 = BankAccount(owner = [p1.key], name = "Steph Prive", number = "123-456789-11", bank = "Fortis")
        # a1.put()
        
        # exp1 = Expense(parent=expensebook_key())
        # exp1.object = "Sandwich"
        # exp1.price = 1.5
        # exp1.currency = c1.key
        # exp1.shop = s1.key
        # exp1.category = [e1.key]
        # exp1.account = a1.key
        # exp1.buyer = [p1.key]
        # exp1.beneficiary = [p1.key]    
        # exp1.payType = pt1.key
        # exp1.recordedBy = p1.key
        # exp1.put()
        
app = webapp2.WSGIApplication([
    ('/', ExpensesPage),
    ('/feed', FeedData),
    ('/add', AddExpense),
    
], debug=True)