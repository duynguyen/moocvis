from django.db import models

class User(models.Model):
	user_id = models.IntegerField()
	session_user_id = models.CharField(max_length=80)
	eventing_user_id = models.CharField(max_length=80)
	country_code = models.CharField(max_length=4, null=True)
	country_name = models.CharField(max_length=255, null=True)
	grade = models.DecimalField(max_digits=5, decimal_places=2, null=True)
	userclass = models.CharField(max_length=80, null=True)
	achievement = models.CharField(max_length=80, null=True)

	def most_active(self, week, week_order):
		Behavior.objects.filter(user = self)

class Course(models.Model):
	name = models.CharField(max_length=80)

	def __unicode__(self):
		return self.name

class Lecture(models.Model):
	name = models.CharField(max_length=80)
	week = models.SmallIntegerField()
	week_order = models.SmallIntegerField()
	length = models.IntegerField()
	latest_modified = models.DateTimeField()
	nonclick_rate = models.SmallIntegerField()
	course = models.ForeignKey(Course)
	slides_imported = models.BooleanField(default=False)
	original_id = models.SmallIntegerField()

	def __unicode__(self):
		return u'%s / Lecture %s-%s' % (self.course.name, self.week, self.week_order)

class Slide(models.Model):
	image_url = models.URLField()
	lecture = models.ForeignKey(Lecture)
	content_type = models.CharField(max_length=1)
	content_name = models.CharField(max_length=16)
	order = models.SmallIntegerField()
	content_order = models.SmallIntegerField()

	def __unicode__(self):
		return u'%s / Lecture %s-%s / %s %s' % (self.lecture.course.name,
        	self.lecture.week, self.lecture.week_order,
        	self.content_name, self.content_order)

	def throughput_in(self):
		total = 0
		for play in self.slideplay_set.all():
			total += play.throughput_in()
		return total
	
	def throughput_out(self):
		total = 0
		for play in self.slideplay_set.all():
			total += play.throughput_out()
		return total

class SlidePlay(models.Model):
	slide = models.ForeignKey(Slide)
	start_time = models.IntegerField()
	end_time = models.IntegerField()
	order = models.SmallIntegerField()

	def throughput_in(self):
		# return len(Seek.objects.filter(~models.Q(source = self), target = self))
		return len(Behavior.objects.filter(event_type = 'seeked', target = self))
	
	def throughput_out(self):
		# return len(Seek.objects.filter(~models.Q(target = self), source = self))
		return len(Behavior.objects.filter(event_type = 'seeked', source = self))

class Behavior(models.Model):
	source = models.ForeignKey(SlidePlay, null=True, related_name='slide_source')
	target = models.ForeignKey(SlidePlay, null=True, related_name='slide_target')
	user = models.ForeignKey(User)
	event_type = models.CharField(max_length=10)
	seek_type = models.CharField(max_length=10, null=True)
	pause_state = models.BooleanField()
	play_end = models.BooleanField(default=False)
	playback_rate = models.DecimalField(max_digits=3, decimal_places=2)
	prev_playback_rate = models.DecimalField(max_digits=3, decimal_places=2)
	init_time = models.DateTimeField()
	event_time = models.DateTimeField()
	source_time = models.IntegerField()
	target_time = models.IntegerField()
	duration = models.IntegerField()

