from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface, Application
from prompt_toolkit.layout import HSplit, Window, TokenListControl, BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.controls import UIContent, UIControl
from prompt_toolkit.layout.screen import Point

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.buffer import Buffer

from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.keys import Keys

from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

import model


class MyControl(UIControl):
    def __init__(self, m):
        self.m = m
        self.content = UIContent(
            get_line=self.get_line,
            line_count=m.line_count(),
            show_cursor=True)

    def get_line(self, i):
        if self.m.numbers:
            return [(Token.LineNumber, '%6d ' % i), (Token.Text, self.m.get_line(i))]
        else:
            return [(Token.Text, self.m.get_line(i))]

    def create_content(self, cli, width, height):
        return self.content


class Tail:
    def __init__(self, path):
        self.edit = False
        self.lock = False

        self.model = model.Model(path)
        self.style = style_from_dict({
            Token.CursorLine: 'reverse',
        })

        self.wrapping = Condition(lambda cli: self.model.wrap)
        self.editing = Condition(lambda cli: self.edit)
        self.locked = Condition(lambda clie: self.lock)

        self.main = Window(
            content=MyControl(self.model),
            cursorline=~self.locked,
            wrap_lines=self.wrapping)

        self.status = Window(
            height=LayoutDimension.exact(1),
            content=TokenListControl(
                get_tokens=self.get_status_tokens,
                align_right=False))

        self.command = Window(
            height=LayoutDimension.exact(1),
            content=BufferControl(buffer_name=DEFAULT_BUFFER),
            allow_scroll_beyond_bottom=True)

        self.layout = HSplit([self.main, self.status, self.command])

        bindings = self.load_bindings()

        self.application = Application(
            layout=self.layout,
            style=self.style,
            use_alternate_screen=True,
            buffer=Buffer(is_multiline=False, read_only=Condition(lambda: not self.edit)),
            key_bindings_registry=bindings)

    def get_status_tokens(self, cli):
        status = ''.join([c[1] for c in (
            (self.edit, 'e'), (self.model.wrap, 'w'), (self.model.numbers, 'n')) if c[0]])

        return [
            (Token.Status, '[%4s]' % status),
            (Token.Text, ' '),
            (Token.Text, self.model.path),
            (Token.Text, ': '),
            (Token.LineNumber, '%d,%d/%d' % (self.model.line, self.main.vertical_scroll, self.model.line_count()))
        ]

    def run(self):
        eventloop = create_eventloop()
        try:
            cli = CommandLineInterface(application=self.application, eventloop=eventloop)
            cli.run()
        finally:
            eventloop.close()

    def scroll(self, count, half):
        info = self.main.render_info
        if not info:
            return

        if half is not None:
            count *= info.window_height
            if half:
                count = count // 2

        self.main.vertical_scroll = max(0, min(self.model.line_count() - 1, self.main.vertical_scroll + count))
        if self.model.line < self.main.vertical_scroll or \
                self.model.line > self.main.vertical_scroll + info.window_height:

            y = self.model.line = self.main.vertical_scroll
            self.main.content.content.cursor_position = Point(y, 0)

    def move_cursor(self, count):
        y = self.model.line = max(0, min(self.model.line_count() - 1, self.model.line + count))
        self.main.content.content.cursor_position = Point(y, 0)

        if not self.main.render_info:
            return

        w = self.main
        info = w.render_info

        if y > w.vertical_scroll + info.window_height or y < w.vertical_scroll:
            w.vertical_scroll = max(0, y - info.window_height // 2)

    def load_bindings(self):
        bindings = load_key_bindings(enable_abort_and_exit_bindings=True, enable_system_bindings=True)

        @bindings.add_binding('j', filter=~self.editing)
        def down(event):
            if self.lock:
                self.scroll(1, None)
            else:
                self.move_cursor(1)

        @bindings.add_binding('k', filter=~self.editing)
        def up(event):
            if self.lock:
                self.scroll(-1, None)
            else:
                self.move_cursor(-1)

        @bindings.add_binding('g', filter=~self.editing)
        def c_d(event): self.scroll(-self.model.line_count(), None)

        @bindings.add_binding('G', filter=~self.editing)
        def c_d(event): self.scroll(self.model.line_count(), None)

        @bindings.add_binding('d', filter=~self.editing)
        def c_d(event): self.scroll(1, True)

        @bindings.add_binding('f', filter=~self.editing)
        def c_d(event): self.scroll(1, False)

        @bindings.add_binding('u', filter=~self.editing)
        def c_u(event): self.scroll(-1, True)

        @bindings.add_binding('b', filter=~self.editing)
        def c_u(event): self.scroll(-1, False)

        @bindings.add_binding('w', filter=~self.editing)
        def toggle_wrap(event): self.model.wrap = not self.model.wrap

        @bindings.add_binding('n', filter=~self.editing)
        def toggle_numbers(event): self.model.numbers = not self.model.numbers

        @bindings.add_binding('q', filter=~self.editing)
        def end_loop(event): event.cli.set_return_value(None)

        @bindings.add_binding('/', filter=~self.editing)
        def start_edit(event): self.edit = True

        @bindings.add_binding(Keys.ControlC)
        def end_edit(event): self.edit = False

        @bindings.add_binding('l', filter=~self.editing)
        def _(event): self.lock = not self.lock

        return bindings


if __name__ == '__main__':
    import sys
    tail = Tail(sys.argv[1])
    tail.run()
