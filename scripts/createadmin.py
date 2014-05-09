#!/usr/bin/env python

from django.contrib.auth.models import User
from lectures.clickstream_handler import importLectures, importUsers

if User.objects.count() == 0:
	admin = User.objects.create(username='admin')
	admin.set_password('123456')
	admin.is_superuser = True
	admin.is_staff = True
	admin.save()

Course(name="Functional Programming Principles in Scala").save()
importLectures()
importUsers()
