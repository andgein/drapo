import abc
import traceback
import unicodedata
import re
import os.path
import logging

from django.db import models
import django.db.migrations.writer
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import sortedm2m.fields
import polymorphic.models
from django.db.models.query_utils import Q
from relativefilepathfield.fields import RelativeFilePathField

import drapo.models
import contests.models
import users.models
from drapo.uploads import save_bytes


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
    is_plagiarized = False
    plagiarized_from = None
    public_comment = ''
    private_comment = ''
    score = 0


class Checked(CheckResult):
    def __init__(self, is_answer_correct, public_comment='', private_comment='', score=0):
        self.is_checked = True
        self.is_correct = is_answer_correct
        self.is_plagiarized = False
        self.plagiarized_from = None
        self.public_comment = public_comment
        self.private_comment = private_comment
        self.score = score


class CheckedPlagiarist(CheckResult):
    def __init__(self, is_answer_correct, plagiarized_from=None, public_comment='', private_comment='', score=0):
        self.is_checked = True
        self.is_correct = is_answer_correct
        self.is_plagiarized = True
        self.public_comment = public_comment
        self.private_comment = private_comment
        self.score = score

        if isinstance(plagiarized_from, contests.models.AbstractParticipant):
            self.plagiarized_from = plagiarized_from
        elif isinstance(plagiarized_from, int):
            try:
                self.plagiarized_from = contests.models.AbstractParticipant.objects.get(id=plagiarized_from)
            except contests.models.AbstractParticipant.DoesNotExist:
                self.plagiarized_from = None
        else:
            self.plagiarized_from = None


    @staticmethod
    def get_potential_plagiarists(participant):
        return contests.models.AbstractParticipant.objects.filter(
            Q(contest=participant.contest) & ~Q(id=participant.id))


class CheckError(CheckResult):
    def __init__(self, private_comment=''):
        self.is_checked = False
        self.is_correct = False
        self.is_plagiarized = False
        self.plagiarized_from = None
        self.public_comment = ''
        self.private_comment = private_comment
        self.score = 0


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
    title = models.TextField(help_text=_('Markdown with substitutes'))

    template = models.TextField(help_text=_('Markdown with substitutes'))

    def is_available_for_anonymous(self):
        # TODO (andgein): check for substitution patterns
        return True

    def generate(self, context):
        # TODO (andgein): make substitutions with variables from context
        return TaskStatement(self.title, self.template)

    def __str__(self):
        return self.template[:50] + '...'


class SimplePyStatementGenerator(AbstractStatementGenerator):
    source = models.TextField(help_text='Python source code. Must contain function generate(context)')

    def get_generator(self):
        module_globals = {
            'TaskFile': TaskFile,
            'TaskStatement': TaskStatement,
        }
        exec(self.source, module_globals)
        return module_globals['generate']

    def generate(self, context):
        generator = self.get_generator()
        return generator(context)

    def is_available_for_anonymous(self):
        return False

    def __str__(self):
        return self.source[:50] + '...'


class AbstractChecker(polymorphic.models.PolymorphicModel):
    def check_attempt(self, attempt, context):
        """ Returns CheckResult or bool """
        raise NotImplementedError('Child should implement it\'s own check()')

    def __str__(self):
        return str(self.get_real_instance())


class TextChecker(AbstractChecker):
    answer = models.TextField(help_text=_('Correct answer'))

    case_sensitive = models.BooleanField(help_text=_('Is answer case sensitive'), default=False)

    def __str__(self):
        return '== "%s"' % (self.answer,)

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


class SimplePyChecker(AbstractChecker):
    source = models.TextField(help_text='Python source code. Must contain function check(attempt, context)')

    def __str__(self):
        return '=~ %s' % repr(self.source)

    def get_checker(self):
        module_globals = {
            'Checked': Checked,
            'CheckedPlagiarist': CheckedPlagiarist,
        }
        exec(self.source, module_globals)
        return module_globals['check']

    def check_attempt(self, attempt, context):
        try:
            checker = self.get_checker()
            return checker(attempt, context)
        except Exception as e:
            logging.getLogger(__name__).exception(e)
            return CheckError(traceback.format_exc())


