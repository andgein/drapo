# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-13 09:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0002_auto_20160607_1306'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='description',
            field=models.TextField(default='', help_text='Full description. Supports MarkDown'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contest',
            name='short_description',
            field=models.TextField(default='', help_text='Shows on main page'),
            preserve_default=False,
        ),
    ]