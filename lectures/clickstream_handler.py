import csv, json, collections, datetime, time
from django.utils.timezone import utc
from models import *
from django.db.models import Count, F
import clickstream_handler

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
	content = getArrayFromCsv('files/lectures.csv')

	for row in content:
		combine = row['title'].split(' - ')[0].split(' ')[1].split('.')
		week = int(combine[0])
		week_order = int(combine[1])
		Lecture(name = row['title'], week = week, week_order = week_order,
			latest_modified = datetime.datetime.fromtimestamp(float(row['last_updated'])).replace(tzinfo=utc),
			length = int(float(row['video_length'])), nonclick_rate = 0, original_id = int(row['id']),
			course = Course.objects.last()).save()

def importUsers():
	content = getArrayFromCsv('files/users.csv')

	for row in content:
		User(user_id=row['user_id'], session_user_id = row['session_user_id'], eventing_user_id = row['eventing_user_id'],
			country_code = row['country_code'], country_name = row['country_name']).save()

def importUsersWithStats():
	content = getArrayFromCsv('files/users.csv')

	for row in content:
		grade = None
		if row['grade'] != "NULL":
			grade = float(row['grade'])
		User(user_id=row['user_id'], session_user_id = row['session_user_id'], eventing_user_id = row['eventing_user_id'],
			country_code = row['country_code'], country_name = row['country_name'], grade = grade,
			userclass = row['userclass'], achievement = row['achievement']).save()

