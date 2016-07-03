from django.db import models

import sortedm2m.fields

from ..tasks import models as tasks_models
import contests.models


class Category(models.Model):
    name = models.CharField(max_length=100, help_text='Public name of the category')

    description = models.TextField(help_text='Public description of the category. Supports Markdown')

    tasks = sortedm2m.fields.SortedManyToManyField(tasks_models.Task)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class ContestCategories(models.Model):
    contest = models.OneToOneField(contests.models.TaskBasedContest, related_name='categories_list')

    categories = sortedm2m.fields.SortedManyToManyField(Category)

    def __str__(self):
        return 'Categories for %s' % (self.contest, )

    class Meta:
        verbose_name_plural = 'Contests categories'
