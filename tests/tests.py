import unittest
import tempfile
import logging
import six
import sys

import model
from p import Tail

TEST_FILE = six.text_type(__file__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class TestModel(unittest.TestCase):
    def test_load_and_bounds(self):
        with model.Model(TEST_FILE) as m:
            for i in range(m.line_count()):
                line = m.get_line(i)
                self.assertIsInstance(line, six.text_type)

            try:
                m.get_line(m.line_count() + 1)
                self.fail('Should have asserted')
            except AssertionError:
                pass

    def test_contents(self):
        with model.Model(TEST_FILE) as m, open(TEST_FILE) as f:
            for i, line in enumerate(ll.rstrip('\n') for ll in f.readlines()):
                read = m.get_line(i)
                self.assertEqual(line, read)

    def test_search(self):
        with tempfile.NamedTemporaryFile(mode='wt') as f:
            f.write('\n'.join(['lorem ipsum do lorem', 'the quick brown fox', 'jumps over the lazy dog']))
            f.flush()
            with model.Model(f.name) as m:
                self.assertEqual(1, m.search(0, 'brown'))
                self.assertEqual(0, m.search(0, 'lorem'))
                self.assertEqual(2, m.search(2, 'l.zy dog'))


class TestTail(unittest.TestCase):
    def test_status(self):
        from prompt_toolkit.token import Token

        tail = Tail(TEST_FILE)
        tokens = tail.get_status_tokens(None)
        tt = type(Token)
        for t in tokens:
            self.assertIsInstance(t[0], tt)
            self.assertIsInstance(t[1], six.text_type)
