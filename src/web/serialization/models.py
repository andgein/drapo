import os
import yaml
from glob import glob
from tempfile import TemporaryDirectory

import taskbased.tasks.models as task_models
import contests.models as contest_models
import taskbased.categories.models as categories_models
from serialization.utils import load_yaml_from_file

from git import Repo


class ContextException(Exception):
    def __init__(self, *args):
        super(ContextException, self).__init__(*args)


class AbstractContext:
    def get_file(self, path):
        raise NotImplementedError("Child should implement its own get_file()")

    def glob(self, glob):
        raise NotImplementedError("Child should implement its own get_file()")

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class DirectoryContext(AbstractContext):
    def __init__(self, directory):
        self.directory = directory

    def get_file(self, relative_path):
        if os.path.isabs(relative_path):
            raise ContextException("Path must be relative")

        return os.path.join(self.directory, relative_path)

    def glob(self, relative_glob):
        if os.path.isabs(relative_glob):
            raise ContextException("Path must be relative")

        absolute_glob = os.path.join(self.directory, relative_glob)
        return glob(absolute_glob)


class SubdirectoryContext(AbstractContext):
    def __init__(self, directory, ctx):
        self.directory = directory
        self.ctx = ctx

    def get_file(self, relative_path):
        if os.path.isabs(relative_path):
            raise ContextException("Path must be relative")

        return self.ctx.get_file(os.path.join(self.directory, relative_path))

    def glob(self, relative_glob):
        if os.path.isabs(relative_glob):
            raise ContextException("Path must be relative")

        nested_glob = os.path.join(self.directory, relative_glob)
        return self.ctx.glob(nested_glob)


class GitContext(AbstractContext):
    def __init__(self, url, branch='master'):
        self.tempdir = TemporaryDirectory()
        self.url = url
        self.branch = branch
        self.downloaded = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tempdir.cleanup()

    def get_file(self, relative_path):
        if not self.downloaded:
            self.download()

        if os.path.isabs(relative_path):
            raise ContextException("Path must be relative")

        return os.path.join(self.tempdir.name, relative_path)

    def glob(self, relative_glob):
        if not self.downloaded:
            self.download()

        if os.path.isabs(relative_glob):
            raise ContextException("Path must be relative")

        return glob(os.path.join(self.tempdir.name, relative_glob))

    def download(self):
        Repo.clone_from(self.url, self.tempdir.name, branch=self.branch)
        self.downloaded = True


class File:
    def __init__(self, path, is_private=False):
        self.path = path
        self.is_private = is_private


class Task:
    def __init__(self, name, max_score, checker, statement_generator, files=None):
        self.files = [] if files is None else files
        self.name = name
        self.max_score = max_score
        self.checker = checker
        self.statement_generator = statement_generator

    def to_model(self, ctx):
        checker = self.checker.to_model(ctx)
        statement_generator = self.statement_generator.to_model(ctx)

        task, created = task_models.Task.objects.get_or_create(
            name=self.name,
            defaults={
                'max_score': self.max_score,
                'checker': checker,
                'statement_generator': statement_generator,
            },
        )

        if not created:
            task.max_score = self.max_score
            old_checker = task.checker
            old_statement_generator = task.statement_generator
            task.checker = checker
            task.statement_generator = statement_generator
            task.save()
            old_checker.delete()
            old_statement_generator.delete()

        # TODO: Files are leaking
        for file in self.files:
            file_names = ctx.glob(file.path)
            if len(file_names) == 0:
                raise RuntimeError("File path '%s' does not specify any files" % file.path)
            for file_name in file_names:
                with open(file_name, 'rb') as fd:
                    file_bytes = fd.read()
                base_name = os.path.basename(file_name)
                task_file = task_models.TaskFile.create_file_for_participant(task, None, file_bytes, base_name)
                task_file.is_private = file.is_private
                task_file.save()

        return task


class TextChecker:
    def __init__(self, answer, case_sensitive=False):
        self.answer = answer
        self.case_sensitive = case_sensitive

    def to_model(self, ctx):
        return task_models.TextChecker.objects.create(answer=self.answer, case_sensitive=self.case_sensitive)


class SimplePyChecker:
    def __init__(self, source_path=None, source=None):
        self.source_path = source_path
        self.source = source

    def to_model(self, ctx):
        if self.source_path is not None:
            with open(ctx.get_file(self.source_path), 'rt', encoding='utf-8') as f:
                self.source = f.read()

        return task_models.SimplePyChecker.objects.create(source=self.source)


class TextStatementGenerator:
    def __init__(self, title, template):
        self.title = title
        self.template = template

    def to_model(self, ctx):
        return task_models.TextStatementGenerator.objects.create(title=self.title, template=self.template)


class SimplePyStatementGenerator:
    def __init__(self, source_path=None, source=None):
        self.source_path = source_path
        self.source = source

    def to_model(self, ctx):
        if self.source_path is not None:
            with open(ctx.get_file(self.source_path), 'rt', encoding='utf-8') as f:
                self.source = f.read()

        return task_models.SimplePyStatementGenerator.objects.create(source=self.source)


