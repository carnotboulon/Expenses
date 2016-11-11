import requests
from BeautifulSoup import BeautifulSoup

class SessionGoogle:
    def __init__(self, url_login, url_auth, login, pwd):
        self.ses = requests.session()
        login_html = self.ses.get(url_login)
        soup_login = BeautifulSoup(login_html.content).find('form').findAll('input')
        my_dict = {}
        for u in soup_login:
            if u.has_key('value') and u.has_key('name'):
                my_dict[u['name']] = u['value']
        # override the inputs without login and pwd:
        my_dict['Email'] = "arnaudboland@gmail.com"
        my_dict['Passwd'] = "Carnot_2412.gG"
        self.ses.post(url_auth, data=my_dict)

    def get(self, URL):
        return self.ses.get(URL).content
        
    def getFormFields(self, url):
        form = self.ses.get(url)
        soup_login = BeautifulSoup(form.content).find('form').findAll('input')
        my_dict = {}
        for u in soup_login:
            if u.has_key('value') and u.has_key('name'):
                my_dict[u['name']] = u['value']
        return my_dict
        
        
url_login = "https://accounts.google.com/ServiceLogin"
url_auth = "https://accounts.google.com/ServiceLoginAuth"
session = googleAuth.SessionGoogle(url_login, url_auth, "myGoogleLogin", "myPassword")
# f = open("testGoogle.html","w")
# f.write(session.get("http://bandpmoney.appspot.com").encode("utf-8"))
# f.close()



