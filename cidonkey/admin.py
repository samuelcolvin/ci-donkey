from django.contrib import admin
from .models import Project, BuildInfo


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'github_url', 'ci_script')


admin.site.register(Project, ProjectAdmin)


class BuildInfoAdmin(admin.ModelAdmin):
    list_display = ('project', 'sha', 'container', 'start', 'complete', 'test_success', 'test_passed')


admin.site.register(BuildInfo, BuildInfoAdmin)

