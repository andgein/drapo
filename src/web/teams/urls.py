from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.teams_list, name='list'),
    url(r'^create/$', views.create, name='create'),
    url(r'^join/$', views.join, name='join'),
    url(r'^join/(?P<invite_hash>[^/]+)/$', views.join, name='join'),
    url(r'^(?P<team_id>\d+)/$', views.team, name='team'),
    url(r'^(?P<team_id>\d+)/edit/$', views.edit, name='edit'),
    url(r'^(?P<team_id>\d+)/leave/$', views.leave, name='leave'),
    url(r'^(?P<team_id>\d+)/members/(?P<user_id>\d+)/remove$', views.remove_member, name='remove_member'),
]
