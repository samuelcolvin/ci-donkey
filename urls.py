from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^$', 'cidonkey.views.build_list', name='build-list'),
    url(r'^builds/do$', 'cidonkey.views.build', name='do-build'),
    url(r'^builds/check$', 'cidonkey.views.check_all', name='check-builds'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.jinja'}),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/accounts/login/'}, name='logout'),
    url(r'^admin/', include(admin.site.urls)),
)
