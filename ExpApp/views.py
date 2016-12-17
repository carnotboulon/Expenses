from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse("Hello, this is the expense list.")
    
def add(request):
    return HttpResponse("Hello, this is the add expense page.")
    
def download(request):
    return HttpResponse("Hello, this is the download page.")

def balance(request):
    return HttpResponse("Hello, this is the balance page.")    