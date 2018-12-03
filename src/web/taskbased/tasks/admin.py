from django.contrib import admin

from . import models


class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement_generator', 'max_score', 'checker')

admin.site.register(models.Task, TaskAdmin)


class TextCheckerAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'answer', 'case_sensitive')
    list_display_links = ('id', 'task')
    list_editable = ('case_sensitive', )

admin.site.register(models.TextChecker, TextCheckerAdmin)


class RegExpCheckerAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'pattern', 'flag_multiline', 'flag_dotall', 'flag_verbose')
    list_display_links = ('id', 'task')
    list_editable = ('flag_multiline', 'flag_dotall', 'flag_verbose')

admin.site.register(models.RegExpChecker, RegExpCheckerAdmin)


class SimplePyCheckerAdmin(admin.ModelAdmin):
    list_display = ('id', 'task')
    list_display_links = ('id', 'task')

admin.site.register(models.SimplePyChecker, SimplePyCheckerAdmin)

class TextStatementGeneratorAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'template', 'last_change_time')

admin.site.register(models.TextStatementGenerator, TextStatementGeneratorAdmin)


class ContestTasksAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest')
    list_filter = ('contest', )

admin.site.register(models.ContestTasks, ContestTasksAdmin)


class AttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'contest', 'task', 'participant', 'is_checked', 'is_correct', 'is_plagiarized', 'plagiarized_from')
    list_editable = ('is_checked', 'is_correct', 'is_plagiarized')
    list_filter = ('contest', 'task', 'is_plagiarized', 'is_checked', 'participant')

admin.site.register(models.Attempt, AttemptAdmin)


class ByCategoriesTasksOpeningPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest', 'opens_for_all_participants')
    list_editable = ('opens_for_all_participants', )
    list_filter = ('contest', )

admin.site.register(models.ByCategoriesTasksOpeningPolicy, ByCategoriesTasksOpeningPolicyAdmin)


class WelcomeTasksOpeningPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest')

admin.site.register(models.WelcomeTasksOpeningPolicy, WelcomeTasksOpeningPolicyAdmin)


class ManualTasksOpeningPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest')

admin.site.register(models.ManualTasksOpeningPolicy, ManualTasksOpeningPolicyAdmin)


class AllTasksOpenedOpeningPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest')

admin.site.register(models.AllTasksOpenedOpeningPolicy, AllTasksOpenedOpeningPolicyAdmin)


class ManualOpenedTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'contest', 'task', 'participant')
    list_filter = ('contest', 'task')

admin.site.register(models.ManualOpenedTask, ManualOpenedTaskAdmin)
