from django.conf.urls import url
from main.api import views as api_views

urlpatterns = [
    url(r'^$', api_views.main, name='api.main'),
    url(r'^jobs/(?P<job_id>\d*)', api_views.jobs, name='api.jobs'),
    url(r'^firmwares/(?P<fw_id>\d*)', api_views.firmwares, name='api.firmware'),
    url(r'^shodan/query/(?P<query_id>\d*)', api_views.shodan_query, name='api.shodan_query'),
    url(r'^tests/(?P<test_id>\d*)', api_views.tests, name='api.tests'),
    url(r'^leaf_info/$', api_views.lead_info, name='api.lead_info'),
    url(r'^log_view/$', api_views.log_view, name='api.log_view'),
    url(r'^session/$', api_views.session, name='api.session'),
    url(r'^cpu_mem_info_view/$', api_views.cpu_mem_info_view, name='api.cpu_mem_info_view'),
    url(r'^fingerprinter/elements/(?P<elem_id>\d*)', api_views.fingerprinter_view, name='api.fingerprinter'),
    url(r'^fingerprinter/values/$', api_views.get_javascript_values, name='api.get_javascript_values'),
    url(r'^versions/$', api_views.version_fingerprints, name='api.version_fingerprints'),

]
