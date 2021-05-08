from __future__ import unicode_literals

from prompt_toolkit.filters import Condition

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.buffer import AcceptAction

from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.margins import NumberredMargin

from prompt_toolkit.layout.screen import Point, Char
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, TokenListControl, UIContent, UIControl, FillControl
from prompt_toolkit.layout.dimension import LayoutDimension as D

from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from prompt_toolkit.application import Application
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.interface import CommandLineInterface


editing = False
insert_mode = Condition(lambda cli: editing)

wrap = False
wrapping = Condition(lambda cli: wrap)


def get_line(i):
    return [(Token.LineNumber, "%04d" % i), (Token.Title, 50 * '(Hello, World) ')]


content = UIContent(
   get_line=get_line,
   show_cursor=True,
   # cursor_position=Point(150, 2),
   line_count=1000000)


class MyControl(UIControl):
    def create_content(self, cli, width, height):
        return content

    def move_cursor(self, y):
        content.cursor_position = Point(y, 0)


def get_status_tokens(cli):
    return [
        (Token.Title, ' Status '),
        (Token.Title, str(editing)),
        (Token.LineNumber, ' %s ' % (str(main.render_info and main.render_info.ui_content.cursor_position) or 'N/A'))
    ]


main = Window(content=MyControl(), cursorline=True, wrap_lines=wrapping)
status = Window(height=D.exact(1), content=TokenListControl(get_status_tokens, align_right=False))


def scroll(count):
    main.vertical_scroll += count
    main.content.move_cursor(main.vertical_scroll)


layout = HSplit([
    main,
    status,
    # Window(height=D.exact(1), content=FillControl('-', token=Token.Line)),
    Window(height=D.exact(1), content=BufferControl(buffer_name=DEFAULT_BUFFER)),
])

registry = load_key_bindings()
# registry = Registry()


@registry.add_binding(Keys.ControlC, eager=True)
@registry.add_binding('q', filter=~insert_mode)
def _(event):
    event.cli.set_return_value(None)


@registry.add_binding('w', filter=~insert_mode)
def _(event):
    global wrap
    wrap = not wrap


@registry.add_binding('j', filter=~insert_mode)
def line_down(event):
    scroll(1)


@registry.add_binding('k', filter=~insert_mode)
def line_up(event):
    scroll(-1)


@registry.add_binding('d', filter=~insert_mode)
def screen_down(event):
    scroll(50)


@registry.add_binding('u', filter=~insert_mode)
def screen_up(event):
    scroll(-50)


@registry.add_binding('x', filter=~insert_mode)
def help(event):
    if application.layout == layout:
        application.layout = Window(FillControl(char=Char('x')))
    else:
        application.layout = layout


@registry.add_binding(':')
def command(event):
    global editing
    editing = True
    buffers[DEFAULT_BUFFER].reset()
    buffers[DEFAULT_BUFFER].text = ':'
    buffers[DEFAULT_BUFFER].cursor_position = 1
    

def accept(cli, doc):
    global editing
    editing = False
    buffers[DEFAULT_BUFFER].reset()
    buffers[DEFAULT_BUFFER].text = ''


buffers = {
    DEFAULT_BUFFER: Buffer(is_multiline=False, accept_action=AcceptAction(handler=accept)),
}

style = style_from_dict({Token.LineNumber: 'bg:#ansiblue'})

application = Application(
    layout=layout,
    style=style,
    buffers=buffers,
    key_bindings_registry=registry,
    use_alternate_screen=True)


def run():
    eventloop = create_eventloop()
    try:
        cli = CommandLineInterface(application=application, eventloop=eventloop)
        cli.run()

    finally:
        eventloop.close()


if __name__ == '__main__':
    run()


