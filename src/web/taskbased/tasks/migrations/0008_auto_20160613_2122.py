# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-13 16:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_attempt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attempt',
            name='is_checked',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='attempt',
            name='is_correct',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]