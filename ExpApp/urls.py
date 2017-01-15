from django.conf.urls import url

from . import views

app_name = 'expapp'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<expense_number>[0-9]+)/$', views.index, name='index'),
    url(r'^add/(?P<expense_id>[0-9]*)', views.add, name='add'),
    url(r'^delete/(?P<expense_id>[0-9]*)', views.delete, name='delete'),
    url(r'^save/(?P<expense_id>[0-9]*)', views.save, name='save'),
    url(r'^download', views.download, name='download'),
    url(r'^balance', views.balance, name='balance'),
]