def importUsersStats():
	content = getArrayFromCsv('files/users.csv')
	for row in content:
		u_list = User.objects.filter(user_id=int(row['user_id']))
		if u_list and len(u_list) == 1:
			u = u_list[0]
			if row['grade'] != "NULL":
				u.grade = float(row['grade'])
			u.achievement = row['achievement']
			u.userclass = row['userclass']
			print u.achievement
			u.save()
		else:
			print row['user_id']
			print u_list
	# content = getArrayFromCsv('files/progfun_stats.csv')

	# for row in content:
	# 	if row['session'] != 'progfun_001':
	# 		continue
	# 	u_list = User.objects.filter(session_user_id=row['user_id'])
	# 	if u_list and len(u_list) == 1:
	# 		u = u_list[0]
	# 		if row['grade'] != "NA":
	# 			u.grade = round(float(row['grade']), 2)
	# 		u.achievement = row['achievement']
	# 		if row['userclass'] != "NA":
	# 			u.userclass = row['userclass'].lower()
	# 		print u.achievement
	# 		u.save()
	# 	else:
	# 		print row['user_id']
	# 		print u_list

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
		print user
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
	start = int(round(time.time() * 1000))
	userclass_list = ['all', 'active', 'viewers', 'inactive']
	achievement_list = {
		"all": ['all', 'distinction', 'normal', 'none'],
		"active": ['all', 'distinction', 'normal', 'none'],
		"viewers": ["all"],
		"inactive": ["all"],
	}
	# achievement_list = ['all', 'distinction', 'normal', 'none']
	if not lecture:
		return None
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	results = {}

	for userclass in userclass_list:
		slides = Slide.objects.filter(lecture__week = week, lecture__week_order = week_order)

		for achievement in achievement_list[userclass]:
			print userclass + "-" + achievement
			filtered_lectures = Behavior.objects.all()
			# users = User.objects.all()
			if userclass != 'all':
				filtered_lectures = filtered_lectures.filter(user__userclass=userclass)
			# 	users = users.filter(userclass=userclass)
			if achievement != 'all':
				filtered_lectures = filtered_lectures.filter(user__achievement=achievement)
			# 	users = users.filter(achievement=achievement)
			# # num_users = (users.count() or 1)
			# if userclass == 'all' and achievement == 'all':
			# 	num_users = User.objects.filter(behavior__source__slide__lecture__week = week, behavior__source__slide__lecture__week_order = week_order).distinct().count() or 1
			# elif userclass == 'all':
			# 	num_users = User.objects.filter(behavior__source__slide__lecture__week = week, behavior__source__slide__lecture__week_order = week_order, userclass=userclass).distinct().count() or 1
			# elif achievement == 'all':
			# 	num_users = User.objects.filter(behavior__source__slide__lecture__week = week, behavior__source__slide__lecture__week_order = week_order, achievement=achievement).distinct().count() or 1
			# else:
			# 	num_users = User.objects.filter(behavior__source__slide__lecture__week = week, behavior__source__slide__lecture__week_order = week_order, userclass=userclass, achievement=achievement).distinct().count() or 1
			nodes = []
			links = []

			for slide in slides:
				print "slide source " + str(slide.order)
				this_node = slide.order - 1
				fw_node = slide.order - 1 + len(slides)
				bw_node = slide.order - 1 + len(slides) * 2
				# node on skeleton
				nodes.append({'name': this_node, 'out': slide.throughput_out(userclass, achievement),
					'incl': slide.throughput_incl(userclass, achievement),
					'slide': slide.content_name + ' ' + str(slide.content_order), 'type': slide.content_type,
					'in': slide.throughput_in(userclass, achievement), 'url': slide.url(), 'order': slide.order - 1,
					'content_order': slide.content_order, 'y': 0})
				# self FW node
				nodes.append({'name': fw_node, 'out': slide.throughput_out(userclass, achievement),
					'incl': slide.throughput_incl(userclass, achievement),
					'slide': slide.content_name + ' ' + str(slide.content_order), 'type': slide.content_type,
					'in': slide.throughput_in(userclass, achievement), 'url': slide.url(), 'order': slide.order - 1,
					'content_order': slide.content_order, 'y': -1})
				# self BW node
				nodes.append({'name': bw_node, 'out': slide.throughput_out(userclass, achievement),
					'incl': slide.throughput_incl(userclass, achievement),
					'slide': slide.content_name + ' ' + str(slide.content_order), 'type': slide.content_type,
					'in': slide.throughput_in(userclass, achievement), 'url': slide.url(), 'order': slide.order - 1,
					'content_order': slide.content_order, 'y': 1})

				for slide2 in Slide.objects.filter(lecture__week = week, lecture__week_order = week_order):
					print "slide dest " + str(slide2.order)
					if slide == slide2:
						strength_bw = filtered_lectures.filter(event_type = 'seeked', seek_type = 'BW',
							source__slide = slide, target__slide = slide).count()
						links.append({'source': this_node, 'target': bw_node, 'strength': strength_bw, 'type': 'BW'})

						strength_fw = filtered_lectures.filter(event_type = 'seeked', seek_type = 'FW',
							source__slide = slide, target__slide = slide).count()
						links.append({'source': this_node, 'target': fw_node, 'strength': strength_fw, 'type': 'FW'})
					else:
						strength = filtered_lectures.filter(event_type = 'seeked', source__slide = slide, target__slide = slide2).count()
						if slide.order > slide2.order:
							seek_type = 'BW'
						else:
							seek_type = 'FW'
						links.append({'source': this_node, 'target': slide2.order - 1, 'strength': strength, 'type': seek_type})

			nodes = sorted(nodes, key=lambda x: x['name'])
			this_key = userclass + '-' + achievement
			results[this_key] = {'nodes': nodes, 'links': links}

	print int(round(time.time() * 1000)) - start
	return results

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
		nodes.append({'name': play.order, 'slide': play.slide.content_name + ' ' + str(play.slide.content_order) + suffix,
			'type': play.slide.content_type, 'image_url': play.slide.url()})
	return sorted(nodes, key=lambda x: x['name'])

