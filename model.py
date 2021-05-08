import logging
import sys
import re

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


class Model:
    def __init__(self, path):
        self.path = path
        self.fd = open(path, 'rb')

        chunk = 4096
        position = 0
        self.lines = [0]
        while True:
            read = self.fd.read(chunk)
            if not read:
                if position > self.lines[-1]:
                    self.lines.append(position + 1)
                break

            for i in range(len(read)):
                if read[i] == 10:
                    self.lines.append(position + i + 1)

            position = position + len(read)

        logging.debug("Lines: %s", ', '.join(map(str, self.lines)))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fd.close()

    def get_line(self, i):
        assert 0 <= i < self.line_count()

        self.fd.seek(self.lines[i])
        count = self.lines[i + 1] - self.lines[i] - 1
        return self.fd.read(count).decode('utf-8')

    def line_count(self):
        return len(self.lines) - 1

    def search(self, start, text):
        p = re.compile(text)
        for i in range(start, self.line_count()):
            line = self.get_line(i)
            if p.search(line):
                return i

        return -1
