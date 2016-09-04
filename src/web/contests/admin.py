from django.contrib import admin

from . import models


class ContestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_visible_in_list', 'start_time', 'finish_time')
    list_display_links = ('id', )
    list_editable = ('is_visible_in_list', )
    search_fields = ('name', )


admin.site.register(models.TaskBasedContest, ContestAdmin)


class IndividualParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest', 'user')
    list_editable = ('contest', )
    list_filter = ('contest', )

admin.site.register(models.IndividualParticipant, IndividualParticipantAdmin)


class TeamParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest', 'team')
    list_editable = ('contest', )
    list_filter = ('contest',)

admin.site.register(models.TeamParticipant, TeamParticipantAdmin)


class ScoreByPlaceAdditionalScorerAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest', 'place', 'points')
    list_editable = ('place', 'points')
    list_filter = ('contest', )

admin.site.register(models.ScoreByPlaceAdditionalScorer, ScoreByPlaceAdditionalScorerAdmin)


class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_published', 'publish_time')
    list_editable = ('title', 'is_published')
    list_filter = ('is_published', )

admin.site.register(models.News, NewsAdmin)