def draw_slides_slide(slides):
	nodes = []
	for slide in slides:
		nodes.append({'name': slide.order, 'slide': slide.content_name + ' ' + str(slide.content_order),
			'type': slide.content_type, 'image_url': slide.url()})
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
				before_group = 'c' + user_behaviors[i - 1].seek_type
				link_group = 'c' + behavior.seek_type
				rev = circles[-1]
				rev_count =  1
				while rev['type'] != 'seeked':
					line_links[len(line_links) - rev_count]['group'] = before_group
					rev_count += 1
					rev = circles[len(circles) - rev_count]
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
		if behavior.play_end and i + 1 < len(user_behaviors):
			circles.append({'name': circles[-1]['name'] + 1, 'x': 1, 'y': circles[-1]['y'] + 1, 'time': '0:00', 'type': 'visit'})

	user_info = {}
	selected_users = User.objects.filter(eventing_user_id=eventing_user_id)
	if len(selected_users) == 1:
		user_info = selected_users[0].to_dict()
	return {'nodes': nodes, 'circles': circles, 'line_links': line_links, "user": user_info}

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
				before_group = 'c' + user_behaviors[i - 1].seek_type
				link_group = 'c' + behavior.seek_type
				rev = circles[-1]
				rev_count =  1
				while rev['type'] != 'seeked':
					line_links[len(line_links) - rev_count]['group'] = before_group
					rev_count += 1
					rev = circles[len(circles) - rev_count]
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
		if behavior.play_end and i + 1 < len(user_behaviors):
			circles.append({'name': circles[-1]['name'] + 1, 'x': 1, 'y': circles[-1]['y'] + 1, 'time': '0:00', 'type': 'visit'})

	user_info = {}
	selected_users = User.objects.filter(eventing_user_id=eventing_user_id)
	if len(selected_users) == 1:
		user_info = selected_users[0].to_dict()
	return {'nodes': nodes, 'circles': circles, 'line_links': line_links, "user": user_info}

def top_balanced(week, week_order, k):
	top_seeks = top_seeks(week, week_order, 2 * k)
	top_pauses = top_pauses(week, week_order, 2 * k)
	top_balanced = []
	for seek in top_seeks:
		if seek in top_pauses:
			top_balanced.append(seek)
	return top_balanced

def all(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_changes = Count('behavior'))\
				.filter(num_changes__gt=0).order_by('-num_changes')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_changes = Count('behavior'))\
				.filter(num_changes__gt=0, behavior__playback_rate = float(rate))\
				.order_by('-num_changes')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_changes = Count('behavior'))\
			.filter(num_changes__gt=0, behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_changes')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_changes = Count('behavior'))\
			.filter(num_changes__gt=0, behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_changes')[:k]:
			results.append(u.eventing_user_id)
	return results

def rate_changer(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_changes = Count('behavior'))\
				.filter(num_changes__gt=0, behavior__event_type='ratechange')\
				.order_by('-num_changes')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_changes = Count('behavior'))\
				.filter(num_changes__gt=0, behavior__event_type='ratechange', behavior__playback_rate = float(rate))\
				.order_by('-num_changes')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_changes = Count('behavior'))\
			.filter(num_changes__gt=0, behavior__event_type='ratechange', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_changes')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_changes = Count('behavior'))\
			.filter(num_changes__gt=0, behavior__event_type='ratechange', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_changes')[:k]:
			results.append(u.eventing_user_id)
	return results

def top_seeks(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_seeks = Count('behavior'))\
				.filter(num_seeks__gt=0, behavior__event_type='seeked')\
				.order_by('-num_seeks')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_seeks = Count('behavior'))\
				.filter(num_seeks__gt=0, behavior__event_type='seeked', behavior__playback_rate = float(rate))\
				.order_by('-num_seeks')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_seeks = Count('behavior'))\
			.filter(num_seeks__gt=0, behavior__event_type='seeked', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_seeks')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_seeks = Count('behavior'))\
			.filter(num_seeks__gt=0, behavior__event_type='seeked', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_seeks')[:k]:
			results.append(u.eventing_user_id)
	return results

