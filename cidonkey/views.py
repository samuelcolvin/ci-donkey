import decimal
import json
import datetime
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
import django.utils.formats as django_format
from django.contrib.humanize.templatetags.humanize import naturaltime

from .cid import ci
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
    return {'main_menu': main_menu, 'admin_access': request.user.is_staff, 'messages': []}


class AjaxPage(TemplateView):
    template_name = "ajax_page.jinja"
    ajax_url = None

    def dispatch(self, request, *args, **kwargs):
        self.ajax_url = self.kwargs.pop('ajax_url')
        return super(AjaxPage, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AjaxPage, self).get_context_data(**kwargs)
        ajax_url = reverse(self.ajax_url, args=self.args, kwargs=self.kwargs)
        context['ajax_url'] = ajax_url
        response = resolve(ajax_url).func(self.request, *self.args, **self.kwargs)
        content = getattr(response, 'rendered_content') # , getattr(response, 'body', None)
        context['initial_content'] = content
        return context

static_ajax_page = login_required(AjaxPage.as_view())


class BuildList(ListView):
    """
    List of previous builds
    """
    model = BuildInfo
    template_name = 'build_list.jinja'
    link_column = 'start'
    columns = ('start', 'time_taken', 'trigger', 'author', 'complete', 'successful')

    def dispatch(self, request, *args, **kwargs):
        check_all_builds()
        return super(BuildList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BuildList, self).get_context_data(**kwargs)
        context['columns'] = self.columns
        context['link_column'] = self.link_column
        context['headings'] = self._headings()
        context['get_value'] = self.get_value
        return context

    def _headings(self):
        meta = self.model._meta
        for attr_name in self.columns:
            try:
                field = meta.get_field_by_name(attr_name)[0]
                yield field.verbose_name
            except FieldDoesNotExist:
                if hasattr(self.model, attr_name) and hasattr(getattr(self.model, attr_name), 'short_description'):
                    yield getattr(self.model, attr_name).short_description
                else:
                    yield attr_name

    def get_value(self, obj, attr_name):
        value = getattr(obj, attr_name)
        if hasattr(value, '__call__'):
            value = value()
        if isinstance(value, datetime.datetime):
            value = naturaltime(value)
        return value


build_list_ajax = login_required(BuildList.as_view())

class BuildDetails(DetailView):
    """
    details of a build.
    """
    model = BuildInfo
    template_name = 'build.jinja'

    def get_context_data(self, **kwargs):
        self.object = ci.check(self.object)
        return super(BuildDetails, self).get_context_data(**kwargs)

build_details_ajax = login_required(BuildDetails.as_view())


@login_required
@require_POST
def go_build(request):
    project = get_project()
    if project:
        build_info = BuildInfo.objects.create(trigger='manual', author=request.user.username, project=project)
        ci.build(build_info)
    else:
        messages.warning(request, 'No project created')
    return redirect(reverse('build-list'))


class UniversalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return '%0.2f' % obj
        if isinstance(obj, datetime.datetime):
            return django_format.date_format(obj, 'DATETIME_FORMAT')
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            return '%s: %r' % (obj.__class__.__name__, obj)


def check_build(build_info):
    bi = ci.check(build_info)
    extract = ['sha', 'complete', 'test_success', 'test_passed', 'start', 'finished', 'pre_log', 'main_log']
    return {at: getattr(bi, at) for at in extract}


def check_all_builds():
    return [check_build(bi) for bi in BuildInfo.objects.filter(complete=False)]


@login_required
def check_builds(request):
    builds = check_all_builds()
    response = {'check_count': len(builds), 'builds': builds}
    return HttpResponse(json.dumps(response, indent=2, cls=UniversalEncoder), content_type='application/json')


def get_project():
    """
    gets the first project, stop gap until we support more than one project
    """
    return Project.objects.first()
