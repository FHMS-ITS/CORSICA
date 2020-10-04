from django.conf.urls import url, include
from main.backend.views.main import main
from main.backend.views.crawler import crawler
from main.backend.views.firmware import firmware
from main.backend.views.remote_tester import remote_tester
from main.backend.views.shodan import shodan
from main.backend.views.tree import tree, modal_leaf_info
from main.backend.views.fingerprinter import fingerprinter
from main.backend.views.version_fingerprints import version_fingerprints

urlpatterns = [
    url(r'^$', main, name='backend.home'),
    url(r'^$', main, name='home'),
    url(r'^crawler/$', crawler, name='backend.crawler'),
    url(r'^firmware/$', firmware, name='backend.firmware'),
    url(r'^version/$', version_fingerprints, name='backend.version_fingerprints'),
    url(r'^rtester/$', remote_tester, name='backend.remote_tester'),
    url(r'^shodan/$', shodan, name='backend.shodan'),
    url(r'^tree/(?P<group_id>\w*)', tree, name='backend.tree_id'),
    url(r'^tree$', tree, name='backend.tree'),
    url(r'^fingerprinter$', fingerprinter, name='backend.fingerprinter'),
    url(r'^modal/leaf_info/$', modal_leaf_info, name='backend.modal_leaf_info'),

]
