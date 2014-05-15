import csv
import json
import collections, datetime
from django.utils.timezone import utc
from models import *
from django.db.models import Count

lecture = '6-5'
map_slides = {}

def getArrayFromCsv(csvFileName):
	content = []
	headers = None

	f = open(csvFileName, "rU")
	reader=csv.reader(f)
	for row in reader:
		if reader.line_num == 1:
			"""
			If we are on the first line, create the headers list from the first row
			by taking a slice from item 1  as we don't need the very first header.
			"""
			headers = row[0:]
		else:
			"""
			Otherwise, the key in the content dictionary is the first item in the
			row and we can create the sub-dictionary by using the zip() function.
			We also know that the stabling entry is a comma separated list of names
			so we split it into a list for easier processing.
			"""
			content.append(dict(zip(headers, row[0:])))
	f.close()
	return content

def getArrayFromChunks(f):
	content = []
	headers = None
	reader=csv.reader(f.read().splitlines())
	for row in reader:
		if reader.line_num == 1:
			"""
			If we are on the first line, create the headers list from the first row
			by taking a slice from item 1  as we don't need the very first header.
			"""
			headers = row[0:]
		else:
			"""
			Otherwise, the key in the content dictionary is the first item in the
			row and we can create the sub-dictionary by using the zip() function.
			We also know that the stabling entry is a comma separated list of names
			so we split it into a list for easier processing.
			"""
			content.append(dict(zip(headers, row[0:])))
	return content

def filterByUser(content, userId):
	newContent = []
	for row in content:
		if(row['user'] == userId):
			newContent.append(row)
	return newContent

def importLectures():
	content = getArrayFromCsv('lectures.csv')

	for row in content:
		combine = row['title'].split(' - ')[0].split(' ')[1].split('.')
		week = int(combine[0])
		week_order = int(combine[1])
		Lecture(name = row['title'], week = week, week_order = week_order,
			latest_modified = datetime.datetime.fromtimestamp(float(row['last_updated'])).replace(tzinfo=utc),
			length = int(float(row['video_length'])), nonclick_rate = 0, original_id = int(row['id']),
			course = Course.objects.last()).save()

def importUsers():
	content = getArrayFromCsv('users.csv')

	for row in content:
		User(user_id=row['user_id'], session_user_id = row['session_user_id'], eventing_user_id = row['eventing_user_id'],
			country_code = row['country_code'], country_name = row['country_name']).save()

def importSlides(content, week, week_order):
	l = Lecture.objects.filter(week=int(week), week_order=int(week_order))[0]
	for row in content:
		content_order = int(row['order'])
		content_type = row['type']
		slds = Slide.objects.filter(lecture = l, content_order = content_order, content_type = content_type)
		
		if len(slds) == 0:
			image_url = row['image_url']
			content_name = {
				'q': 'quiz',
				's': 'slide',
				'd': 'demo',
			}[row['type']]

			s = Slide(image_url = image_url, content_name = content_name, content_type = content_type,
				order = -1, content_order = content_order,
				lecture = l)
			s.save()
		else:
			s = slds[0]
		print s
		SlidePlay(slide = s, start_time = int(row['start_time']), end_time = int(row['end_time']), order = int(row['id'])).save()
	count = 1
	for play in SlidePlay.objects.order_by('start_time'):
		if play.slide.order == -1:
			play.slide.order = count
			play.slide.save()
			count += 1
	l.slides_imported = True
	l.save()

