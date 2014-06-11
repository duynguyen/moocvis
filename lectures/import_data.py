import csv, json, collections, datetime, time
from django.utils.timezone import utc
from models import *
from clickstream_handler import *

def import_anonymous_behaviors(week, week_order):
	# lectures = Lecture.objects.filter(course__id=1).order_by('week', 'week_order')
	lectures = Lecture.objects.filter(course__id=1, week=week, week_order=week_order)
	for lecture in lectures:

		content = getArrayFromCsv('files/lectures/' + str(lecture.week) + '-' + str(lecture.week_order) + '.csv')
		# mocking slide /slideplay
		slide = Slide(lecture=lecture, image_url="http://www.google.com", order=0, content_order=0, content_type="f", content_name="fake")
		slide.save()
		slideplay_source = SlidePlay(slide=slide, start_time=-1, end_time=-1, order=0)
		slideplay_source.save()
		slideplay_target = SlidePlay(slide=slide, start_time=-1, end_time=-1, order=1)
		slideplay_target.save()
		users = []
		seek_users = []
		prev_row = None
		for row in content:
			# Get nonclick users
			user = row['user']
			eventType = row['eventType']
			if user not in users:
				users.append(user)

			u = User.objects.filter(eventing_user_id = user)[0]
			if u == None:
				u = User(session_user_id = 'new_user', user_id = -1, eventing_user_id = user)
				u.save()
			# process playback_rate / prev_playback_rate
			if not prev_row:
				prev_row = row
			if user == prev_row['user']:
				prev_rate = prev_row['playbackRate']
			else:
				prev_rate = row['playbackRate']
			print datetime.datetime.fromtimestamp(float(row['eventTime']) / 1e3).replace(tzinfo=utc)
			# Add seeks
			if eventType == 'seeked':
				if user not in seek_users:
					seek_users.append(user)
				source_time = round(float(row['seekFrom']))
				target_time = round(float(row['seekTo']))

				sk = Behavior(user = u, event_type = eventType, seek_type = row['seekType'], pause_state = (row['pauseState'] == 'True'),
					init_time = datetime.datetime.fromtimestamp(float(row['initTime']) / 1e3).replace(tzinfo=utc),
					event_time = datetime.datetime.fromtimestamp(float(row['eventTime']) / 1e3).replace(tzinfo=utc),
					source_time = source_time, target_time = target_time, play_end = (row['pauseType'] == 'PLAYEND'),
					playback_rate = float(row['playbackRate']), prev_playback_rate = prev_rate, duration = 0,
					source = slideplay_source, target = slideplay_target)
				sk.save()
			elif not row['pauseType'] == 'DEFAULT':
				occur_time = round(float(row['currentTime']))
				duration = 0
				if eventType == 'pause':
					if row['pauseDuration'] != 'NA':
						duration = round(float(row['pauseDuration']))

				ps = Behavior(user = u, event_type = eventType, seek_type = '', pause_state = (row['pauseState'] == 'True'),
					init_time = datetime.datetime.fromtimestamp(float(row['initTime']) / 1e3).replace(tzinfo=utc),
					event_time = datetime.datetime.fromtimestamp(float(row['eventTime']) / 1e3).replace(tzinfo=utc),
					source_time = occur_time, target_time = occur_time, play_end = (row['pauseType'] == 'PLAYEND'),
					playback_rate = float(row['playbackRate']), prev_playback_rate = prev_rate, duration = duration,
					source = slideplay_source, target = slideplay_target)

				ps.save()
			prev_row = row

def import_behaviors_slideplay(week, week_order):
	behaviors = Behavior.objects.filter(source__slide__lecture__week=week, source__slide__lecture__week_order=week_order)
	for behavior in behaviors:
		print behavior.event_time
		# Add seeks
		source_time = behavior.source_time
		target_time = behavior.target_time
		start_plays = SlidePlay.objects.filter(slide__lecture__week = week, slide__lecture__week_order = week_order,
			start_time__lte = source_time, end_time__gte = source_time)
		end_plays = SlidePlay.objects.filter(slide__lecture__week = week, slide__lecture__week_order = week_order,
			start_time__lte = target_time, end_time__gte = target_time)

		if len(start_plays) != 1 or len(end_plays) != 1:
			print 'more than 1 result: wrong slideplay data!'
			print len(start_plays)
			print len(end_plays)
			print behavior.source_time
			print behavior.target_time
			exit()
			continue
		behavior.source = start_plays[0]
		behavior.target = end_plays[0]
		behavior.save()

		# sk = Behavior(user = u, event_type = eventType, seek_type = row['seekType'], pause_state = (row['pauseState'] == 'True'),
		# 	init_time = datetime.datetime.fromtimestamp(float(row['initTime']) / 1e3).replace(tzinfo=utc),
		# 	event_time = datetime.datetime.fromtimestamp(float(row['eventTime']) / 1e3).replace(tzinfo=utc),
		# 	source_time = source_time, target_time = target_time, play_end = (row['pauseType'] == 'PLAYEND'),
		# 	playback_rate = float(row['playbackRate']), prev_playback_rate = prev_rate, duration = 0,
		# 	source = start_plays[0], target = end_plays[0])
		# sk.save()

	# Calc nonclick_rate
	l = Lecture.objects.filter(week = week, week_order = week_order)[0]
	total_u = Behavior.objects.filter(source__slide__lecture__week=week,
		source__slide__lecture__week_order=week_order).values('user').distinct().count()
	seeked_u = Behavior.objects.filter(event_type='seeked', source__slide__lecture__week=week,
		source__slide__lecture__week_order=week_order).values('user').distinct().count()
	l.nonclick_rate = int(round((total_u - seeked_u) * 1.0 / total_u * 100))
	l.save()

	SlidePlay.objects.filter(slide__lecture__week=week, slide__lecture__week_order=week_order, slide__content_type='f').delete()
	Slide.objects.filter(lecture__week=week, lecture__week_order=week_order, content_type='f').delete()
