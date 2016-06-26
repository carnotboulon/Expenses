from bs4 import BeautifulSoup
import urllib, re, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
bro = webdriver.Firefox()
bro.get('http://shop.delhaize.be/fr-be/promotions/search?intcmp=Ban_DD_w25Rose_Saving_Banner_Be_Fr_Promos_BanBotPromoLP_Nav_Promotio_NA')