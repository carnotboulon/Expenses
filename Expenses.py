#!/usr/bin/env python
# -*- coding: utf-8 -*-

# [START imports]
from google.appengine.api import users
from google.appengine.ext import ndb
import os, time, datetime, webapp2, logging, urllib

# 28JUIN16 - ne fonctionne pas car un élément "toBuy" reçoit comme subcategorie 
# soit une ExpenseCategory soit une ExpenseSubcategory. Il faut donc vérifier query
# la propriété subcategory de l'élément toBuy peut prendre des entités différentes (catgory ou subcategory).

import jinja2
import webapp2

authorized_users = ["arnaudboland@gmail.com", "stephanie.thys@gmail.com"]

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
                if type(el) == unicode or type(el) == float or type(el) == datetime.date or type(el) == datetime.datetime or type(el) == int or type(el) == bool:
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
    parentCategory = ndb.KeyProperty(kind='ExpenseCategory', indexed = True, required = False)
   
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
    comment = ndb.StringProperty(indexed = False, required = False)
    price = ndb.FloatProperty(indexed = True, required = True)
    currency = ndb.KeyProperty(kind='Currency', required = True)

    # shop = ndb.KeyProperty(kind='Shop', indexed = True, required = True)
    categories = ndb.KeyProperty(kind='ExpenseCategory', indexed = True, repeated = True)
    account = ndb.KeyProperty(kind='BankAccount', indexed = True, required = True)

    buyers = ndb.KeyProperty(kind='Person', indexed = True, repeated = True )
    nb_buyers = ndb.ComputedProperty(lambda e: len(e.buyers))
    beneficiaries = ndb.KeyProperty(kind='Person', indexed = True, repeated = True)
    nb_beneficiaries =  ndb.ComputedProperty(lambda e: len(e.beneficiaries))
                        
    payType = ndb.KeyProperty(kind='PayementType', indexed = True, required = True)

    recordedBy = ndb.KeyProperty(kind='Person', indexed = True, required = True)
    recordedOn = ndb.DateTimeProperty(indexed = True, required = True)

class ToBuy(RenderModel):
    _use_cache = False
    _use_memcache = False
    object = ndb.StringProperty(indexed = True, required = True)
    category = ndb.KeyProperty(kind='ExpenseCategory', indexed = True, required = True)
    enabled = ndb.BooleanProperty(indexed = True, required = True)
    
def computeBalance(expensebook_name):
    pers = Person.query().fetch()
    # logging.info([p.key.id() for p in pers])
    persDict = {}
    
    # Initialize personal counts.
    for p in pers:
        persDict[p.key.id()] = {"exp": 0., "benef": 0.}
        
        # Initialise la valeur pour Arn au bilan du 06 JUN 2016.
        # Derniere depense = Bic pour faire-part 06 JUN 16, 5.77 EUR.
        # if p.email == "arnaudboland@gmail.com":
            # persDict[p.key.id()]["benef"] = 341.50 + 88.09
        # if p.email == "stephanie.thys@gmail.com":
            # persDict[p.key.id()]["exp"] = 341.50 + 88.09
    
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

    
#  [START PAGES]
class ExpensesPage(webapp2.RequestHandler):
    def get(self):
        # Checks for active Google account session
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
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
            
            if user.email().lower() in authorized_users:
                template = JINJA_ENVIRONMENT.get_template('expenseList.html')
                self.response.write(template.render(template_values))
            else:
                template = JINJA_ENVIRONMENT.get_template('unauthorized.html')
                self.response.write(template.render({"email":user.email().lower()}))
        
class BalancePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
            
            comptes = computeBalance(expensebook_name)
            actions = []
            #logging.info("%s" % (comptes))
            for k in comptes.keys():
                logging.info("%s" % (Person.get_by_id(k).firstName))
                logging.info("\ta paye : %s" % (comptes[k]["exp"]))
                logging.info("\ta beneficie : %s" % (comptes[k]["benef"]))
                bilan = comptes[k]["exp"] - comptes[k]["benef"]
                logging.info(bilan)
                if bilan > 0.01:
                    action = "%s needs %.2f EUR back" % (Person.get_by_id(k).firstName, bilan)
                elif bilan < 0.01:
                    action = "%s ows %.2f EUR" % (Person.get_by_id(k).firstName, -bilan)
                else:
                    action = "%s %s is fine." % (Person.get_by_id(k).firstName, Person.get_by_id(k).lastName)
                logging.info(action)
                actions.append({"person":"%s %s"%(Person.get_by_id(k).firstName, Person.get_by_id(k).lastName), "action":action})
                
            if user.email().lower() in authorized_users:
                template_values = {
                    'actions': actions
                }
                template = JINJA_ENVIRONMENT.get_template('expenseBalance.html')
                self.response.write(template.render(template_values))
            else:
                template = JINJA_ENVIRONMENT.get_template('unauthorized.html')
                self.response.write(template.render({"email":user.email().lower()}))
        
