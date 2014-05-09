from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from lectures.clickstream_handler import lecture_data, behaviors_by_user, behaviors_by_user_slide, top_seeks, top_pauses, top_seeks_playrate, top_pauses_playrate, top_ratechanges, handle_slides_file, handle_clickstream_file
from lectures.forms import UploadFileForm
from lectures.models import Lecture

import json

# Create your views here.
# def upload_course(request):
# 	if request.method == 'POST':
# 		form = UploadFileForm(request.POST, request.FILES)
# 		if form.is_valid():
# 			handle_course_file(request.FILES['file'])
# 			# return HttpResponse(request.FILES['file'])
# 	else:
# 		form = UploadFileForm()
# 	return render_to_response('upload_course.html', {'form': form}, context_instance=RequestContext(request))

# def upload_lecture(request):
# 	if request.method == 'POST':
# 		form = UploadFileForm(request.POST, request.FILES)
# 		if form.is_valid():
# 			handle_clickstream_file(request.FILES['file'])
# 			# return HttpResponse(request.FILES['file'])
# 	else:
# 		form = UploadFileForm()
# 	return render_to_response('upload_clickstream.html', {'form': form}, context_instance=RequestContext(request))

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
	nonclick_rate = 0
	if 'lecture_q' in request.GET:
		lecture = request.GET['lecture_q']
		tokens = lecture.split('-')
		nonclick_rates = Lecture.objects.filter(week = int(tokens[0]), week_order = int(tokens[1]))
		if len(nonclick_rates) > 0:
			nonclick_rate = nonclick_rates[0].nonclick_rate
	return render_to_response('per_lecture.html', {'nonclick_rate': nonclick_rate, 'lecture_q': lecture, 'lecture_list': lecture_list}, context_instance=RequestContext(request))

def per_user(request):
	lectures = Lecture.objects.filter(slides_imported = True).order_by("week", "week_order")
	lecture_list = []
	for lecture in lectures:
		lecture_list.append(str(lecture.week) + '-' + str(lecture.week_order))
	lecture = ''
	user = ''
	seq = ''
	indicator = ''
	if 'lecture_q' in request.GET and 'user_q' in request.GET and 'seq_q' in request.GET:
		lecture = request.GET['lecture_q']
		user = request.GET['user_q']
		seq = request.GET['seq_q']
		if 'indicator_q' in request.GET:
			indicator = request.GET['indicator_q']

	# indicators
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
	rate_changer = [
		'ee7104602f171e3982cf313958edfeb0ec6e58d1',
		'a296da3018f0d7ea1d2d19a421df2eef1157f6b8',
		'8db5c7e9e37423cee6111d5a85919b1d2c3bea44',
	]
	return render_to_response('per_user.html', {'lecture_list': lecture_list, 'lecture_q': lecture, 'user_q': user, 'seq_q': seq, 'indicator_q': indicator,
		'top_seeks': top_seeks(lecture, 10), 'top_pauses': top_pauses(lecture, 10),
		'not_much_jump': not_much_jump, 'few_clicks': few_clicks,
		'low_prop_fw_bw': low_prop_fw_bw, 'high_prop_fw_bw': high_prop_fw_bw,
		'high_fw': high_fw, 'high_bw': high_bw, 'rate_changer': top_ratechanges(lecture, 10),
		'top_pauses_playrate_125': top_pauses_playrate(lecture, 10, 1.25), 'top_pauses_playrate_150': top_pauses_playrate(lecture, 10, 1.5),
		'top_seeks_playrate_125': top_seeks_playrate(lecture, 10, 1.25), 'top_seeks_playrate_150': top_seeks_playrate(lecture, 10, 1.5)},
		# },
		context_instance=RequestContext(request))

def lecture_json(request):
	if 'lecture' in request.GET:
		lecture = request.GET['lecture']
		response_data = lecture_data(lecture)
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