class TaskSet:
    def __init__(self, context=None, task_paths=None, categories=None):
        self.context = context
        self.task_paths = task_paths
        self.categories = categories

        if (task_paths is None) == (categories is None):
            raise Exception("Exactly one of task_paths or categories should be defined")

    def import_task(self, task_path):
        spec = load_yaml_from_file(self.context.get_file(task_path))
        ctx = SubdirectoryContext(os.path.dirname(task_path), self.context)
        return spec.to_model(ctx)

    def import_tasks(self, task_paths):
        return [self.import_task(p) for p in task_paths]

    def import_category(self, category):
        return {
            'name': category['name'],
            'description' : category.get('description', ''),
            'tasks': self.import_tasks(category['task_paths']),
        }

    def import_categories(self, categories):
        return [self.import_category(c) for c in categories]

    def to_model(self, ctx):
        if self.context is None:
            self.context = ctx

        with self.context:
            if self.task_paths:
                return self.import_tasks(self.task_paths)
            else:
                return self.import_categories(self.categories)


class TaskBasedContest:
    def __init__(self,
                 name,
                 is_visible_in_list,
                 registration_type,
                 participation_mode,
                 start_time,
                 finish_time,
                 short_description,
                 description,
                 tasks_grouping,
                 task_opening_policy,
                 task_set,
                 regions=None,
                 registration_start_time=None,
                 registration_finish_time=None):
        self.name = name
        self.is_visible_in_list = is_visible_in_list
        self.registration_type = registration_type
        self.participation_mode = participation_mode
        self.start_time = start_time
        self.finish_time = finish_time
        self.short_description = short_description
        self.description = description
        self.tasks_grouping = tasks_grouping
        self.task_opening_policy = task_opening_policy
        self.task_set = task_set
        self.regions = regions or []
        self.registration_start_time = registration_start_time
        self.registration_finish_time = registration_finish_time

    def to_model(self, ctx):
        contest, _ = contest_models.TaskBasedContest.objects.update_or_create(
            name=self.name,
            defaults={
                'is_visible_in_list': self.is_visible_in_list,
                'registration_type': self.registration_type,
                'participation_mode': self.participation_mode,
                'start_time': self.start_time,
                'finish_time': self.finish_time,
                'registration_start_time': self.registration_start_time,
                'registration_finish_time': self.registration_finish_time,
                'short_description': self.short_description,
                'description': self.description,
                'tasks_grouping': self.tasks_grouping,
            },
        )

        if self.task_opening_policy == "All":
            task_models.AllTasksOpenedOpeningPolicy.objects.get_or_create(contest=contest)
        elif self.task_opening_policy == "Manual":
            task_models.ManualTasksOpeningPolicy.objects.get_or_create(contest=contest)
        elif self.task_opening_policy == "Welcome":
            task_models.WelcomeTasksOpeningPolicy.objects.get_or_create(contest=contest)
        else:
            raise RuntimeError("Unknown task opening policy: %s" % self.task_opening_policy)

        for region in self.regions:
            contest_models.ContestRegion.objects.update_or_create(
                contest=contest,
                name=region['name'],
                defaults={
                    'start_time' : region['start_time'],
                    'finish_time' : region['finish_time'],
                    'timezone' : region.get('timezone', 'UTC'),
                },
            )

        if contest.tasks_grouping == contest_models.TasksGroping.OneByOne:
            contest_tasks, _ = task_models.ContestTasks.objects.get_or_create(contest=contest)
            for task in self.task_set.to_model(ctx):
                contest_tasks.tasks.add(task)
            contest_tasks.save()
        else:
            contest_categories, _ = categories_models.ContestCategories.objects.get_or_create(contest=contest)
            old_categories = {c.name : c for c in contest_categories.categories.all()}
            contest_categories.categories.clear()
            for category in self.task_set.to_model(ctx):
                db_category = old_categories.pop(category['name'], None)
                if db_category is None:
                    db_category = categories_models.Category(name=category['name'])
                db_category.description = category.get('description', '')
                db_category.save()

                db_category.tasks.set(category['tasks'])
                contest_categories.categories.add(db_category)

            for old_category in old_categories.values():
                old_category.delete()

        return contest


def register_class(cls):
    yaml_tag = "!%s" % cls.__name__
    yaml.add_constructor(yaml_tag,
                         lambda loader, node: cls(**loader.construct_mapping(node, deep=True)))
    yaml.add_representer(cls,
                         lambda dumper, data: dumper.represent_yaml_object(yaml_tag, data, cls, flow_style=False))


register_class(GitContext)
register_class(DirectoryContext)

register_class(File)

register_class(Task)
register_class(TextChecker)
register_class(SimplePyChecker)
register_class(TextStatementGenerator)
register_class(SimplePyStatementGenerator)

register_class(TaskSet)
register_class(TaskBasedContest)
