from django.contrib import admin
from lectures.models import User, Course, Lecture, Slide, Behavior

admin.site.register(User)
admin.site.register(Course)
admin.site.register(Lecture)
admin.site.register(Slide)
admin.site.register(Behavior)
