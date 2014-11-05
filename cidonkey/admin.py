from django.contrib import admin
from .models import Project, BuildInfo


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('github_repo', 'github_user', 'ci_script')


admin.site.register(Project, ProjectAdmin)


class BuildInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'sha', 'container', 'start', 'queued', 'complete', 'test_success', 'test_passed')


admin.site.register(BuildInfo, BuildInfoAdmin)

