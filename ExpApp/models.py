#!/usr/local/bin/python
# coding: latin-1

from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Person(models.Model):
	firstname = models.CharField(max_length=32)
	lastname = models.CharField(max_length=32)
	surname = models.CharField(max_length=10)
	email = models.EmailField(max_length=128)
    
	def __str__(self):
		# return "%s: %s %s [%s]" % (self.surname, self.firstname, self.lastname, self.email)
		return "%s" % (self.surname)
    
class Currency(models.Model):
	name = models.CharField(max_length=32)
	code = models.CharField(max_length=3)
	factor = models.DecimalField(max_digits=6, decimal_places=2)
    
	def __str__(self):
		return "%s [%s], Factor=%.2f" % (self.name, self.code, self.factor)
        
class Category(models.Model):
	name = models.CharField(max_length=32)
	active = models.BooleanField()

	def __str__(self):
		if self.active:
			return "%s" % (self.name)
		else:
			return "(%s)" % (self.name)
    
class BankAccount(models.Model):
	owner = models.ManyToManyField(Person)
	name = models.CharField(max_length=32)
	number = models.CharField(max_length=32)
	bank = models.CharField(max_length=32)

	def __str__(self):
		# return "%s [%s], %s" % (self.name, self.number, self.bank)
		return "%s" % (self.name)
    
class PayementType(models.Model):
	name = models.CharField(max_length=32)
    
	def __str__(self):
		return "%s" % (self.name)

class Expense(models.Model):
	date = models.DateField()
	object = models.CharField(max_length=32)
	comment = models.CharField(max_length=200)
    
	price = models.DecimalField(max_digits=8, decimal_places=2)
	currency = models.ForeignKey(Currency, on_delete=models.DO_NOTHING)
    
	categories = models.ManyToManyField(Category)
	account = models.ForeignKey(BankAccount, on_delete=models.DO_NOTHING)
	payType = models.ForeignKey(PayementType, on_delete=models.DO_NOTHING)
    
	beneficiaries = models.ManyToManyField(Person)
    
	recordedBy = models.ForeignKey(Person,related_name = "recorder", on_delete=models.DO_NOTHING)
	recordedOn = models.DateField(auto_now_add=True)
    
	@property
	def nb_beneficiaries(self):
		return len(self.beneficiaries.all())
    
	@property
	def nb_buyers(self):
		return len(self.account.owner.all())
    
	def __str__(self):
		cats = [c.name for c in self.categories.all()]
        
		return "[%s] %s %s" % (self.date, self.object, ",".join(cats))
		
# # Automatisation de creation de raccourcis.
# class Shortcut(models.Model):
	# name = models.CharField(max_length=32)
	# user = models.ManyToManyField(Person)
	# picture = ImageField(upload_to="shortcuts", blank=True, null=True, height_field=400, width_field=400)
	
	# object = models.CharField(max_length=32)
	# comment = models.CharField(max_length=200)
	# price = models.CharField(max_length=32)
	# currency = models.CharField(max_length=3)
	# category = models.CharField(max_length=32)
	# account = models.CharField(max_length=32)
	# payType = models.CharField(max_length=32)
    
	# beneficiaries = models.CharField(max_length=32)