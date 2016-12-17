from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^add', views.add, name='add'),
    url(r'^download', views.download, name='download'),
    url(r'^balance', views.balance, name='balance'),
]