def importBehaviors(content, week, week_order):
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
		# Add seeks
		if eventType == 'seeked':
			if user not in seek_users:
				seek_users.append(user)
			source_time = round(float(row['seekFrom']))
			target_time = round(float(row['seekTo']))
			start_plays = SlidePlay.objects.filter(slide__lecture__week = int(week), slide__lecture__week_order = int(week_order),
				start_time__lte = source_time, end_time__gte = source_time)
			end_plays = SlidePlay.objects.filter(slide__lecture__week = int(week), slide__lecture__week_order = int(week_order),
				start_time__lte = target_time, end_time__gte = target_time)

			if len(start_plays) != 1 or len(end_plays) != 1:
				print 'more than 1 result: wrong slideplay data!'
				continue

			sk = Behavior(user = u, event_type = eventType, seek_type = row['seekType'], pause_state = (row['pauseState'] == 'True'),
				init_time = datetime.datetime.fromtimestamp(float(row['initTime']) / 1e3).replace(tzinfo=utc),
				event_time = datetime.datetime.fromtimestamp(float(row['eventTime']) / 1e3).replace(tzinfo=utc),
				source_time = source_time, target_time = target_time, play_end = (row['pauseType'] == 'PLAYEND'),
				playback_rate = float(row['playbackRate']), prev_playback_rate = prev_rate, duration = 0,
				source = start_plays[0], target = end_plays[0])
			sk.save()
		# ignore ratechange
		# elif eventType == 'ratechange':
		# 	continue
		# add pauses
		else:
			occur_time = round(float(row['currentTime']))
			duration = 0
			if eventType == 'pause':
				if row['pauseDuration'] != 'NA':
					duration = round(float(row['pauseDuration']))

			occur_plays = SlidePlay.objects.filter(slide__lecture__week = int(week), slide__lecture__week_order = int(week_order),
				start_time__lte = occur_time, end_time__gte = occur_time)

			if len(occur_plays) != 1:
				print 'more than 1 result: wrong slideplay data!'
				continue

			ps = Behavior(user = u, event_type = eventType, seek_type = '', pause_state = (row['pauseState'] == 'True'),
				init_time = datetime.datetime.fromtimestamp(float(row['initTime']) / 1e3).replace(tzinfo=utc),
				event_time = datetime.datetime.fromtimestamp(float(row['eventTime']) / 1e3).replace(tzinfo=utc),
				source_time = occur_time, target_time = occur_time, play_end = (row['pauseType'] == 'PLAYEND'),
				playback_rate = float(row['playbackRate']), prev_playback_rate = prev_rate, duration = duration,
				source = occur_plays[0], target = occur_plays[0])

			# ps = Pause(user = u, pause_state = (row['pauseState'] == 'True'), play_end = (row['pauseType'] == 'PLAYEND'),
			# 	event_type = eventType, seek_type = '',
			# 	init_time = datetime.datetime.fromtimestamp(float(row['initTime']) / 1e3).replace(tzinfo=utc),
			# 	event_time = datetime.datetime.fromtimestamp(float(row['eventTime']) / 1e3).replace(tzinfo=utc),
			# 	occur_time = occur_time, playback_rate = float(row['playbackRate']), duration = duration,
			# 	place = occur_plays[0])
			ps.save()
		prev_row = row

	# Calc nonclick_rate
	l = Lecture.objects.filter(week = int(week), week_order = int(week_order))[0]
	l.nonclick_rate = int(round((len(users) - len(seek_users)) * 1.0 / len(users) * 100))
	l.save()

def runImport():
	lectures = Lecture.objects.all()
	for lecture in lectures:
		importSeeks(lecture.week + '-' + lecture.week_order)

def lecture_data(lecture):
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])

	nodes = []
	links = []

	slides = Slide.objects.filter(lecture__week = week, lecture__week_order = week_order)

	for slide in slides:
		this_node = slide.order - 1
		fw_node = slide.order - 1 + len(slides)
		bw_node = slide.order - 1 + len(slides) * 2
		# node on skeleton
		nodes.append({'name': this_node, 'out': slide.throughput_out(),
			'slide': slide.content_name + ' ' + str(slide.content_order), 'type': slide.content_type,
			'in': slide.throughput_in(), 'url': slide.image_url, 'order': slide.order - 1,
			'content_order': slide.content_order, 'y': 0})
		# self FW node
		nodes.append({'name': fw_node, 'out': slide.throughput_out(),
			'slide': slide.content_name + ' ' + str(slide.content_order), 'type': slide.content_type,
			'in': slide.throughput_in(), 'url': slide.image_url, 'order': slide.order - 1,
			'content_order': slide.content_order, 'y': -1})
		# self BW node
		nodes.append({'name': bw_node, 'out': slide.throughput_out(),
			'slide': slide.content_name + ' ' + str(slide.content_order), 'type': slide.content_type,
			'in': slide.throughput_in(), 'url': slide.image_url, 'order': slide.order - 1,
			'content_order': slide.content_order, 'y': 1})

		for slide2 in Slide.objects.filter(lecture__week = week, lecture__week_order = week_order):
			if slide == slide2:
				strength_bw = len(Behavior.objects.filter(event_type = 'seeked', seek_type = 'BW',
					source__slide = slide, target__slide = slide2))
				links.append({'source': this_node, 'target': bw_node, 'strength': strength_bw, 'type': 'BW'})

				strength_fw = len(Behavior.objects.filter(event_type = 'seeked', seek_type = 'FW',
					source__slide = slide, target__slide = slide2))
				links.append({'source': this_node, 'target': fw_node, 'strength': strength_fw, 'type': 'FW'})
			else:
				strength = len(Behavior.objects.filter(event_type = 'seeked', source__slide = slide, target__slide = slide2))
				if slide.order > slide2.order:
					seek_type = 'BW'
				else:
					seek_type = 'FW'
				if strength > 0:
					links.append({'source': this_node, 'target': slide2.order - 1, 'strength': strength, 'type': seek_type})

	nodes = sorted(nodes, key=lambda x: x['name'])
	dataDict = {'nodes': nodes, 'links': links}
	return dataDict

