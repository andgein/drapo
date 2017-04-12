import os
import tempfile
import yaml
from django.test import TestCase

import taskbased.tasks.models as models

from src.web.serialization.models import *


class TaskTestCase(TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

        with open(os.path.join(self.tempdir.name, 'file1.txt'), 'wb') as f:
            f.write(b'1')
        with open(os.path.join(self.tempdir.name, 'image001.png'), 'wb') as f:
            f.write(b'2')
        with open(os.path.join(self.tempdir.name, 'image002.png'), 'wb') as f:
            f.write(b'3')

        self.task = Task("sample-task",
                         100,
                         TextChecker("sample_answer"),
                         TextStatementGenerator("Sample task", "Sample template"),
                         [File("file1.txt"), File("image*.png", True)])

    def tearDown(self):
        self.tempdir.cleanup()

    def test_deserialize_correctly(self):
        obj = yaml.load("""
        !Task
        name: sample-task
        max_score: 100
        checker: !TextChecker
            answer: sample_answer
        statement_generator: !TextStatementGenerator
            title: Sample task
            template: Sample template
        files:
        - !File
          path: file1.txt
        - !File
          is_private: True
          path: image*.png
        """)
        self.assertTrue(isinstance(obj, Task), "invalid type after deserialization")
        self.assertEqual(obj.name, "sample-task")
        self.assertEqual(obj.max_score, 100)
        self.assertTrue(isinstance(obj.checker, TextChecker), "invalid checker type after deserialization")
        self.assertEqual(obj.checker.answer, "sample_answer")
        self.assertEqual(obj.checker.case_sensitive, False)
        self.assertTrue(isinstance(obj.statement_generator, TextStatementGenerator),
                        "invalid checker type after deserialization")
        self.assertEqual(obj.statement_generator.title, "Sample task")
        self.assertEqual(obj.statement_generator.template, "Sample template")
        self.assertEqual(len(obj.files), 2)

    def test_serialize_correctly(self):
        expected = "!Task\n" + \
                   "checker: !TextChecker\n" + \
                   "  answer: sample_answer\n" + \
                   "  case_sensitive: false\n" + \
                   "files:\n" + \
                   "- !File\n" + \
                   "  is_private: false\n" + \
                   "  path: file1.txt\n" + \
                   "- !File\n" + \
                   "  is_private: true\n" + \
                   "  path: image*.png\n" + \
                   "max_score: 100\n" + \
                   "name: sample-task\n" + \
                   "statement_generator: !TextStatementGenerator\n" + \
                   "  template: Sample template\n" + \
                   "  title: Sample task\n"
        self.assertEqual(expected, yaml.dump(self.task, default_flow_style=False))

    def test_to_model(self):
        returned = self.task.to_model(DirectoryContext(self.tempdir.name))
        from_db = models.Task.objects.get(name="sample-task")
        self.assertIsNotNone(from_db)
        self.assertEqual(returned, from_db)
        self.assertEqual(from_db.name, "sample-task")
        self.assertEqual(from_db.max_score, 100)
        self.assertEqual(len(from_db.files.all()), 3)


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

    def test_to_model(self):
        obj = TextChecker("dsadsa")
        returned = obj.to_model(None)
        from_db = models.TextChecker.objects.get(answer="dsadsa")
        self.assertIsNotNone(from_db)
        self.assertEqual(returned, from_db)
        self.assertEqual(from_db.answer, "dsadsa")
        self.assertEqual(from_db.case_sensitive, False)


class TextStatementGeneratorTestCase(TestCase):
    def test_deserialize_correctly(self):
        obj = yaml.load("""
        !TextStatementGenerator
        title: Sample task
        template: Sample template
        """)
        self.assertTrue(isinstance(obj, TextStatementGenerator), "invalid type after deserialization")
        self.assertEqual(obj.title, "Sample task")
        self.assertEqual(obj.template, "Sample template")

    def test_serialize_correctly(self):
        obj = TextStatementGenerator("Sample task", "Sample template")
        expected = "!TextStatementGenerator\n" + \
                   "template: Sample template\n" + \
                   "title: Sample task\n"
        self.assertEqual(expected, yaml.dump(obj, default_flow_style=False))

    def test_to_model(self):
        obj = TextStatementGenerator("asdasd", "Sample template")
        returned = obj.to_model(None)
        from_db = models.TextStatementGenerator.objects.get(title="asdasd")
        self.assertIsNotNone(from_db)
        self.assertEqual(returned, from_db)
        self.assertEqual(from_db.title, "asdasd")
        self.assertEqual(from_db.template, "Sample template")
