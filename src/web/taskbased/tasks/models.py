import abc
import unicodedata
import re

import sortedm2m.fields
from django.db import models

import polymorphic.models

import drapo.models
import contests.models
import users.models


class TaskStatement:
    def __init__(self, title, statement, files=None):
        if files is None:
            files = []
        self.title = title
        self.statement = statement
        self.files = files


class CheckResult(abc.ABC):
    is_checked = False
    is_correct = False
    public_comment = ''
    private_comment = ''
    score = 0


class Checked(CheckResult):
    def __init__(self, is_answer_correct, public_comment='', private_comment='', score=0):
        self.is_checked = True
        self.is_correct = is_answer_correct
        self.public_comment = public_comment
        self.private_comment = private_comment
        self.score = score

class PostponeForManualCheck(CheckResult):
    pass


class AbstractStatementGenerator(polymorphic.models.PolymorphicModel, drapo.models.ModelWithTimestamps):
    def generate(self, context):
        """ Returns TaskStatement """
        raise NotImplementedError('Child should implement it\'s own generate()')

    def is_available_for_anonymous(self):
        raise NotImplementedError('Child should implement it\'s own is_available_for_anonymous()')

    @property
    def last_change_time(self):
        """ By default last change time is last model update, but you can modify this behavior for child """
        return self.updated_at

    def __str__(self):
        return str(self.get_real_instance())


class TextStatementGenerator(AbstractStatementGenerator):
    title = models.TextField(help_text='Markdown with substitutes')

    template = models.TextField(help_text='Markdown with substitutes')

    # TODO (andgein): add files

    def is_available_for_anonymous(self):
        # TODO (andgein): check for substitution patterns
        return True

    def generate(self, context):
        # TODO (andgein): make substitutions with variables from context
        return TaskStatement(self.title, self.template)

    def __str__(self):
        return self.template[:50] + '...'


class AbstractChecker(polymorphic.models.PolymorphicModel):
    def check_attempt(self, attempt, context):
        """ Returns CheckResult or bool """
        raise NotImplementedError('Child should implement it\'s own check()')

    def __str__(self):
        return str(self.get_real_instance())


class TextChecker(AbstractChecker):
    answer = models.TextField(help_text='Correct answer')

    case_sensitive = models.BooleanField(help_text='Is answer case sensitive', default=False)

    def __str__(self):
        return '== "%s"' % (self.answer, )

    @classmethod
    def _normalize_case_less(cls, text):
        return unicodedata.normalize('NFKD', text.casefold())

    @classmethod
    def _case_insensitive_string_comparison(cls, first, second):
        """
        Case insensitive comparison is hard problem.
        See http://stackoverflow.com/questions/319426/how-do-i-do-a-case-insensitive-string-comparison-in-python
        for details
        """
        return cls._normalize_case_less(first) == cls._normalize_case_less(second)

    def check_attempt(self, attempt, context):
        if self.case_sensitive:
            return self.answer == attempt.answer
        return self._case_insensitive_string_comparison(self.answer, attempt.answer)


class RegExpChecker(AbstractChecker):
    pattern = models.TextField(help_text='Regular expression for matching, don\'t need ^ and $')

    flag_ignore_case = models.BooleanField(help_text='Python\'s re.IGNORECASE (re.I)', default=False)

    flag_multiline = models.BooleanField(help_text='Python\'s re.MULTILINE (re.M)', default=False)

    flag_dotall = models.BooleanField(help_text='Python\'s re.DOTALL (re.S)', default=False)

    flag_verbose = models.BooleanField(help_text='Python\'s re.VERBOSE (re.X)', default=False)

    def __str__(self):
        return '=~ /%s/%s' % (
            self.pattern,
            'i' if self.flag_ignore_case else '' +
            'm' if self.flag_multiline else '' +
            's' if self.flag_dotall else '' +
            'x' if self.flag_verbose else ''
        )

    @property
    def compiled_regexp(self):
        flags = 0
        if self.flag_ignore_case:
            flags |= re.IGNORECASE
        if self.flag_multiline:
            flags |= re.MULTILINE
        if self.flag_dotall:
            flags |= re.DOTALL
        if self.flag_verbose:
            flags |= re.VERBOSE

        return re.compile(self.pattern, flags)

    def check_attempt(self, attempt, context):
        return self.compiled_regexp.fullmatch(attempt.answer) is not None


class Task(models.Model):
    name = models.CharField(max_length=100, help_text='Shows on tasks page')

    statement_generator = models.OneToOneField(AbstractStatementGenerator, related_name='task')

    max_score = models.PositiveIntegerField(help_text='Maximum score for this task')

    checker = models.OneToOneField(AbstractChecker, related_name='task')

    def __str__(self):
        return self.name

    def check_attempt(self, attempt, context):
        check_result = self.checker.check_attempt(attempt, context)
        if type(check_result) == bool:
            score = self.max_score if check_result else 0
            return Checked(check_result, score=score)
        if isinstance(check_result, CheckResult):
            return check_result

        return PostponeForManualCheck()


# For contests without categories
class ContestTasks(models.Model):
    contest = models.OneToOneField(contests.models.Contest, related_name='tasks_list')

    tasks = sortedm2m.fields.SortedManyToManyField(Task)

    def __str__(self):
        return 'Tasks set for %s' % (self.contest, )


class Attempt(drapo.models.ModelWithTimestamps):
    contest = models.ForeignKey(contests.models.Contest, related_name='attempts')

    task = models.ForeignKey(Task, related_name='attempts')

    participant = models.ForeignKey(contests.models.AbstractParticipant, related_name='attempts')

    author = models.ForeignKey(users.models.User, related_name='attempts')

    answer = models.TextField()

    is_checked = models.BooleanField(default=False, db_index=True)

    is_correct = models.BooleanField(default=False, db_index=True)

    score = models.IntegerField(default=0)

    public_comment = models.TextField(blank=True)

    private_comment = models.TextField(blank=True)

    def __str__(self):
        return 'Attempt by %s on %s.%s' % (self.author, self.contest, self.task)

    def try_to_check(self):
        context = {}
        check_result = self.task.check_attempt(self, context)
        if check_result.is_checked:
            self.is_checked = True
            self.is_correct = check_result.is_correct
            self.public_comment = check_result.public_comment
            self.private_comment = check_result.private_comment
            self.score = check_result.score

            self.save()
