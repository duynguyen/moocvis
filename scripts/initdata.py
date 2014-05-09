#!/usr/bin/env python

from lectures.models import *
from lectures.clickstream_handler import importLectures, importUsers, importSlides, importBehaviors, getArrayFromCsv

Behavior.objects.all().delete()
User.objects.all().delete()
SlidePlay.objects.all().delete()
Slide.objects.all().delete()
Lecture.objects.all().delete()
Course.objects.all().delete()

Course(name="Functional Programming Principles in Scala").save()
importLectures()
importUsers()
importSlides(getArrayFromCsv('6-5_slides.csv'), 6, 5)
importBehaviors(getArrayFromCsv('6-5.csv'), 6, 5)
importSlides(getArrayFromCsv('6-2_slides.csv'), 6, 2)
importBehaviors(getArrayFromCsv('6-2.csv'), 6, 2)