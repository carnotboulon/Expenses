from bs4 import BeautifulSoup
import urllib, re, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

bro = webdriver.Firefox()
bro.get('http://shop.delhaize.be/fr-be/promotions/search?intcmp=Ban_DD_w25Rose_Saving_Banner_Be_Fr_Promos_BanBotPromoLP_Nav_Promotio_NA')
bro.maximize_window()

bro.find_element_by_class_name("load_all_products").click()
bro.implicitly_wait(10)
source = bro.find_element_by_class_name("listingGridPage").get_attribute('innerHTML')
soup = BeautifulSoup(source,"html.parser")
promosHTML = soup.find_all('div', {'class':"prod_grid_has_promotion"})
print len(promosHTML)


bro.find_element_by_class_name("load_all_products").click()
bro.implicitly_wait(10)
source = bro.find_element_by_class_name("listingGridPage").get_attribute('innerHTML')
soup = BeautifulSoup(source,"html.parser")
promosHTML = soup.find_all('div', {'class':"prod_grid_has_promotion"})
print len(promosHTML)

bro.find_element_by_class_name("load_all_products").click()
bro.implicitly_wait(20)
source = bro.find_element_by_class_name("listingGridPage").get_attribute('innerHTML')
soup = BeautifulSoup(source,"html.parser")
promosHTML = soup.find_all('div', {'class':"prod_grid_has_promotion"})
print len(promosHTML)

# bro.find_element_by_class_name("load_all_products").click()
# bro.implicitly_wait(5)
# # source = bro.page_source  # Does not work. Load only initial page.
# # source = bro.execute_script("return document.documentElement.outerHTML") # Does not work. Load only initial page.
# # source = bro.find_element_by_class_name("listingGridPage").get_attribute('innerHTML')   # this one works!
# source = bro.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
# soup = BeautifulSoup(source,"html.parser")
# promosHTML = soup.find_all('div', {'class':"prod_grid_has_promotion"})
# print len(promosHTML)



promos = []
for (i,promoHTML) in enumerate(promosHTML):
    
    
    # try:
         
        
    promo = {}
    promo["promoType"] = promoHTML.find("a",{"class":"promoLink"})["promodescription"]
    promoDetails = promoHTML.find("div",{"class":"details"})
    promo["marque"] = promoDetails.find("span",{"class":"manufacturerName"}).get_text().strip()
    promo["produit"] = promoDetails.find("a",{"class":"productInformation"}).get_text().strip()
    print "%s >> %s" % (i, promo["marque"])
    # promo["category"] = promoDetails.find("a",{"class":"productInformation"})["href"].split("/")[2]
    # promo["subcat"] = promoDetails.find("a",{"class":"productInformation"})["href"].split("/")[3]
    # promo["prix"] = promoDetails.find(id="totalint").get_text().strip() + "," + promoDetails.find(id="totalfraction").get_text().strip()
    # promo["packaging"] =  promoDetails.find("label",{"class":re.compile("prod_desciption")})
    promos.append(promo)
    # print "len = %s" % len(promos)
    # except:
        # pass
print "%s promos found." % len(promos)
# print "Last promos = %s >>> %s" % (promos[-1]["marque"], promos[-1]["prix"])

