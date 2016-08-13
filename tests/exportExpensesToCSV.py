from google.appengine.ext import ndb
from Expenses import *
import time

expenses_query = Expense.query(ancestor=expensebook_key("BandP")).order(-Expense.date)
expenses = expenses_query.fetch()
expList = []

for exp in expenses:
    expItem = {}
    expItem["date"] = exp.date.__str__()
    expItem["object"] = exp.object
    expItem["price"] = exp.price
    expItem["shop"] = exp.shop.get().name
    expItem["categories"] = [e.get().name for e in exp.categories]
    expItem["account"] = exp.account.get().name
    expItem["buyers"] = [e.get().email for e in exp.buyers]
    expItem["beneficiaries"] = [e.get().email for e in exp.beneficiaries]
    expItem["payType"] = exp.payType.get().type
    
    expList.append(expItem)
    
f = open("ExportDB-%s.csv" % time.strftime("%d%b%y"),"w")
f.write("Date; Object; Price; Shop; Categories; Account; Buyers; Beneficiaries; PayType;\n")
for exp in expList:
    extStr = "%s ; %s ; %s ; %s ; %s ; %s ; %s ; %s ; %s ;\n" % (exp["date"],exp["object"],exp["price"],exp["shop"], ",".join(exp["categories"]), exp["account"], ",".join(exp["buyers"]), ",".join(exp["beneficiaries"]), exp["payType"]) 
    f.write(extStr.encode("utf-8"))
f.close()