class AddExpense(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))       
        else:
            # Get data.
            expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
            
            objects = list(set([e.render()["object"] for e in Expense.query().order(Expense.object)]))
            # logging.info("Objects: %s" % objects)
            
            shops = [s.render() for s in Shop.query().order(Shop.name)]
            # logging.info("Shops: %s" % shops)
            
            # cur = [c.render() for c in Currency.query().order(Currency.name)]
            # logging.info("Currencies: %s" % cur)
            
            cat = []
            catIds = []
            for c in ExpenseCategory.query():
                if c.parentCategory == None and c.render()["id"] not in catIds:
                    cat.append(c.render())
                    catIds.append(c.render()["id"])
                elif c.parentCategory != None and c.parentCategory.get().render()["id"] not in catIds:
                    cat.append(c.parentCategory.get().render())
                    catIds.append(c.parentCategory.get().render()["id"])
            
            sortedCat = sorted(cat, key=lambda k: k['name'])
            logging.info("Cats: %s" % sortedCat)
            
            pers = [p.render() for p in Person.query().order(Person.firstName)]
            # logging.info("Persons: %s" % pers)
            
            accounts = [a.render() for a in BankAccount.query().order(BankAccount.name)]
            # logging.info("Accounts: %s" % accounts)
            
            payTypes = [t.render() for t in PayementType.query().order(PayementType.type)]
            
            today = datetime.date.today().strftime("%Y-%m-%d")
            
            user = users.get_current_user()
            
            template_values = {
                'user': user.email().lower(),
                'expList': objects,
                'shopList': shops,
                'categoryList': cat,
                'personList': pers,
                'accountList': accounts,
                'typeList': payTypes,
                'today': today,
                'payTypes': payTypes
            }
            if user.email().lower() in authorized_users:
                template = JINJA_ENVIRONMENT.get_template('expenseAdd.html')
                self.response.write(template.render(template_values))
            else:
                template = JINJA_ENVIRONMENT.get_template('unauthorized.html')
                self.response.write(template.render({"email":user.email().lower()}))
           
    def post(self): 
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
            
            # logging.info("User: %s" % user.email())
            # logging.info("Expense Book Key: %s" % expensebook_key(expensebook_name))
            
            expense = Expense(parent=expensebook_key(expensebook_name))
            
            # logging.info("Date: %s" % self.request.get('whenValue'))
            expense.date = datetime.datetime.strptime(self.request.get('whenValue'), '%Y-%m-%d')   
            
            # logging.info("Object: %s" % self.request.get('whatValue'))
            expense.object = self.request.get('whatValue')
            
            expense.comment = self.request.get("commentValue")
            
            # logging.info("Price: %s" % self.request.get('priceValue'))
            expense.price = float(self.request.get('priceValue'))
            expense.currency = Currency.query(Currency.code == "EUR").get().key
            
            # logging.info("Shop: %s" % self.request.get_all('shopValue'))
            # expense.shop = ndb.Key(urlsafe=self.request.get_all('shopValue')[0])
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
            
            logging.info("User: %s", user.email())
            expense.recordedBy = Person.query(Person.email == user.email().lower()).get().key
            
            if user.email().lower() in authorized_users:
                # logging.info("Expense: %s" % expense.render())
                expense.put()
                
                query_params = {'expensebook_name': expensebook_name}
                # self.redirect('/?' + urllib.urlencode(query_params))
                self.redirect('/list')
            else:
                template = JINJA_ENVIRONMENT.get_template('unauthorized.html')
                self.response.write(template.render({"email":user.email().lower()}))

class RemoveEntity(webapp2.RequestHandler):
    def get(self):
        ent = ndb.Key(urlsafe=self.request.get('id'))
        logging.info("Removing: %s" % ent.get().object)
        ent.delete()
        
class DisableEntity(webapp2.RequestHandler):
    def get(self):
        ent = ndb.Key(urlsafe=self.request.get('id')).get()
        logging.info("Disabling: %s" % ent.object)
        ent.enabled = False
        ent.put()

class ToBuyPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))       
        else:
            # Get data.
            expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
            toBuyList = [tb.render() for tb in ToBuy.query().order(ToBuy.category)]
            # logging.info("ToBuy: %s" % toBuyList)
            
            template_values = {
                'user': user.email().lower(),
                'toBuyList': toBuyList,
                # 'subcategoryList': catList.sort()
            }
            
            if user.email().lower() in authorized_users:
                template = JINJA_ENVIRONMENT.get_template('toBuyList.html')
                self.response.write(template.render(template_values))
            else:
                template = JINJA_ENVIRONMENT.get_template('unauthorized.html')
                self.response.write(template.render({"email":user.email().lower()}))
    
class ToBuyAddPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))       
        else:
            # Get data.
            expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
            toBuyList = [tb.render() for tb in ToBuy.query().order(ToBuy.object)]
            # logging.info("ToBuy: %s" % toBuyList)
            
            
            # Prendre toutes les catégories qui on un parent non nul et stocker le parent dans une liste séparée. 
            # Reparcourir la liste des categories et retirer celles qui sont des parents.
            cats = ExpenseCategory.query()
            catList = [c.render() for c in cats]
            parentCats = [c.parentCategory.urlsafe() for c in cats if c.parentCategory != None]   # Gets the parent categories ids.         
            
            for cat in catList:
                logging.info("%s - %s" %(cat["name"], cat["parentCategory"]))
                
            for cat in parentCats:    
                logging.info(cat)
            
            # Retirer les categories parentes de catList
            for idx, cat in enumerate(catList):
                if cat["id"] in parentCats:
                    del catList[idx]               
            
            sortedList = sorted(catList, key=lambda k: k['name'])
            
            # OLD WAY OF WORKING.
            # subcats = set([c.key.urlsafe() for c in ExpenseSubcategory.query()])
            # cats = set([c.key.urlsafe() for c in ExpenseCategory.query()])
            # parentCats = set([c.category.urlsafe() for c in ExpenseSubcategory.query()])  # Get a list of parents categories (without duplicates).
            # catUrls = list(subcats.union(cats) - parentCats)
            # catList = [{"id": usafe, "name" : ndb.Key(urlsafe=usafe).get().name} for usafe in catUrls]
            # sortedList = sorted(catList, key=lambda k: k['name']) 
            # END OF OLD WAY OF WORKING.
            
            # logging.info(sortedList)
            
            template_values = {
                'user': user.email().lower(),
                'toBuyList': toBuyList,
                'subcategoryList': sortedList
            }
            
            if user.email().lower() in authorized_users:
                template = JINJA_ENVIRONMENT.get_template('toBuyAdd.html')
                self.response.write(template.render(template_values))
            else:
                template = JINJA_ENVIRONMENT.get_template('unauthorized.html')
                self.response.write(template.render({"email":user.email().lower()}))
    
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            expensebook_name = self.request.get('expensebook_name', DEFAULT_EXPENSEBOOK_NAME)
                       
            # Check if object already exist.
            newtoBuy = self.request.get('articleValue').capitalize()
            toBuyList = [tb.object for tb in ToBuy.query(ancestor=expensebook_key(expensebook_name)).fetch()]
            
            # if object already exist, enable it.
            if newtoBuy in toBuyList:
                toBuy = ToBuy.query(ToBuy.object == newtoBuy).get()         
                toBuy.enabled = True
            
            # else create it.
            else:
                toBuy = ToBuy(parent=expensebook_key(expensebook_name))
                toBuy.object = newtoBuy
                
                cat = self.request.get('catSelect')
                toBuy.category = ndb.Key(urlsafe=cat)
                
                toBuy.enabled = True
                
            
            if user.email().lower() in authorized_users:
                # logging.info("Expense: %s" % expense.render())
                toBuy.put()
                time.sleep(1)
                self.redirect('/toBuy')
                return
            else:
                template = JINJA_ENVIRONMENT.get_template('unauthorized.html')
                self.response.write(template.render({"email":user.email().lower()}))
        
