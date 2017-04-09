import yaml
from django.test import TestCase

from src.web.serialization.models import TextStatementsGenerator, TextChecker, Task


class TaskTestCase(TestCase):
    def test_deserialize_correctly(self):
        obj = yaml.load("""
        !Task
        name: sample-task
        max_score: 100
        checker: !TextChecker
            answer: sample_answer
        statements_generator: !TextStatementsGenerator
            title: Sample task
            description: Sample description
        """)
        self.assertTrue(isinstance(obj, Task), "invalid type after deserialization")
        self.assertEqual(obj.name, "sample-task")
        self.assertEqual(obj.max_score, 100)
        self.assertTrue(isinstance(obj.checker, TextChecker), "invalid checker type after deserialization")
        self.assertEqual(obj.checker.answer, "sample_answer")
        self.assertEqual(obj.checker.case_sensitive, False)
        self.assertTrue(isinstance(obj.statements_generator, TextStatementsGenerator),
                        "invalid checker type after deserialization")
        self.assertEqual(obj.statements_generator.title, "Sample task")
        self.assertEqual(obj.statements_generator.description, "Sample description")

    def test_serialize_correctly(self):
        obj = Task("sample-task",
                   100,
                   TextChecker("sample_answer"),
                   TextStatementsGenerator("Sample task", "Sample description"))
        expected = "!Task\n" + \
                   "checker: !TextChecker\n" + \
                   "  answer: sample_answer\n" + \
                   "  case_sensitive: false\n" + \
                   "max_score: 100\n" + \
                   "name: sample-task\n" + \
                   "statements_generator: !TextStatementsGenerator\n" + \
                   "  description: Sample description\n" + \
                   "  title: Sample task\n"
        self.assertEqual(expected, yaml.dump(obj, default_flow_style=False))


class TextCheckerTestCase(TestCase):
    def test_deserialize_correctly(self):
        obj = yaml.load("""
        !TextChecker
        answer: sample_answer
        case_sensitive: true
        """)
        self.assertTrue(isinstance(obj, TextChecker), "invalid type after deserialization")
        self.assertEqual(obj.answer, "sample_answer")
        self.assertEqual(obj.case_sensitive, True)

    def test_deserialize_correctly_without_case(self):
        obj = yaml.load("""
        !TextChecker
        answer: sample_answer
        """)
        self.assertTrue(isinstance(obj, TextChecker), "invalid type after deserialization")
        self.assertEqual(obj.answer, "sample_answer")
        self.assertEqual(obj.case_sensitive, False)

    def test_serialize_correctly(self):
        obj = TextChecker("sample_answer", True)
        expected = "!TextChecker\n" + \
                   "answer: sample_answer\n" + \
                   "case_sensitive: true\n"
        self.assertEqual(expected, yaml.dump(obj, default_flow_style=False))


class TextStatementsGeneratorTestCase(TestCase):
    def test_deserialize_correctly(self):
        obj = yaml.load("""
        !TextStatementsGenerator
        title: Sample task
        description: Sample description
        """)
        self.assertTrue(isinstance(obj, TextStatementsGenerator), "invalid type after deserialization")
        self.assertEqual(obj.title, "Sample task")
        self.assertEqual(obj.description, "Sample description")

    def test_serialize_correctly(self):
        obj = TextStatementsGenerator("Sample task", "Sample description")
        expected = "!TextStatementsGenerator\n" + \
                   "description: Sample description\n" + \
                   "title: Sample task\n"
        self.assertEqual(expected, yaml.dump(obj, default_flow_style=False))
