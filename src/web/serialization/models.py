import yaml


class Task(object):
    def __init__(self, name, max_score, checker, statements_generator):
        self.name = name
        self.max_score = max_score
        self.checker = checker
        self.statements_generator = statements_generator


class TextChecker(object):
    def __init__(self, answer, case_sensitive=False):
        self.answer = answer
        self.case_sensitive = case_sensitive


class TextStatementsGenerator(object):
    def __init__(self, title, description):
        self.title = title
        self.description = description


def register_class(cls):
    yaml_tag = "!%s" % cls.__name__
    yaml.add_constructor(yaml_tag,
                         lambda loader, node: cls(**loader.construct_mapping(node)))
    yaml.add_representer(cls,
                         lambda dumper, data: dumper.represent_yaml_object(yaml_tag, data, cls, flow_style=False))


register_class(Task)
register_class(TextChecker)
register_class(TextStatementsGenerator)
