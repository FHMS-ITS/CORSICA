from django.conf.urls import url

from main.frontend.views import about

urlpatterns = [
    url(r'^about/$', about, name='frontend.about'),
]
