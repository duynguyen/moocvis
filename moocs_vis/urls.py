from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()

from clickstream.views import current_date, hours_ahead
from lectures.views import home, upload_slides, upload_clickstream, per_lecture, lecture_json, per_user, lecture_json_by_user

# urlpatterns = patterns('',
#     # Examples:
#     # url(r'^$', 'moocs_vis.views.home', name='home'),
#     # url(r'^blog/', include('blog.urls')),

#     url(r'^admin/', include(admin.site.urls)),
# )

urlpatterns = patterns('',
	url(r'^$', home),
    url(r'^hello/$', home),
    url(r'^date/$', current_date),
    url(r'^upload-slides/$', upload_slides),
    url(r'^upload-clickstream/$', upload_clickstream),
    url(r'^per-lecture/$', per_lecture),
    url(r'^per-lecture/lecture-json/$', lecture_json),
    url(r'^per-user/$', per_user),
    url(r'^per-user/lecture-json/$', lecture_json_by_user),
    url(r'^time/plus/(\d{1,2})/$', hours_ahead),
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
