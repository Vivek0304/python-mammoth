from __future__ import unicode_literals

import re


class _WriterOutput(object):
    def __init__(self, start, end, anchor_position=None):
        self.start = start
        self.end = end
        self.anchor_position = anchor_position


class _MarkdownState(object):
    def __init__(self):
        self.list_state = _MarkdownListState()


class _MarkdownListState(object):
    def __init__(self):
        self.count = 0


def _symmetric_wrapped(end):
    return _Wrapped(end, end)


class _Wrapped(object):
    def __init__(self, start, end):
        self._start = start
        self._end = end
    
    def __call__(self, attributes, markdown_state):
        return _WriterOutput(self._start, self._end)


def _hyperlink(attributes, markdown_state):
    href = attributes.get("href", "")
    if href:
        return _WriterOutput(
            "[", "]({0})".format(href),
            anchor_position="before",
        )
    else:
        return _default_output


def _image(attributes, markdown_state):
    src = attributes.get("src", "")
    alt_text = attributes.get("alt", "")
    if src or alt_text:
        return _WriterOutput("![{0}]({1})".format(alt_text, src), "")
    else:
        return _default_output


def _list(ordered):
    def call(attributes, markdown_state):
        return _WriterOutput("", "\n")
    
    return call


def _list_item(attributes, markdown_state):
    list_state = markdown_state.list_state
    list_state.count += 1
    return _WriterOutput("{0}. ".format(list_state.count), "\n")


def _init_writers():
    writers = {
        "p": _Wrapped("", "\n\n"),
        "br": _Wrapped("", "  \n"),
        "strong": _symmetric_wrapped("__"),
        "em": _symmetric_wrapped("*"),
        "a": _hyperlink,
        "img": _image,
        "ol": _list(ordered=True),
        "li": _list_item,
    }
    
    for level in range(1, 7):
        writers["h{0}".format(level)] = _Wrapped("#" * level + " ", "\n\n")
    
    return writers


_writers = _init_writers()
_default_output = _WriterOutput("", "")
_default_writer = lambda attributes, markdown_state: _default_output


class MarkdownWriter(object):
    def __init__(self):
        self._fragments = []
        self._element_stack = []
        self._markdown_state = _MarkdownState()
    
    def text(self, text):
        self._fragments.append(_escape_markdown(text))
    
    def start(self, name, attributes=None):
        if attributes is None:
            attributes = {}
        
        output = _writers.get(name, _default_writer)(attributes, self._markdown_state)
        
        anchor_before_start = output.anchor_position == "before"
        if anchor_before_start:
            self._write_anchor(attributes)
        
        self._fragments.append(output.start)
        
        if not anchor_before_start:
            self._write_anchor(attributes)
        
        self._element_stack.append(output.end)

    def end(self, name):
        end = self._element_stack.pop()
        self._fragments.append(end)
    
    def self_closing(self, name, attributes=None):
        self.start(name, attributes)
        self.end(name)
    
    def append(self, other):
        self._fragments.append(other)
    
    def as_string(self):
        return "".join(self._fragments)
    
    def _write_anchor(self, attributes):
        html_id = attributes.get("id")
        if html_id:
            self._fragments.append('<a id="{0}"></a>'.format(html_id))


def _escape_markdown(value):
    return re.sub(r"([\`\*_\{\}\[\]\(\)\#\+\-\.\!])", r"\\\1", re.sub("\\\\", "\\\\\\\\", value))