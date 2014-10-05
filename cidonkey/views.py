import datetime
import uuid
import pytz
import os
import time
from django.contrib.sites.shortcuts import get_current_site
from django.core.servers.basehttp import FileWrapper
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse, resolve
from django.db.models import FieldDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.views.generic import DetailView
from django.views.generic.list import ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import naturaltime

from . import cid
from .models import BuildInfo, Project


def cid_context(request):
    """
    Main context processor, adds main menu.
    """
    main_menu = []
    if request.user.is_authenticated():
        if request.user.is_staff:
            main_menu = []
        else:
            main_menu = []
        # TODO: add github url here
    return {'request': request,
            'main_menu': main_menu,
            'admin_access': request.user.is_staff,
            'messages': []}


class PageWithAjax(TemplateView):
    template_name = "ajax_page.jinja"
    ajax_url = None

    def dispatch(self, request, *args, **kwargs):
        self.ajax_url = self.kwargs.pop('ajax_url')
        return super(PageWithAjax, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PageWithAjax, self).get_context_data(**kwargs)
        ajax_url = reverse(self.ajax_url, args=self.args, kwargs=self.kwargs)
        context['ajax_url'] = ajax_url
        response = resolve(ajax_url).func(self.request, *self.args, **self.kwargs)
        content = getattr(response, 'rendered_content')
        context['initial_content'] = content
        return context

page_with_ajax = login_required(PageWithAjax.as_view())


class BuildMixin(object):
    status = 200
    model = None
    link_column = None
    columns = []
    live_times = []

    def render_to_response(self, context, **response_kwargs):
        return super(BuildMixin, self).render_to_response(context, status=self.status, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(BuildMixin, self).get_context_data(**kwargs)
        context['columns'] = self.columns
        context['link_column'] = self.link_column
        context['headings'] = self._headings()
        context['get_value'] = self._get_value
        context['get_verbose_name'] = self._get_verbose_name
        context['live_times'] = self.live_times
        return context

    def _headings(self):
        for attr_name in self.columns:
            yield self._get_verbose_name(attr_name)

    def _get_verbose_name(self, attr_name):
        meta = self.model._meta
        try:
            field = meta.get_field_by_name(attr_name)[0]
            return field.verbose_name
        except FieldDoesNotExist:
            if hasattr(self.model, attr_name) and hasattr(getattr(self.model, attr_name), 'short_description'):
                return getattr(self.model, attr_name).short_description
            else:
                return attr_name

    def _get_value(self, obj, attr_name):
        value = getattr(obj, attr_name)
        if hasattr(value, '__call__'):
            value = value()

        if attr_name in self.live_times and isinstance(value, datetime.datetime):
            return '<span class="live-time" data-start="%s"></span>' % value.isoformat(), True

        if isinstance(value, datetime.datetime):
            value = naturaltime(value)
        return value, False


class BuildList(BuildMixin, ListView):
    """
    List of previous builds
    """
    model = BuildInfo
    template_name = 'build_list.jinja'
    link_column = 'start'
    columns = ('start', 'time_taken', 'trigger', 'label', 'author', 'show_coverage', 'successful')
    paginate_by = 50
    live_times = ['time_taken']

    def dispatch(self, request, *args, **kwargs):
        if not any_active_builds(self.request):
            self.status = 201
        return super(BuildList, self).dispatch(request, *args, **kwargs)


build_list_ajax = login_required(BuildList.as_view())


class BuildDetails(BuildMixin, DetailView):
    """
    details of a build.
    """
    model = BuildInfo
    template_name = 'build.jinja'
    columns = ('start',
               'modified',
               'time_taken',
               'trigger',
               'action',
               'label',
               'on_master',
               'fetch_branch',
               'commit_url',
               'author',
               'complete',
               'test_success',
               'test_passed',
               'container',)

    def get_context_data(self, **kwargs):
        self.object = check(self.request, self.object)
        if self.object.complete:
            self.status = 202
        if self.object.process_log:
            self.object.process_log = self.object.process_log.replace(self.object.project.github_token,
                                                                      '<github token>')
        return super(BuildDetails, self).get_context_data(**kwargs)

build_details_ajax = login_required(BuildDetails.as_view())


@csrf_exempt
@require_POST
def webhook(request, pk):
    project = get_project(pk)
    if not project:
        return HttpResponse('no project created', status=403)
    time.sleep(0.5)
    build_info = BuildInfo.objects.create(project=project)
    response_code, info = cid.process_github_webhook(request, build_info)
    if response_code == 202:
        cid.build(info, get_site(request))
        msg = 'building started, id = %d' % info.id
    else:
        build_info.delete()
        msg = str(info)
    return HttpResponse(msg, status=response_code)


def status_svg(request, pk):
    project = get_project(pk)
    svg = project.status_svg if project else 'null.svg'
    svg_path = os.path.join(os.path.dirname(__file__), 'static', svg)
    response = HttpResponse(FileWrapper(open(svg_path)), content_type='image/svg+xml')
    response['Etag'] = '"%s"' % uuid.uuid4()
    response['Cache-Control'] = 'no-cache'
    response['Expires'] = datetime.datetime.now().replace(tzinfo=pytz.UTC).strftime('%a, %d %b %Y %H:%M:%S %Z')
    return response


@login_required
@require_POST
def go_build(request):
    project = get_project()
    if project:
        build_info = BuildInfo.objects.create(trigger='manual',
                                              author=request.user.username,
                                              project=project,
                                              on_master=True)
        cid.build(build_info, get_site(request))
    else:
        messages.warning(request, 'No project created')
    return redirect(reverse('build-list'))


def check(request, build_info):
    bi = build_info
    try:
        bi = cid.check(build_info, get_site(request))
    except cid.KnownError, e:
        messages.error(request, str(e))
        bi = build_info
    finally:
        return bi


def check_build(request, build_info):
    extract = ['sha', 'complete', 'test_success', 'test_passed', 'start', 'finished', 'process_log', 'ci_log']
    bi = check(request, build_info)
    return {at: getattr(bi, at) for at in extract}


def any_active_builds(r):
    return any([not check_build(r, bi)['complete'] for bi in BuildInfo.objects.filter(complete=False)])


def get_site(request):
    current_site = get_current_site(request)
    return 'http://' + current_site.domain + '/'


def get_project(pk=None):
    """
    gets the first project, stop gap until we support more than one project
    """
    projects = Project.objects.all()
    if pk is not None:
        projects = projects.filter(pk=pk)
    return projects.first()