class ManualChecker(AbstractChecker):
    def check_attempt(self, attempt, context):
        return PostponeForManualCheck()


class Task(models.Model):
    name = models.CharField(max_length=100, help_text='Shows on tasks page', unique=True)

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


class TaskFile(models.Model):
    task = models.ForeignKey(Task, related_name='files')

    participant = models.ForeignKey(
        contests.models.AbstractParticipant,
        help_text='None if this file is for all participants',
        related_name='+',
        null=True,
        default=None
    )

    name = models.CharField(
        max_length=1000,
        help_text='File name. Visible to participants',
    )

    path = RelativeFilePathField(
        path=django.db.migrations.writer.SettingsReference(
            settings.DRAPO_TASKS_FILES_DIR,
            'DRAPO_TASKS_FILES_DIR'
        ),
        recursive=True,
        max_length=1000
    )

    content_type = models.CharField(max_length=1000, default='application/octet-stream')

    is_private = models.BooleanField(default=False)

    class Meta:
        unique_together = (('task', 'participant', 'name'),)

    @staticmethod
    def get_private_files(task):
        return list(task.files.filter(Q(is_private=True)))

    @staticmethod
    def copy_file_for_participant(task_file, participant, name):
        TaskFile.objects.get_or_create(
            task=task_file.task,
            participant=participant,
            name=name,
            path=task_file.path,
            content_type=task_file.content_type,
            is_private=False
        )

    @staticmethod
    def create_file_for_participant(task, participant, file_bytes, name, content_type=None):
        task_file, created = TaskFile.objects.get_or_create(task=task, participant=participant, name=name)

        if created:
            task_file_dir = TaskFile.generate_directory_name(task, participant)
            task_file_name = save_bytes(file_bytes, task_file_dir)
            task_file.path = task_file_name
        else:
            with open(task_file.path, 'wb') as fd:
                fd.write(file_bytes)

        if content_type is not None:
            task_file.content_type = content_type
        task_file.save()

        return task_file

    @staticmethod
    def generate_directory_name(task, participant):
        return os.path.join(
            settings.DRAPO_TASKS_FILES_DIR,
            str(task.id),
            str(participant.id) if participant is not None else '_'
        )


# For contests without categories
class ContestTasks(models.Model):
    contest = models.OneToOneField(contests.models.Contest, related_name='tasks_list')

    tasks = sortedm2m.fields.SortedManyToManyField(Task)

    def __str__(self):
        return 'Tasks set for %s' % (self.contest,)


class Attempt(drapo.models.ModelWithTimestamps):
    contest = models.ForeignKey(contests.models.Contest, related_name='attempts')

    task = models.ForeignKey(Task, related_name='attempts')

    participant = models.ForeignKey(contests.models.AbstractParticipant, related_name='attempts')

    author = models.ForeignKey(users.models.User, related_name='attempts')

    answer = models.TextField()

    is_checked = models.BooleanField(default=False, db_index=True)

    is_correct = models.BooleanField(default=False, db_index=True)

    is_plagiarized = models.BooleanField(default=False, db_index=True)

    plagiarized_from = models.ForeignKey(
        contests.models.AbstractParticipant,
        related_name='+',
        default=None,
        null=True
    )

    score = models.IntegerField(default=0)

    public_comment = models.TextField(blank=True)

    private_comment = models.TextField(blank=True)

    def __str__(self):
        return 'Attempt by %s on %s.%s' % (self.author, self.contest, self.task)

    def try_to_check(self):
        context = {}
        check_result = self.task.check_attempt(self, context)

        self.is_checked = check_result.is_checked
        self.is_correct = check_result.is_correct
        self.is_plagiarized = check_result.is_plagiarized
        self.plagiarized_from = check_result.plagiarized_from
        self.public_comment = check_result.public_comment
        self.private_comment = check_result.private_comment
        self.score = check_result.score

        self.save()


