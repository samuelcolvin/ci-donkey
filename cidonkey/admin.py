from django.contrib import admin
from .models import Project, Build


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'github_url', 'ci_script')


admin.site.register(Project, ProjectAdmin)


class BuildAdmin(admin.ModelAdmin):
    list_display = ('sha', 'start', 'complete', 'test_success', 'test_passed')


admin.site.register(Build, BuildAdmin)

