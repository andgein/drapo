# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-18 08:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0006_auto_20160718_1313'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('tasks', '0012_taskfile_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractTasksOpeningPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name_plural': 'Task opening policies',
                'verbose_name': 'Task opening policy',
            },
        ),
        migrations.CreateModel(
            name='ManualChecker',
            fields=[
                ('abstractchecker_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tasks.AbstractChecker')),
            ],
            options={
                'abstract': False,
            },
            bases=('tasks.abstractchecker',),
        ),
        migrations.CreateModel(
            name='ManualOpenedTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contests.TaskBasedContest')),
                ('participant', models.ForeignKey(default=None, help_text='Setting Null opens task for everyone', null=True, on_delete=django.db.models.deletion.CASCADE, to='contests.AbstractParticipant')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='manual_opens', to='tasks.Task')),
            ],
        ),
        migrations.CreateModel(
            name='ByCategoriesTasksOpeningPolicy',
            fields=[
                ('abstracttasksopeningpolicy_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tasks.AbstractTasksOpeningPolicy')),
                ('opens_for_all_participants', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Task opening policies: by categories',
                'verbose_name': 'Task opening policy: by categories',
            },
            bases=('tasks.abstracttasksopeningpolicy',),
        ),
        migrations.CreateModel(
            name='ManualTasksOpeningPolicy',
            fields=[
                ('abstracttasksopeningpolicy_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tasks.AbstractTasksOpeningPolicy')),
            ],
            options={
                'abstract': False,
            },
            bases=('tasks.abstracttasksopeningpolicy',),
        ),
        migrations.AddField(
            model_name='abstracttasksopeningpolicy',
            name='contest',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks_opening_policies', to='contests.TaskBasedContest'),
        ),
        migrations.AddField(
            model_name='abstracttasksopeningpolicy',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_tasks.abstracttasksopeningpolicy_set+', to='contenttypes.ContentType'),
        ),
    ]