def top_seeks_fw(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_seeks = Count('behavior'))\
				.filter(num_seeks__gt=0, behavior__seek_type='FW').order_by('-num_seeks')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_seeks = Count('behavior'))\
				.filter(num_seeks__gt=0, behavior__seek_type='FW', behavior__playback_rate = float(rate))\
				.order_by('-num_seeks')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_seeks = Count('behavior'))\
			.filter(num_seeks__gt=0, behavior__seek_type='FW', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_seeks')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_seeks = Count('behavior'))\
			.filter(num_seeks__gt=0, behavior__seek_type='FW', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_seeks')[:k]:
			results.append(u.eventing_user_id)
	return results

def top_seeks_bw(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_seeks = Count('behavior'))\
				.filter(num_seeks__gt=0, behavior__seek_type='BW').order_by('-num_seeks')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_seeks = Count('behavior'))\
				.filter(num_seeks__gt=0, behavior__seek_type='BW', behavior__playback_rate = float(rate))\
				.order_by('-num_seeks')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_seeks = Count('behavior'))\
			.filter(num_seeks__gt=0, behavior__seek_type='BW', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_seeks')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_seeks = Count('behavior'))\
			.filter(num_seeks__gt=0, behavior__seek_type='BW', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_seeks')[:k]:
			results.append(u.eventing_user_id)
	return results

def top_pauses(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_pauses = Count('behavior'))\
				.filter(num_pauses__gt=0, behavior__event_type='pause').order_by('-num_pauses')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_pauses = Count('behavior'))\
				.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__playback_rate = float(rate))\
				.order_by('-num_pauses')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_pauses = Count('behavior'))\
			.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_pauses')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_pauses = Count('behavior'))\
			.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_pauses')[:k]:
			results.append(u.eventing_user_id)
	return results

# TODO
def highest_rate(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_pauses = Count('behavior'))\
				.filter(num_pauses__gt=0, behavior__event_type='pause').order_by('-num_pauses')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_pauses = Count('behavior'))\
				.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__playback_rate = float(rate))\
				.order_by('-num_pauses')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_pauses = Count('behavior'))\
			.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_pauses')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_pauses = Count('behavior'))\
			.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_pauses')[:k]:
			results.append(u.eventing_user_id)
	return results

# TODO
def lowest_rate(lecture, k, rate):
	results = []
	if lecture == '':
		if rate == 'any':
			for u in User.objects.annotate(num_pauses = Count('behavior'))\
				.filter(num_pauses__gt=0, behavior__event_type='pause').order_by('-num_pauses')[:k]:
				results.append(u.eventing_user_id)
		else:
			for u in User.objects.annotate(num_pauses = Count('behavior'))\
				.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__playback_rate = float(rate))\
				.order_by('-num_pauses')[:k]:
				results.append(u.eventing_user_id)
		return results
	tokens = lecture.split('-')
	week = int(tokens[0])
	week_order = int(tokens[1])
	if rate == 'any':
		for u in User.objects.annotate(num_pauses = Count('behavior'))\
			.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order)\
			.order_by('-num_pauses')[:k]:
			results.append(u.eventing_user_id)
	else:
		for u in User.objects.annotate(num_pauses = Count('behavior'))\
			.filter(num_pauses__gt=0, behavior__event_type='pause', behavior__source__slide__lecture__week=week, behavior__source__slide__lecture__week_order=week_order,
				behavior__playback_rate = float(rate))\
			.order_by('-num_pauses')[:k]:
			results.append(u.eventing_user_id)
	return results

# def play_at_rate(user_id, week, week_order, rate):
# 	all_behaviors = Behavior.objects.filter(source__slide__lecture__week=week, source__slide__lecture__week_order=week_order,
# 		user__id=user_id).count()
# 	rated_behaviors = Behavior.objects.filter(source__slide__lecture__week=week, source__slide__lecture__week_order=week_order,
# 		user__id=user_id, playback_rate=rate).count()
# 	if rated_behaviors * 1.0 / all_behaviors >= 0.5:
# 		return True
# 	return False