class FeedData(webapp2.RequestHandler):
    def get(self):
        arn = ndb.Key(urlsafe="aghkZXZ-Tm9uZXITCxIGUGVyc29uGICAgICAgKQIDA").get()
        # # steph = ndb.Key(urlsafe="agxzfmJhbmRwbW9uZXlyEwsSBlBlcnNvbhiAgICA692ICgw").get()
        
        account = ndb.Key(urlsafe="aghkZXZ-Tm9uZXIYCxILQmFua0FjY291bnQYgICAgICAxAkM").get()
        # # BankAccount(owner = [arn.key,steph.key], name = "Tickets Restaurant", number = "", bank = "No Bank").put()
        # # BankAccount(owner = [arn.key], name = "Arn MasterCard", number = "123-456789-11", bank = "Belfius").put()
        
        cur = ndb.Key(urlsafe="aghkZXZ-Tm9uZXIVCxIIQ3VycmVuY3kYgICAgICAhAkM").get()
        # # Shop(name = "Brico").put()
        # # Shop(name = "Match").put()
        # # Shop(name = "Pharmacie").put()
        # # Shop(name = "Voltis").put()
        # # Shop(name = "Carodec").put()
        # # Shop(name = "Ikea").put()
        # # Shop(name = "Boucherie").put()
        # # Shop(name = "Boulangerie").put()
        # # Shop(name = "Colruyt").put()
        # # Shop(name = "Spar").put()
        # # shops = [s.render() for s in Shop.query().order(Shop.name)]
        # # logging.info("Shops: %s" % shops)
        
        # # cat = ndb.Key(urlsafe="aghkZXZ-Tm9uZXIcCxIPRXhwZW5zZUNhdGVnb3J5GICAgICA1L4JDA").get()
        # alim = ExpenseCategory(name="Alimentation").put()
        # tech = ExpenseCategory(name="Techs").put()
        # med = ExpenseCategory(name="Sante").put()
        
        # fruits = ExpenseSubcategory(name="Fruits", category=alim).put()
        # legumes = ExpenseSubcategory(name="Legumes", category=alim).put()
        
        # # cat = [c.render() for c in ExpenseCategory.query().order(ExpenseCategory.name)]
        # # for c in cat:
            # # logging.info("%s" % c)
        
        # # pers = [p.render() for p in Person.query().order(Person.firstName)]
        # # for p in pers:
            # # logging.info("%s %s %s %s" % (p["firstName"], p["lastName"], p["email"], p["surname"]))
        
        # # accounts = [a.render() for a in BankAccount.query().order(BankAccount.name)]
        # # for a in accounts:
            # # logging.info("%s %s %s" % (a["number"], a["bank"], a["owner"][0]["id"]))
        # pt = ndb.Key(urlsafe="aghkZXZ-Tm9uZXIZCxIMUGF5ZW1lbnRUeXBlGICAgICAgMQKDA").get()
        # alim = ndb.Key(urlsafe="aghkZXZ-Tm9uZXIcCxIPRXhwZW5zZUNhdGVnb3J5GICAgICA1OkIDA")
        # Expense(parent = expensebook_key(), date=datetime.datetime.now(), object="IPhone", comment="Light", price=33.0, currency = cur.key, categories=[alim], account = account.key, buyers = [arn.key], beneficiaries = [arn.key], payType = pt.key,recordedBy = arn.key, recordedOn = datetime.datetime.now() ).put()
        fr = ndb.Key(urlsafe="aghkZXZ-Tm9uZXIcCxIPRXhwZW5zZUNhdGVnb3J5GICAgICA1JkKDA")
        ToBuy(parent = expensebook_key(), object = "Fleurs", category = fr, enabled=True).put()
        
        # ExpenseCategory(name= "Santé", parentCategory=None).put()
        # ExpenseCategory(name= "Maison", parentCategory=None).put()
        # ExpenseCategory(name= "Techs", parentCategory=None).put()
        # alim = ExpenseCategory(name= "Alimentation", parentCategory=None).put()
        # ExpenseCategory(name= "Viande", parentCategory=alim).put()
        # ExpenseCategory(name= "Poisson", parentCategory=alim).put()
        # ExpenseCategory(name= "Cremerie", parentCategory=alim).put()
        # ExpenseCategory(name= "Traiteur", parentCategory=alim).put()
        # ExpenseCategory(name= "Boulangerie-Patisserie", parentCategory=alim).put()
        # ExpenseCategory(name= "Epicerie salé", parentCategory=alim).put()
        # ExpenseCategory(name= "Epicerie sucré", parentCategory=alim).put()
        # ExpenseCategory(name= "Surgeles", parentCategory=alim).put()
        # ExpenseCategory(name= "Vins et Bulles", parentCategory=alim).put()
        # ExpenseCategory(name= "Alcool", parentCategory=alim).put()
        # ExpenseCategory(name= "Boissons", parentCategory=alim).put()
        
        self.response.write("Bonjour c'est dans la boite.")
        pass
        
app = webapp2.WSGIApplication([
    ('/list', ExpensesPage),
    # ('/feed', FeedData),
    ('/', AddExpense),
    ('/balance', BalancePage),
    ('/remove', RemoveEntity),
    ('/disable', DisableEntity),
    ('/toBuy', ToBuyPage),
    ('/toBuyAdd', ToBuyAddPage),
    
    
], debug=True)