from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url

from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [url(r'^$', RedirectView.as_view(url='/backend', permanent=False), name='index'),
               url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
               url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'), path('admin/', admin.site.urls),
               url('', include('main.frontend.urls')),
               url('backend/', include('main.backend.urls')),
               url(r'api/', include('main.api.urls'))]