# event-based
def map_json():
	stats = {}
	countries = User.objects.values('country_code').distinct()
	for country in countries:
		country = country['country_code']
		num_users = Behavior.objects.filter(user__country_code=country).values('user').distinct().count()
		num_pauses = Behavior.objects.filter(event_type="pause", user__country_code=country, play_end=False).count()
		num_seeks = Behavior.objects.filter(event_type="seeked", user__country_code=country).count()
		num_seeks_fw = Behavior.objects.filter(seek_type="FW", user__country_code=country).count()
		num_seeks_bw = Behavior.objects.filter(seek_type="BW", user__country_code=country).count()
		num_ratechanges = Behavior.objects.filter(event_type="ratechange", user__country_code=country).count()
		num_uprate = Behavior.objects.filter(event_type="ratechange", user__country_code=country, playback_rate__gt=F('prev_playback_rate')).count()
		num_downrate = Behavior.objects.filter(event_type="ratechange", user__country_code=country, playback_rate__lt=F('prev_playback_rate')).count()
		print country
		print num_uprate
		print num_downrate
		print num_ratechanges
		# behaviorbased
		# stats[country] = {
		# 	"pauses": round(num_pauses * 1.0 / (num_users_pauses or 1), 2),
		# 	"seeks": round(num_seeks * 1.0 / (num_users_seeks or 1), 2),
		# 	"seeks_fw": round(num_seeks_fw * 1.0 / (num_users_seeks_fw or 1), 2),
		# 	"seeks_bw": round(num_seeks_bw * 1.0 / (num_users_seeks_bw or 1), 2),
		# 	"ratechanges": round(num_ratechanges * 1.0 / (num_users_ratechanges or 1), 2),
		# 	"num_users_pauses": num_users_pauses,
		# 	"num_users_seeks": num_users_seeks,
		# 	"num_users_seeks_fw": num_users_seeks_fw,
		# 	"num_users_seeks_bw": num_users_seeks_bw,
		# 	"num_users_ratechanges": num_users_ratechanges,
		# 	"users": num_users,
		# }
		stats[country] = {
			"pauses": round(num_pauses * 1.0 / (num_users or 1), 2),
			"seeks": round(num_seeks * 1.0 / (num_users or 1), 2),
			"seeks_fw": round(num_seeks_fw * 1.0 / (num_users or 1), 2),
			"seeks_bw": round(num_seeks_bw * 1.0 / (num_users or 1), 2),
			"ratechanges": round(num_ratechanges * 1.0 / (num_users or 1), 2),
			"uprate": round(num_uprate * 1.0 / (num_users or 1), 2),
			"downrate": round(num_downrate * 1.0 / (num_users or 1), 2),
			"num_pauses": num_pauses,
			"num_seeks": num_seeks,
			"num_seeks_fw": num_seeks_fw,
			"num_seeks_bw": num_seeks_bw,
			"num_ratechanges": num_ratechanges,
			"num_uprate": num_uprate,
			"num_downrate": num_downrate,
			"users": num_users,
		}
	return stats

