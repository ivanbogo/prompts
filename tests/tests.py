import unittest
import tempfile

import model
from p import Tail


class TestModel(unittest.TestCase):
    def test_load_and_bounds(self):
        with model.Model('../venv/bin/activate') as m:
            for i in range(m.line_count()):
                line = m.get_line(i)
                self.assertIs(type(line), str)

            try:
                m.get_line(m.line_count() + 1)
                self.fail('Should have asserted')
            except AssertionError:
                pass

    def test_contents(self):
        path = '../venv/bin/activate'
        with model.Model(path) as m, open(path) as f:
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

        tail = Tail('../venv/bin/activate')
        self.assertEqual('n', tail.get_status())
        tokens = tail.get_status_tokens(None)
        for t in tokens:
            self.assertIsInstance(t[0], type(Token))
            self.assertIsInstance(t[1], str)
