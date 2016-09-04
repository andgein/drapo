from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.contests_list, name='list'),
    url(r'^list/$', views.contests_list),
    url(r'^create/$', views.create, name='create'),

    url(r'^(?P<contest_id>\d+)/$', views.contest, name='contest'),
    url(r'^(?P<contest_id>\d+)/join/$', views.join, name='join'),
    url(r'^(?P<contest_id>\d+)/edit/$', views.edit, name='edit'),

    url(r'^(?P<contest_id>\d+)/tasks/$', views.tasks, name='tasks'),
    url(r'^(?P<contest_id>\d+)/tasks/(?P<task_id>\d+)/$', views.task, name='task'),
    url(r'^(?P<contest_id>\d+)/tasks/(?P<task_id>\d+)/delete/$', views.delete_task, name='delete_task'),
    url(r'^(?P<contest_id>\d+)/tasks/(?P<task_id>\d+)/opened/$', views.task_opens, name='task_opens'),
    url(r'^(?P<contest_id>\d+)/tasks/(?P<task_id>\d+)/open/(?P<participant_id>\d+)/$', views.open_task, name='open_task'),
    url(r'^(?P<contest_id>\d+)/tasks/add/$', views.add_task, name='add_task'),
    url(r'^(?P<contest_id>\d+)/files/(?P<file_id>\d+)/$', views.task_file, name='task_file'),

    url(r'^(?P<contest_id>\d+)/categories/add/$', views.add_category, name='add_category'),
    url(r'^(?P<contest_id>\d+)/categories/(?P<category_id>\d+)/add/$', views.add_task_to_category, name='add_task_to_category'),
    url(r'^(?P<contest_id>\d+)/categories/(?P<category_id>\d+)/edit/$', views.edit_category, name='edit_category'),
    url(r'^(?P<contest_id>\d+)/categories/(?P<category_id>\d+)/delete/$', views.delete_category, name='delete_category'),
    url(r'^(?P<contest_id>\d+)/scoreboard/$', views.scoreboard, name='scoreboard'),
    url(r'^(?P<contest_id>\d+)/attempts/$', views.attempts, name='attempts'),
    url(r'^(?P<contest_id>\d+)/attempts/(?P<attempt_id>\d+)/$', views.attempt, name='attempt'),

    url(r'^(?P<contest_id>\d+)/news/add/$', views.add_news, name='add_news'),
    url(r'^(?P<contest_id>\d+)/news/(?P<news_id>\d+)/$', views.news, name='news'),
    url(r'^(?P<contest_id>\d+)/news/(?P<news_id>\d+)/edit/$', views.edit_news, name='edit_news'),

    url(r'^(?P<contest_id>\d+)/participants/$', views.participants, name='participants'),
    url(r'^(?P<contest_id>\d+)/participants/add/$', views.add_participant, name='add_participant'),
    url(r'^(?P<contest_id>\d+)/participants/(?P<participant_id>\d+)/change/$',
        views.change_participant_status,
        name='change_participant_status'),
]
