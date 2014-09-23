from django.core.urlresolvers import reverse
from django.db.models import FieldDoesNotExist
from django.views.generic.list import ListView
from django.contrib.auth.decorators import login_required

from .models import Build


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


class BuildList(ListView):
    model = Build
    template_name = 'build_list.jinja'
    link_column = 'start'
    columns = ('start', 'time_taken', 'trigger', 'author', 'on_master')

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
        return value


build_list = login_required(BuildList.as_view())
