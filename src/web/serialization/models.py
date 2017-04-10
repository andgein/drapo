import os
import yaml

import taskbased.tasks.models as models


class ContextException(Exception):
    def __init__(self, *args):
        super(ContextException, self).__init__(*args)


class AbstractContext(object):
    def get_file(self, path):
        raise NotImplementedError("Child should implement its own get_file()")


class DirectoryContext(object):
    def __init__(self, directory):
        self.directory = directory

    def open_file(self, relative_path):
        if os.path.isabs(relative_path):
            raise ContextException("Path must be relative")

        return os.path.join(self.directory, relative_path)


class Task(object):
    def __init__(self, name, max_score, checker, statement_generator):
        self.name = name
        self.max_score = max_score
        self.checker = checker
        self.statement_generator = statement_generator

    def to_model(self, ctx):
        try:
            old_model = models.Task.objects.get(name=self.name)
            # TODO
            raise models.Task.DoesNotExist()
        except models.Task.DoesNotExist:
            return models.Task.objects.create(name=self.name,
                                     max_score=self.max_score,
                                     checker=self.checker.to_model(ctx),
                                     statement_generator=self.statement_generator.to_model(ctx))


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

register_class(Task)
register_class(TextChecker)
register_class(TextStatementGenerator)