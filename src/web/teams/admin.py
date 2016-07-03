from django.contrib import admin

from . import models


class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'captain')
    list_display_links = ('id', )
    list_editable = ('name', )

admin.site.register(models.Team, TeamAdmin)
