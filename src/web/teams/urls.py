from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.teams_list, name='list'),
    url(r'^create/$', views.create, name='create'),
    url(r'^join/(?P<invite_hash>[^/]+)/$', views.join, name='join'),
    url(r'^(?P<team_id>\d+)/$', views.team, name='team'),
]