class AbstractTasksOpeningPolicy(polymorphic.models.PolymorphicModel):
    """ Defined tasks opening policies, only for task-based CTFs """
    contest = models.ForeignKey(contests.models.TaskBasedContest, related_name='tasks_opening_policies')

    class Meta:
        verbose_name = 'Task opening policy'
        verbose_name_plural = 'Task opening policies'

    def get_open_tasks(self, participant):
        raise NotImplementedError()


class WelcomeTasksOpeningPolicy(AbstractTasksOpeningPolicy):

    class Meta:
        verbose_name = 'Task opening policy: welcome'
        verbose_name_plural = 'Task opening policies: welcome'

    def get_open_tasks(self, participant):
        correct_attempts = self.contest.attempts.filter(participant=participant, is_correct=True)

        if correct_attempts.count() > 0:
            return AllTasksOpenedOpeningPolicy.get_open_tasks(self, participant)

        if self.contest.tasks_grouping == contests.models.TasksGroping.ByCategories:
            if self.contest.categories:
                category = self.contest.categories[0]
                return category.tasks.values_list('id', flat=True)
            else:
                return []
        elif self.contest.tasks_grouping == contests.models.TasksGroping.OneByOne:
            task = self.contest.tasks.first()
            return [task.id] if task else []
        else:
            raise ValueError('Invalid tasks grouping')


class ByCategoriesTasksOpeningPolicy(AbstractTasksOpeningPolicy):
    opens_for_all_participants = models.BooleanField(default=True)

    def __str__(self):
        return ('Tasks are opening inside category for %s in %s' %
                ('all' if self.opens_for_all_participants else 'participant who solved previous task',
                 self.contest)
                )

    class Meta:
        verbose_name = 'Task opening policy: by categories'
        verbose_name_plural = 'Task opening policies: by categories'

    def get_open_tasks(self, participant):
        if self.opens_for_all_participants:
            done_tasks = set(self.contest.attempts
                                         .filter(is_correct=True)
                                         .values_list('task_id', flat=True))
        else:
            done_tasks = set(self.contest.attempts
                                         .filter(participant=participant, is_correct=True)
                                         .values_list('task_id', flat=True))

        opened_tasks = []
        if self.contest.tasks_grouping == contests.models.TasksGroping.ByCategories:
            for category in self.contest.categories:
                prev_task = None
                for task in category.tasks.all():
                    if prev_task is None or prev_task.id in done_tasks:
                        opened_tasks.append(task.id)
                    prev_task = task
        elif self.contest.tasks_grouping == contests.models.TasksGroping.OneByOne:
            prev_task = None
            for task in self.contest.tasks:
                if prev_task is None or prev_task.id in done_tasks:
                    opened_tasks.append(task.id)
                prev_task = task
        else:
            raise ValueError('Invalid tasks grouping')

        return opened_tasks


class AllTasksOpenedOpeningPolicy(AbstractTasksOpeningPolicy):
    class Meta:
        verbose_name = 'Task opening policy: all'
        verbose_name_plural = 'Task opening policies: all'

    def get_open_tasks(self, participant):
        if self.contest.tasks_grouping == contests.models.TasksGroping.ByCategories:
            tasks_ids = []
            for category in self.contest.categories:
                tasks_ids.extend(category.tasks.values_list('id', flat=True))
            return tasks_ids
        elif self.contest.tasks_grouping == contests.models.TasksGroping.OneByOne:
            return [task.id for task in self.contest.tasks]
        else:
            raise ValueError('Invalid tasks grouping')


class ManualTasksOpeningPolicy(AbstractTasksOpeningPolicy):
    class Meta:
        verbose_name = 'Task opening policy: manual'
        verbose_name_plural = 'Task opening policies: manual'

    def get_open_tasks(self, participant):
        return ManualOpenedTask.objects.filter(
            contest=self.contest
        ).filter(
            Q(participant__isnull=True) | Q(participant=participant)
        ).values_list('task_id', flat=True)


class ManualOpenedTask(models.Model):
    contest = models.ForeignKey(contests.models.TaskBasedContest, related_name='+')

    task = models.ForeignKey(Task, related_name='manual_opens')

    participant = models.ForeignKey(
        contests.models.AbstractParticipant,
        null=True,
        default=None,
        help_text='Set NULL to open task for everyone'
    )
