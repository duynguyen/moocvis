from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
import datetime
# from moocs_vis.clickstream.models import User

def home(request):
    return HttpResponse('Hello Clickstream users!')

def current_date(request):
	now = datetime.datetime.now()
	return render(request, 'current_date.html', {'current_date': now, 'current_section': 'present'})

def hours_ahead(request, offset):
	try:
		offset = int(offset)
	except ValueError:
		raise Http404()
	dt = datetime.datetime.now() + datetime.timedelta(hours=offset)
	return render(request, 'hours_ahead.html', {'next_time': dt, 'hour_offset': offset, 'current_section': 'future'})

def user_list(request):
	users = User.objects.order_by('name')
	return render(request, 'user_list.html', {'users': users})