# user-based
def map_json():
	stats = {}
	countries = User.objects.values('country_code').distinct()
	for country in countries:
		country = country['country_code']
		num_users = Behavior.objects.filter(user__country_code=country).values('user').distinct().count()
		# collections
		user_uprates = Behavior.objects.filter(event_type="ratechange", playback_rate__gt=F('prev_playback_rate')).values('user').distinct()
		user_downrates = Behavior.objects.filter(event_type="ratechange", playback_rate__lt=F('prev_playback_rate')).values('user').distinct()
		# num_users
		num_users_pauses = User.objects.filter(behavior__event_type='pause', country_code=country, behavior__play_end=False).distinct().count()
		num_users_seeks = User.objects.filter(behavior__event_type='seeked', country_code=country).distinct().count()
		num_users_seeks_fw = User.objects.filter(behavior__seek_type='FW', country_code=country).distinct().count()
		num_users_seeks_bw = User.objects.filter(behavior__seek_type='BW', country_code=country).distinct().count()
		num_users_ratechanges = User.objects.filter(behavior__event_type='ratechange', country_code=country).distinct().count()
		num_users_uprate = User.objects.filter(behavior__event_type='ratechange', country_code=country, id__in=user_uprates).distinct().count()
		num_users_downrate = User.objects.filter(behavior__event_type='ratechange', country_code=country, id__in=user_downrates).distinct().count()
		# userbased
		stats[country] = {
			"pauses": round(num_users_pauses * 100.0 / (num_users or 1), 2),
			"seeks": round(num_users_seeks * 100.0 / (num_users or 1), 2),
			"seeks_fw": round(num_users_seeks_fw * 100.0 / (num_users or 1), 2),
			"seeks_bw": round(num_users_seeks_bw * 100.0 / (num_users or 1), 2),
			"ratechanges": round(num_users_ratechanges * 100.0 / (num_users or 1), 2),
			"uprate": round(num_users_uprate * 100.0 / (num_users or 1), 2),
			"downrate": round(num_users_downrate * 100.0 / (num_users or 1), 2),
			"num_users_pauses": num_users_pauses,
			"num_users_seeks": num_users_seeks,
			"num_users_seeks_fw": num_users_seeks_fw,
			"num_users_seeks_bw": num_users_seeks_bw,
			"num_users_ratechanges": num_users_ratechanges,
			"num_users_uprate": num_users_uprate,
			"num_users_downrate": num_users_downrate,
			"users": num_users,
		}
		print country
		print num_users_uprate
		print num_users_downrate
		print num_users_ratechanges
	return stats

