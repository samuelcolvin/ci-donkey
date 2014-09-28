from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^$', 'cidonkey.views.static_ajax_page', name='build-list', kwargs={'ajax_url': 'build-list-ajax'}),
    url(r'^ajax/$', 'cidonkey.views.build_list_ajax', name='build-list-ajax'),

    url(r'^(?P<pk>\d+)/$', 'cidonkey.views.static_ajax_page', name='build-details', kwargs={'ajax_url': 'build-details-ajax'}),
    url(r'^ajax/(?P<pk>\d+)/$', 'cidonkey.views.build_details_ajax', name='build-details-ajax'),
    url(r'^go-build/$', 'cidonkey.views.go_build', name='go-build'),
    url(r'^builds/check$', 'cidonkey.views.check_builds', name='check-builds'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.jinja'}),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/accounts/login/'}, name='logout'),
    url(r'^admin/', include(admin.site.urls)),
)
