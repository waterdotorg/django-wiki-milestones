from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('milestones.views',
    url(r'^batch/$', 'milestones_batch', name='milestones_batch'),
    url(r'^calendar/$', 'milestones_calendar', name='milestones_calendar'),
    url(r'^calendar/json/$', 'milestones_calendar_json', name='milestones_calendar_json'),
)
