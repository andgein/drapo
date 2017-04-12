import os
import yaml

import taskbased.tasks.models as models

from glob import glob


class ContextException(Exception):
    def __init__(self, *args):
        super(ContextException, self).__init__(*args)


class AbstractContext(object):
    def get_file(self, path):
        raise NotImplementedError("Child should implement its own get_file()")

    def glob(self, glob):
        raise NotImplementedError("Child should implement its own get_file()")


class DirectoryContext(object):
    def __init__(self, directory):
        self.directory = directory

    def open_file(self, relative_path):
        if os.path.isabs(relative_path):
            raise ContextException("Path must be relative")

        return os.path.join(self.directory, relative_path)

    def glob(self, relative_glob):
        if os.path.isabs(relative_glob):
            raise ContextException("Path must be relative")

        absolute_glob = os.path.join(self.directory, relative_glob)
        return glob(absolute_glob)


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
            # TODO
            raise models.Task.DoesNotExist()
        except models.Task.DoesNotExist:
            task = models.Task.objects.create(name=self.name,
                                              max_score=self.max_score,
                                              checker=self.checker.to_model(ctx),
                                              statement_generator=self.statement_generator.to_model(ctx))
            for file in self.files:
                for file_name in ctx.glob(file.path):
                    with open(file_name, 'rb') as fd:
                        bytes = fd.read()
                    base_name = os.path.basename(file_name)
                    task_file = models.TaskFile.create_file_for_participant(task, None, bytes, base_name)
                    task_file.is_private = file.is_private
                    task_file.save()
            return task


class TextChecker(object):
    def __init__(self, answer, case_sensitive=False):
        self.answer = answer
        self.case_sensitive = case_sensitive

    def to_model(self, ctx):
        return models.TextChecker.objects.create(answer=self.answer, case_sensitive=self.case_sensitive)


class TextStatementGenerator(object):
    def __init__(self, title, template):
        self.title = title
        self.template = template

    def to_model(self, ctx):
        return models.TextStatementGenerator.objects.create(title=self.title, template=self.template)


def register_class(cls):
    yaml_tag = "!%s" % cls.__name__
    yaml.add_constructor(yaml_tag,
                         lambda loader, node: cls(**loader.construct_mapping(node)))
    yaml.add_representer(cls,
                         lambda dumper, data: dumper.represent_yaml_object(yaml_tag, data, cls, flow_style=False))


register_class(DirectoryContext)

register_class(File)

register_class(Task)
register_class(TextChecker)
register_class(TextStatementGenerator)