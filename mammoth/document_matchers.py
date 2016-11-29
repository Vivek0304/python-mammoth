import collections

import cobble


def paragraph(style_id=None, style_name=None, numbering=None):
    return ParagraphMatcher(style_id, style_name, numbering)


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", ["style_id", "style_name", "numbering"])
ParagraphMatcher.element_type = "paragraph"


def run(style_id=None, style_name=None):
    return RunMatcher(style_id, style_name)


RunMatcher = collections.namedtuple("RunMatcher", ["style_id", "style_name"])
RunMatcher.element_type = "run"


class bold(object):
    element_type = "bold"


class italic(object):
    element_type = "italic"


class underline(object):
    element_type = "underline"


class strikethrough(object):
    element_type = "strikethrough"


class comment_reference(object):
    element_type = "comment_reference"


def equal_to(value):
    return StringMatcher(_operator_equal_to, value)


def _operator_equal_to(first, second):
    return first.upper() == second.upper()


@cobble.data
class StringMatcher(object):
    operator = cobble.field()
    value = cobble.field()
    
    def matches(self, other):
        return self.operator(self.value, other)
    
    