def convertTime(intRep):
	minute = intRep / 60
	second = intRep % 60
	str_sec = str(second)
	if second < 10:
		str_sec = '0' + str(second)
	return str(minute) + ':' + str_sec

def draw_node(circles, line_links, order, type, text, link_group):
	count = circles[-1]['name']
	x = circles[-1]['x']
	y = circles[-1]['y']
	if order != x:
		if len(circles) > 1 and (circles[-2]['x'] - x) * (x - order) < 0:
			y += 1
			count += 1
			circles.append({'name': count, 'x': x, 'y': y, 'time': '', 'type': 'virtual'})
			line_links.append({'source': count - 1, 'target': count, 'group': link_group})
			count += 1
			circles.append({'name': count, 'x': order, 'y': y, 'time': '', 'type': 'virtual'})
			line_links.append({'source': count - 1, 'target': count, 'group': link_group})
			y += 1
	else:
		y += 1
	count += 1
	circles.append({'name': count, 'x': order, 'y': y, 'time': text, 'type': type})
	line_links.append({'source': count - 1, 'target': count, 'group': link_group})

def draw_slides(slideplays):
	nodes = []
	countNodes = {}
	for play in slideplays:
		suffix = ''
		if play.slide_id in countNodes.keys():
			suffix = str(unichr(ord('A') + countNodes[play.slide_id]))
			countNodes[play.slide_id] += 1
		else:
			countNodes[play.slide_id] = 1
		nodes.append({'name': play.order, 'out': play.throughput_out(),
			'slide': play.slide.content_name + ' ' + str(play.slide.content_order) + suffix,
			'type': play.slide.content_type, 'in': play.slide.throughput_in(), 'image_url': play.slide.image_url})
	return sorted(nodes, key=lambda x: x['name'])

def draw_slides_slide(slides):
	nodes = []
	for slide in slides:
		nodes.append({'name': slide.order, 'out': slide.throughput_out(),
			'slide': slide.content_name + ' ' + str(slide.content_order),
			'type': slide.content_type, 'in': slide.throughput_in(), 'image_url': slide.image_url})
	return sorted(nodes, key=lambda x: x['name'])


def behaviors_by_user(eventing_user_id, lecture):
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])

	slideplays = SlidePlay.objects.filter(slide__lecture__week = week, slide__lecture__week_order = week_order).order_by('order')
	# for top slides
	nodes = draw_slides(slideplays)

	# for flow
	user_behaviors = Behavior.objects.filter(~models.Q(event_type = 'play'), user__eventing_user_id = eventing_user_id,
		source__slide__lecture__week = week, source__slide__lecture__week_order = week_order).order_by('id')
	
	deltas = []
	for behavior in user_behaviors:
		delta = behavior.event_time - behavior.init_time
		deltas.append(int(delta.total_seconds()))
	
	circles = []
	line_links = []	# Line link abbr: v = virtual, d = discrete, r = continuous
	circles.append({'name': nodes[0]['name'], 'x': 1, 'y': 0, 'time': '0:00', 'type': 'visit'})

	for i in range(0, len(user_behaviors)):
		behavior = user_behaviors[i]
		if i == 0:
			prev_event_time = behavior.init_time
		else:
			prev_event_time = user_behaviors[i - 1].event_time
		x_source = behavior.source.order
		x_target = behavior.target.order
		if behavior.event_type == "seeked":
			before_group = 'v'
			link_group = behavior.seek_type
			if i > 0 and deltas[i] - deltas[i - 1] < 10 and user_behaviors[i - 1].event_type == "seeked":
				before_group = 'c'
				link_group = 'c'
				line_links[-1]['group'] = 'c'
			draw_node(circles, line_links, x_source, behavior.event_type, convertTime(deltas[i]), before_group)
			draw_node(circles, line_links, x_target, 'dest', '', link_group)

		else: # event is paused / changerate
			if behavior.play_end:
				text = 'End'
			else:
				text = convertTime(deltas[i])
			draw_node(circles, line_links, x_source, behavior.event_type, text, 'v')
			if behavior.event_type == 'ratechange':
				circles[-1]['rate'] = float(behavior.playback_rate)
				circles[-1]['prev_rate'] = float(behavior.prev_playback_rate)
			else:
				circles[-1]['duration'] = behavior.duration

	return {'nodes': nodes, 'circles': circles, 'line_links': line_links}

