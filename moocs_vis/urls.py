from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()

from clickstream.views import current_date, hours_ahead
from lectures.views import *

urlpatterns = patterns('',
	url(r'^$', home),
    url(r'^hello/$', home),
    url(r'^date/$', current_date),
    url(r'^upload-slides/$', upload_slides),
    url(r'^upload-clickstream/$', upload_clickstream),
    url(r'^map/$', geo_map),
    url(r'^map/json/$', geo_map_json),
    url(r'^indicators/json/$', indicators_json),
    url(r'^per-lecture/$', per_lecture),
    url(r'^lectures/$', lectures),
    url(r'^lectures/users/$', lectures_users),
    url(r'^lectures/json/$', lectures_json),
    url(r'^lectures/users/json/$', lectures_users_json),
    url(r'^per-lecture/lecture-json/$', lecture_json),
    url(r'^per-user/$', per_user),
    url(r'^per-user/lecture-json/$', lecture_json_by_user),
    url(r'^time/plus/(\d{1,2})/$', hours_ahead),
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