def get_weekly_stats(course_id):
	start = int(round(time.time() * 1000))
	week_numbers = Lecture.objects.filter(course__id=course_id).values('week').distinct().order_by('week')
	weeks = []
	events = ['all', 'seeks', 'pauses', 'ratechanges', 'forward seeks', 'backward seeks']
	results = {}
	for e in events:
		results[e] = []
	for w in week_numbers:
		this_week = 'Week ' + str(w['week'])
		print this_week
		weeks.append(this_week)
		for e in events:
			print e
			week_obj = {}
			week_obj['name'] = this_week
			week_obj['data'] = []
			lectures = Lecture.objects.filter(course__id=course_id, week=w['week']).order_by('week_order')
			for lecture in lectures:
				lecture_obj = {}
				lecture_obj['name'] = str(lecture.week) + '-' + str(lecture.week_order)
				lecture_obj['x'] = lecture.week_order
				lecture_obj['y'] = lecture.week - 1
				lecture_obj['length'] = lecture.length

				count_users = User.objects.filter(behavior__source__slide__lecture__week = lecture.week,
					behavior__source__slide__lecture__week_order = lecture.week_order).distinct().count()
				if e == 'forward seeks':
					count_objs = Behavior.objects.filter(source__slide__lecture__week = lecture.week,
						source__slide__lecture__week_order = lecture.week_order, seek_type='FW').count()
					count_users = User.objects.filter(behavior__source__slide__lecture__week = lecture.week,
						behavior__source__slide__lecture__week_order = lecture.week_order,
						behavior__seek_type='FW').distinct().count()
				elif e == 'backward seeks':
					count_objs = Behavior.objects.filter(source__slide__lecture__week = lecture.week,
						source__slide__lecture__week_order = lecture.week_order, seek_type='BW').count()
					count_users = User.objects.filter(behavior__source__slide__lecture__week = lecture.week,
						behavior__source__slide__lecture__week_order = lecture.week_order,
						behavior__seek_type='BW').distinct().count()
				elif e == 'seeks':
					count_objs = Behavior.objects.filter(source__slide__lecture__week = lecture.week,
						source__slide__lecture__week_order = lecture.week_order, event_type='seeked').count()
					count_users = User.objects.filter(behavior__source__slide__lecture__week = lecture.week,
						behavior__source__slide__lecture__week_order = lecture.week_order,
						behavior__event_type='seeked').distinct().count()
				elif e == 'pauses':
					count_objs = Behavior.objects.filter(source__slide__lecture__week = lecture.week,
						source__slide__lecture__week_order = lecture.week_order, event_type='pause', play_end=False).count()
					count_users = User.objects.filter(behavior__source__slide__lecture__week = lecture.week,
						behavior__source__slide__lecture__week_order = lecture.week_order,
						behavior__event_type='pause', behavior__play_end=False).distinct().count()
				elif e == 'ratechanges':
					count_objs = Behavior.objects.filter(source__slide__lecture__week = lecture.week,
						source__slide__lecture__week_order = lecture.week_order, event_type='ratechange').count()
					count_users = User.objects.filter(behavior__source__slide__lecture__week = lecture.week,
						behavior__source__slide__lecture__week_order = lecture.week_order,
						behavior__event_type='ratechange').distinct().count()
				else:
					count_objs = Behavior.objects.filter(~models.Q(event_type = 'play'), source__slide__lecture__week = lecture.week,
						source__slide__lecture__week_order = lecture.week_order, play_end=False).count()
					count_users = User.objects.filter(behavior__source__slide__lecture__week = lecture.week,
						behavior__source__slide__lecture__week_order = lecture.week_order, behavior__play_end=False).distinct().count()
				print count_objs
				# total
				# lecture_obj['z'] = count_objs
				# average per user
				lecture_obj['z'] = round(count_objs * 1.0 / (count_users or 1), 1)
				# average per user per min
				# lecture_obj['z'] = round(count_objs * 1.0 / (count_users or 1) * 60 / lecture.length, 2)
				print lecture_obj['z']
				week_obj['data'].append(lecture_obj)
			results[e].append(week_obj)
	print int(round(time.time() * 1000)) - start
	return { 'weeks': weeks, 'data': results, 'events': events }

def get_weekly_stats_users(course_id):
	colors = {"Week 1": "orange", "Week 2": "blue", "Week 3": "yellow", "Week 4": "green", "Week 5": "pink", "Week 6": "#bbb", "Week 7": "cyan"}
	start = int(round(time.time() * 1000))
	week_numbers = Lecture.objects.filter(course__id=course_id).values('week').distinct().order_by('week')
	weeks = []
	events = ['all', 'top_seeks', 'top_seeks_fw', 'top_seeks_bw', 'top_pauses', 'rate_changer', 'highest_rate', 'lowest_rate']
	# rates = ['any', '0.5', '0.75', '1.0', '1.25', '1.5', '1.75', '2.0']
	results = {}
	for e in events:
		print e
		results[e] = {}
		results[e]['data'] = []
		users = getattr(clickstream_handler, e)('', 10, "any")
		results[e]['users'] = users
		u_count = 0
		for user in users:
			user_obj = {}
			user_obj['name'] = user
			user_obj['data'] = []
			for w in week_numbers:
				week_order_numbers = Lecture.objects.filter(course__id=course_id, week=w['week']).values('week_order').distinct().order_by('week_order')
				this_week = 'Week ' + str(w['week'])
				print this_week
				if this_week not in weeks:
					weeks.append(this_week)
				# weeks[this_week] = [o['week_order'] for o in week_order_numbers]
				lectures = Lecture.objects.filter(course__id=course_id, week=w['week']).order_by('week_order')
				for lecture in lectures:
					lecture_obj = {}
					lecture_obj['name'] = str(lecture.week) + '-' + str(lecture.week_order)
					# lecture_obj['week'] = this_week
					lecture_obj['color'] = colors[this_week]
					lecture_obj['x'] = lecture.week - 1.6 + (lecture.week_order * 1.0 / len(week_order_numbers))
					lecture_obj['y'] = u_count
					count_objs = Behavior.objects.filter(source__slide__lecture__week = lecture.week,
							source__slide__lecture__week_order = lecture.week_order,
							user__eventing_user_id=user).count()

					# if e == 'seeked forward':
					# 	filtered_objs = filtered_objs.filter(seek_type='FW')
					# elif e == 'seeked backward':
					# 	filtered_objs = filtered_objs.filter(seek_type='BW')
					# elif e != 'all':
					# 	filtered_objs = filtered_objs.filter(event_type=e)
					lecture_obj['z'] = count_objs
					user_obj['data'].append(lecture_obj)
			u_count += 1
			results[e]['data'].append(user_obj)
	print int(round(time.time() * 1000)) - start
	return { 'weeks': weeks, 'data': results, 'events': events }