# To refactor: duplicate above
def behaviors_by_user_slide(eventing_user_id, lecture):
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	slides = Slide.objects.filter(lecture__week = week, lecture__week_order = week_order).order_by('order')

	# for top slides
	nodes = draw_slides_slide(slides)

	# for flow
	user_behaviors = Behavior.objects.filter(~models.Q(event_type = 'play'), user__eventing_user_id = eventing_user_id,
		source__slide__lecture__week = week, source__slide__lecture__week_order = week_order).order_by('id')
	
	deltas = []
	for behavior in user_behaviors:
		delta = behavior.event_time - behavior.init_time
		deltas.append(int(delta.total_seconds()))
	
	circles = []
	line_links = []	# Line link abbr: v = virtual, d = discrete, r = continuous
	circles.append({'name': nodes[0]['name'], 'x': 1, 'y': 0, 'time': '0:00', 'type': 'visit'})

	for i in range(0, len(user_behaviors)):
		behavior = user_behaviors[i]
		if i == 0:
			prev_event_time = behavior.init_time
		else:
			prev_event_time = user_behaviors[i - 1].event_time
		x_source = behavior.source.slide.order
		x_target = behavior.target.slide.order
		if behavior.event_type == "seeked":
			before_group = 'v'
			link_group = behavior.seek_type
			if i > 0 and deltas[i] - deltas[i - 1] < 10 and user_behaviors[i - 1].event_type == "seeked":
				before_group = 'c'
				link_group = 'c'
				line_links[-1]['group'] = 'c'
			draw_node(circles, line_links, x_source, behavior.event_type, convertTime(deltas[i]), before_group)
			draw_node(circles, line_links, x_target, 'dest', '', link_group)

		else: # event is paused / changerate
			if behavior.play_end:
				text = 'End'
			else:
				text = convertTime(deltas[i])
			draw_node(circles, line_links, x_source, behavior.event_type, text, 'v')
			if behavior.event_type == 'ratechange':
				circles[-1]['rate'] = float(behavior.playback_rate)
				circles[-1]['prev_rate'] = float(behavior.prev_playback_rate)
			else:
				circles[-1]['duration'] = behavior.duration

	return {'nodes': nodes, 'circles': circles, 'line_links': line_links}

def top_balanced(week, week_order, k):
	top_seeks = top_seeks(week, week_order, 2 * k)
	top_pauses = top_pauses(week, week_order, 2 * k)
	top_balanced = []
	for seek in top_seeks:
		if seek in top_pauses:
			top_balanced.append(seek)
	return top_balanced

def top_seeks(lecture, k):
	if lecture == '':
		return []
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	results = []
	for u in User.objects.annotate(num_seeks = Count('behavior'))\
		.filter(num_seeks__gt=0, behavior__event_type='seeked', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
		.order_by('-num_seeks')[:k]:
		results.append(u.eventing_user_id)
	return results

def top_pauses(lecture, k):
	if lecture == '':
		return []
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	results = []
	for u in User.objects.annotate(num_pauses = Count('behavior'))\
		.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
		.order_by('-num_pauses')[:k]:
		results.append(u.eventing_user_id)
	return results

def top_ratechanges(lecture, k):
	if lecture == '':
		return []
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	results = []
	for u in User.objects.annotate(num_changes = Count('behavior'))\
		.filter(num_changes__gt=0, behavior__event_type='ratechange', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
		.order_by('-num_changes')[:k]:
		results.append(u.eventing_user_id)
	return results

def top_seeks_playrate(lecture, k, rate):
	if lecture == '':
		return []
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	results = []
	for u in User.objects.annotate(num_seeks = Count('behavior'))\
		.filter(num_seeks__gt=0, behavior__event_type='seeked', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
			behavior__playback_rate = rate)\
		.order_by('-num_seeks')[:k]:
		results.append(u.eventing_user_id)
	return results

def top_pauses_playrate(lecture, k, rate):
	if lecture == '':
		return []
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	results = []
	for u in User.objects.annotate(num_pauses = Count('behavior'))\
		.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
			behavior__playback_rate = rate)\
		.order_by('-num_pauses')[:k]:
		results.append(u.eventing_user_id)
	return results

def handle_slides_file(slides_f):
	# get name
	tokens = slides_f.name.split('.')[0].split('_')[0].split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])

	# get content
	content = getArrayFromChunks(slides_f)
	importSlides(content, week, week_order)

def handle_clickstream_file(slides_f):
	tokens = slides_f.name.split('.')[0].split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	content = getArrayFromChunks(slides_f)
	importBehaviors(content, week, week_order)

