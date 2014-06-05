from django.contrib import admin
from lectures.models import User, Course, Lecture, Slide, SlidePlay, Behavior

admin.site.register(User)
admin.site.register(Course)
admin.site.register(Lecture)
admin.site.register(Slide)
admin.site.register(SlidePlay)
admin.site.register(Behavior)
