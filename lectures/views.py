from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from lectures import clickstream_handler
from lectures.clickstream_handler import *
from lectures.forms import UploadFileForm
from lectures.models import Lecture

import json

events_mapping = {'all': 'All users', 'top_seeks': 'Users making the most seeks',
			'top_seeks_fw': 'Users making the most forward seeks',
			'top_seeks_bw': 'Users making the most forward seeks',
			'top_pauses': 'Users making the most pauses',
			'rate_changer': 'Users changing playback rate the most',
			'highest_rate': 'Users playing at highest average rate',
			'lowest_rate': 'Users playing at lowest average rate'}

def home(request):
	return render_to_response('home.html', context_instance=RequestContext(request))

def upload_slides(request):
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			handle_slides_file(request.FILES['file'])
			return render_to_response('upload_slides.html', {'form': form, 'message': 'File uploaded successfully!'}, context_instance=RequestContext(request))
	else:
		form = UploadFileForm()
	return render_to_response('upload_slides.html', {'form': form}, context_instance=RequestContext(request))

def upload_clickstream(request):
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			handle_clickstream_file(request.FILES['file'])
			return render_to_response('upload_clickstream.html', {'form': form, 'message': 'File uploaded successfully!'}, context_instance=RequestContext(request))
	else:
		form = UploadFileForm()
	return render_to_response('upload_clickstream.html', {'form': form}, context_instance=RequestContext(request))

def per_lecture(request):
	lectures = Lecture.objects.filter(slides_imported = True).order_by("week", "week_order")
	lecture_list = []
	for lecture in lectures:
		lecture_list.append(str(lecture.week) + '-' + str(lecture.week_order))
	lecture = ''
	userclass = ''
	achievement = ''
	nonclick_rate = 0
	userclass_list = ['active', 'viewers', 'inactive']
	achievement_list = ['distinction', 'normal', 'none']
	userclass = request.GET.get('userclass_q', '')
	achievement = request.GET.get('achievement_q', '')
	lecture = request.GET.get('lecture_q', '')
	if lecture:
		tokens = lecture.split('-')
		nonclick_rates = Lecture.objects.filter(week = int(tokens[0]), week_order = int(tokens[1]))
		if len(nonclick_rates) > 0:
			nonclick_rate = nonclick_rates[0].nonclick_rate
	return render_to_response('per_lecture.html', {
		'nonclick_rate': nonclick_rate,
		'lecture_q': lecture,
		'lecture_list': lecture_list,
		'userclass': userclass,
		'userclass_list': userclass_list,
		'achievement': achievement,
		'achievement_list': achievement_list,
		}, context_instance=RequestContext(request))

def lectures(request):
	lectures = Lecture.objects.filter(slides_imported = True).order_by("week", "week_order")
	return render_to_response('lectures.html', {
		'lectures': lectures,
		}, context_instance=RequestContext(request))

def lectures_users(request):
	lectures = Lecture.objects.filter(slides_imported = True).order_by("week", "week_order")
	return render_to_response('lectures_by_user.html', {
		'lectures': lectures,
		# 'events': ['all', 'top_seeks', 'top_seeks_fw', 'top_seeks_bw', 'top_pauses', 'rate_changer'],
		'events_mapping': events_mapping,
		'rates': ['any', '0.5', '0.75', '1.0', '1.25', '1.5', '1.75', '2.0'],
		}, context_instance=RequestContext(request))

def per_user(request):
	lectures = Lecture.objects.filter(slides_imported = True).order_by("week", "week_order")
	lecture_list = []
	for lecture in lectures:
		lecture_list.append(str(lecture.week) + '-' + str(lecture.week_order))
	lecture = request.GET.get('lecture_q', '')
	user = request.GET.get('user_q')
	seq = request.GET.get('seq_q')
	indicator = request.GET.get('indicator_q')
	playrate = request.GET.get('playrate_q')

	return render_to_response('per_user.html', {
			'lecture_list': lecture_list,
			'lecture_q': lecture,
			'user_q': user, 'seq_q': seq,
			'indicator_q': indicator,
			'rates': ['any', '0.5', '0.75', '1.0', '1.25', '1.5', '1.75', '2.0'],
			'playrate_q': playrate,
		},
		context_instance=RequestContext(request))