def get_stats_user(course_id, user_id):
	colors = {"Week 1": "orange", "Week 2": "blue", "Week 3": "yellow", "Week 4": "green", "Week 5": "pink", "Week 6": "#bbb", "Week 7": "cyan"}
	user_obj = {}
	user_obj['name'] = user_id
	user_obj['data'] = []
	week_numbers = Lecture.objects.filter(course__id=course_id).values('week').distinct().order_by('week')
	for w in week_numbers:
		week_order_numbers = Lecture.objects.filter(course__id=course_id, week=w['week']).values('week_order').distinct().order_by('week_order')
		this_week = 'Week ' + str(w['week'])
		lectures = Lecture.objects.filter(course__id=course_id, week=w['week']).order_by('week_order')
		for lecture in lectures:
			lecture_obj = {}
			lecture_obj['name'] = str(lecture.week) + '-' + str(lecture.week_order)
			# lecture_obj['week'] = this_week
			lecture_obj['color'] = colors[this_week]
			lecture_obj['x'] = lecture.week - 1.6 + (lecture.week_order * 1.0 / len(week_order_numbers))
			lecture_obj['y'] = 0
			count_objs = Behavior.objects.filter(source__slide__lecture__week = lecture.week,
					source__slide__lecture__week_order = lecture.week_order,
					user__eventing_user_id=user_id).count()

			# if e == 'seeked forward':
			# 	filtered_objs = filtered_objs.filter(seek_type='FW')
			# elif e == 'seeked backward':
			# 	filtered_objs = filtered_objs.filter(seek_type='BW')
			# elif e != 'all':
			# 	filtered_objs = filtered_objs.filter(event_type=e)
			lecture_obj['z'] = count_objs
			user_obj['data'].append(lecture_obj)
	return [user_obj]

def generate_indicators():
	indicators = ['top_seeks', 'top_seeks_fw', 'top_seeks_bw', 'top_pauses', 'rate_changer', 'highest_rate', 'lowest_rate']
	lectures = Lecture.objects.all()
	response_data = {}
	for lecture in lectures:
		lecture_name = str(lecture.week) + "-" + str(lecture.week_order)
		print lecture_name
		for indicator in indicators:
			response_data[indicator] = getattr(clickstream_handler, indicator)(lecture_name, 10, "any")
	return response_data

def generate_per_lecture_by_week(week):
	indicators = ['top_seeks', 'top_seeks_fw', 'top_seeks_bw', 'top_pauses', 'rate_changer', 'highest_rate', 'lowest_rate']
	lectures = Lecture.objects.filter(week=week)
	response_data = {}
	for lecture in lectures:
		lecture_name = str(lecture.week) + "-" + str(lecture.week_order)
		result = lecture_data(lecture_name)
		response_data[lecture_name] = result
		print '=====================' + lecture_name + "====================="
	return response_data


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

