import os
import yaml
from glob import glob
from tempfile import TemporaryDirectory

import taskbased.tasks.models as task_models
import contests.models as contest_models
from serialization.utils import load_yaml_from_file

from git import Repo


class ContextException(Exception):
    def __init__(self, *args):
        super(ContextException, self).__init__(*args)


class AbstractContext(object):
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


class File(object):
    def __init__(self, path, is_private=False):
        self.path = path
        self.is_private = is_private


class Task(object):
    def __init__(self, name, max_score, checker, statement_generator, files=None):
        self.files = [] if files is None else files
        self.name = name
        self.max_score = max_score
        self.checker = checker
        self.statement_generator = statement_generator

    def to_model(self, ctx):
        try:
            task_models.Task.objects.get(name=self.name).delete()
        except task_models.Task.DoesNotExist:
            pass

        task = task_models.Task.objects.create(name=self.name,
                                               max_score=self.max_score,
                                               checker=self.checker.to_model(ctx),
                                               statement_generator=self.statement_generator.to_model(ctx))
        for file in self.files:
            file_names = ctx.glob(file.path)
            if len(file_names) == 0:
                raise RuntimeError("File path '%s' does not specify any files" % file.path)
            for file_name in file_names:
                with open(file_name, 'rb') as fd:
                    bytes = fd.read()
                base_name = os.path.basename(file_name)
                task_file = task_models.TaskFile.create_file_for_participant(task, None, bytes, base_name)
                task_file.is_private = file.is_private
                task_file.save()
        return task


class TextChecker(object):
    def __init__(self, answer, case_sensitive=False):
        self.answer = answer
        self.case_sensitive = case_sensitive

    def to_model(self, ctx):
        return task_models.TextChecker.objects.create(answer=self.answer, case_sensitive=self.case_sensitive)


class TextStatementGenerator(object):
    def __init__(self, title, template):
        self.title = title
        self.template = template

    def to_model(self, ctx):
        return task_models.TextStatementGenerator.objects.create(title=self.title, template=self.template)


class TaskSet(object):
    def __init__(self, context, task_paths):
        self.context = context
        self.task_paths = task_paths

    def to_model(self, ctx):
        tasks = []
        with self.context:
            for task_path in self.task_paths:
                spec = load_yaml_from_file(self.context.get_file(task_path))
                tasks.append(spec.to_model(self.context))
        return tasks


class TaskBasedContest(object):
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
        self.registration_start_time = registration_start_time
        self.registration_finish_time = registration_finish_time

    def to_model(self, ctx):
        try:
            contest_models.TaskBasedContest.objects.get(name=self.name).delete()
        except contest_models.TaskBasedContest.DoesNotExist:
            pass

        tasks = self.task_set.to_model(ctx)
        contest = contest_models.TaskBasedContest(
            name=self.name,
            is_visible_in_list=self.is_visible_in_list,
            registration_type=self.registration_type,
            participation_mode=self.participation_mode,
            start_time=self.start_time,
            finish_time=self.finish_time,
            registration_start_time=self.registration_start_time,
            registration_finish_time=self.registration_finish_time,
            short_description=self.short_description,
            description=self.description,
            tasks_grouping=self.tasks_grouping,
        )
        contest.save()

        contest_tasks = task_models.ContestTasks(
            contest=contest,
        )
        contest_tasks.save()

        if self.task_opening_policy == "All":
            task_models.AllTasksOpenedOpeningPolicy(contest=contest).save()
        elif self.task_opening_policy == "Manual":
            task_models.ManualTasksOpeningPolicy(contest=contest).save()
        else:
            raise RuntimeError("Unknown task opening policy: %s" % self.task_opening_policy)

        for task in tasks:
            contest_tasks.tasks.add(task)
        contest_tasks.save()

        return contest


def register_class(cls):
    yaml_tag = "!%s" % cls.__name__
    yaml.add_constructor(yaml_tag,
                         lambda loader, node: cls(**loader.construct_mapping(node)))
    yaml.add_representer(cls,
                         lambda dumper, data: dumper.represent_yaml_object(yaml_tag, data, cls, flow_style=False))


register_class(GitContext)
register_class(DirectoryContext)

register_class(File)

register_class(Task)
register_class(TextChecker)
register_class(TextStatementGenerator)

register_class(TaskSet)
register_class(TaskBasedContest)
