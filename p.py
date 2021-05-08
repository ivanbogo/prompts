from prompt_toolkit import CommandLineInterface, Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.layout import HSplit, Window, TokenListControl, BufferControl
from prompt_toolkit.layout.controls import UIContent, UIControl
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from prompt_toolkit.layout.dimension import LayoutDimension

import model


class MyControl(UIControl):
    def __init__(self, m: model.Model):
        self.m = m
        self.content = UIContent(
            get_line=self.get_line,
            line_count=m.line_count(),
            show_cursor=True)

    def get_line(self, i):
        return [(Token.Text, self.m.get_line(i))]

    def create_content(self, cli, width, height):
        return self.content


class Tail:
    def __init__(self, path: str):
        self.edit = False
        self.wrap = False
        self.numbers = True
        self.marks = dict()
        self.line = 0

        self.model = model.Model(path)
        self.style = style_from_dict({
            Token.CursorLine: 'reverse',
        })

        self.main = Window(
            content=MyControl(self.model),
            cursorline=True,
            wrap_lines=Condition(lambda cli: self.wrap))

        self.status = Window(
            height=LayoutDimension.exact(1),
            content=TokenListControl(
                get_tokens=self.get_status_tokens,
                align_right=False))

        self.command = Window(
            height=LayoutDimension.exact(1),
            content=BufferControl(buffer_name=DEFAULT_BUFFER))

        self.layout = HSplit([self.main, self.status, self.command])

        bindings = load_key_bindings(enable_abort_and_exit_bindings=True, enable_system_bindings=True)
        bindings.add_binding('j')(self.down)
        bindings.add_binding('k')(self.up)

        self.application = Application(
            layout=self.layout,
            style=self.style,
            use_alternate_screen=True,
            buffer=Buffer(is_multiline=False),
            key_bindings_registry=bindings)

    def get_status_tokens(self, cli):
        return [
            (Token.Status, self.get_status()),
            (Token.Text, ' : '),
            (Token.LineNumber, '%04d' % self.line)
        ]

    def get_status(self):
        return ''.join([c[1] for c in ((self.edit, 'e'), (self.wrap, 'w'), (self.numbers, 'n')) if c[0]])

    def run(self):
        eventloop = create_eventloop()
        try:
            cli = CommandLineInterface(application=self.application, eventloop=eventloop)
            cli.run()
        finally:
            eventloop.close()

    def scroll(self, count):
        self.main.vertical_scroll += count
        self.line = self.main.vertical_scroll
        self.main.content.content.cursor_position = Point(self.main.vertical_scroll, 0)

    def down(self, event):
        self.scroll(1)

    def up(self, event):
        self.scroll(-1)


if __name__ == '__main__':
    import sys
    tail = Tail(sys.argv[1])
    tail.run()
