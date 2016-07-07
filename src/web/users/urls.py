from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<user_id>\d+)/$', views.profile, name='profile'),
    url(r'^login/$', views.login, name='login'),
    url(r'^confirm/(?P<token>\w+)/$', views.confirm, name='confirm'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^register/$', views.register, name='register'),
    url(r'^edit/$', views.edit, name='edit'),
    url(r'^change_password/$', views.change_password, name='change_password'),
]