def indicators_json(request):
	lecture = request.GET.get('lecture', '')
	if not lecture:
		return HttpResponse("No lecture chosen!", content_type="application/json")

	not_much_jump = [
		'2cb1b1ce76e8055cf4fa10d7c4f4223ccb1a3e6c',
		'0734a1493fc249a3c82688db10b562ea9b7d4025',
		'32cc688b1d9906a935be183354b27b09e0dd384e',
	]
	few_clicks = [
		'6eaacbc91b6f0258268b2cb7f69d20420ecadf20',
		'81b0bcf376892aaf75ef0b2539aa2f6acfc99d39',
		'2c864e640b049c3d40f9166900089a6a133a4558',
	]
	low_prop_fw_bw = [
		'4f27c335bdcced586cb7c54ca9b81e15ca3f6ea7',
		'7608a241fb3f0a10d4d823a614a9dded39080f0c',
		'cb4eb61624cfc63a1b0c9588c21afda472962b24',
		'11dfc7c2a604c285c528e6fd6650272eef79932b',
		'e44cae143c150f4598a7bec9b9a7f402525f4f4b',
		'1943560029298bddc07a5563897fa6de4995fbfd',
		'42bea50b26a7e03bfef1dea6261a9b4739b6f5fa',
	]
	high_prop_fw_bw = [
		'de61c304f468c17ebd71c277cc32390bae243794',
		'9574876900d0b4c76f5ea71c903a8a2feddeb852',
		'23a97b5239a39ec36743433b6dbd6c493fae94cb',
	]
	high_fw = [
		'adadd5575a88ccef23fafc194d0def28c4181328',
		'2f7359c43398e9669f95181d8835629ecf76daa1',
		'f4e2c0b6c7089154365273f4f6240a128a693d1a',
	]
	high_bw = [
		'31fc299fb2671692e9a334e7d4ee804013e238dd',
		'9412d6093b3534d5e61f81d13ff0bc85ba5d4ee9',
		'72ef39cdc7803863c919ead70be79bd908a2a841',
	]
	rates = ['any', '0.5', '0.75', '1.0', '1.25', '1.5', '1.75', '2.0']
	indicators = ['top_seeks', 'top_seeks_fw', 'top_seeks_bw', 'top_pauses', 'rate_changer']
	response_data = {}
	response_data['indicators'] = indicators
	for indicator in indicators:
		for rate in rates:
			response_data[indicator + '-' + rate] = getattr(clickstream_handler, indicator)(lecture, 10, rate)

	# response_data = {
	# 	'top_seeks': top_seeks(lecture, 10), 'top_pauses': top_pauses(lecture, 10),
	# 	'not_much_jump': not_much_jump, 'few_clicks': few_clicks,
	# 	'low_prop_fw_bw': low_prop_fw_bw, 'high_prop_fw_bw': high_prop_fw_bw,
	# 	'high_fw': high_fw, 'high_bw': high_bw, 'rate_changer': top_ratechanges(lecture, 10),
	# 	'top_pauses_playrate_125': top_pauses_playrate(lecture, 10, 1.25), 'top_pauses_playrate_150': top_pauses_playrate(lecture, 10, 1.5),
	# 	'top_seeks_playrate_125': top_seeks_playrate(lecture, 10, 1.25), 'top_seeks_playrate_150': top_seeks_playrate(lecture, 10, 1.5),
	# }

	return HttpResponse(json.dumps(response_data), content_type="application/json")

def lecture_json(request):
	lecture = request.GET.get('lecture', '')
	response_data = lecture_data(lecture)
	if response_data:
		return HttpResponse(json.dumps(response_data), content_type="application/json")
	return HttpResponse("Some error occurs!", content_type="application/json")

def lectures_json(request):
	userclass = request.GET.get('userclass', '')
	achievement = request.GET.get('achievement', '')
	option = request.GET.get('option', '')
	course_id = request.GET.get('course_id', '')
	response_data = get_weekly_stats(int(course_id))
	if response_data:
		return HttpResponse(json.dumps(response_data), content_type="application/json")
	return HttpResponse("Some error occurs!", content_type="application/json")

def lectures_users_json(request):
	course_id = request.GET.get('course_id', '')
	response_data = get_weekly_stats_users(int(course_id))
	if response_data:
		return HttpResponse(json.dumps(response_data), content_type="application/json")
	return HttpResponse("Some error occurs!", content_type="application/json")

def lectures_user_json(request):
	course_id = request.GET.get('course_id', '')
	user_id = request.GET.get('user_id', '')
	response_data = get_stats_user(int(course_id), user_id)
	if response_data:
		return HttpResponse(json.dumps(response_data), content_type="application/json")
	return HttpResponse("Some error occurs!", content_type="application/json")

def lecture_json_by_user(request):
	if 'lecture' in request.GET and 'user' in request.GET and 'seq' in request.GET:
		lecture = request.GET['lecture']
		user = request.GET['user']
		if request.GET['seq'] == 'slide_seq':
			return HttpResponse(json.dumps(behaviors_by_user_slide(user, lecture)), content_type="application/json")
		elif request.GET['seq'] == 'time_seq':
			return HttpResponse(json.dumps(behaviors_by_user(user, lecture)), content_type="application/json")
	return HttpResponse("Some error occurs!", content_type="application/json")

def geo_map(request):
	lectures = Lecture.objects.filter(slides_imported = True).order_by("week", "week_order")
	lecture_list = []
	for lecture in lectures:
		lecture_list.append(str(lecture.week) + '-' + str(lecture.week_order))
	return render_to_response('map.html', { 'lectures' : lecture_list }, context_instance=RequestContext(request))

def geo_map_json(request):
	return HttpResponse(json.dumps(map_json()), content_type="application/json")
