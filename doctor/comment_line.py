# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Comment Line. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)

# Standard library imports, in alphabetic order.
#
# Module for enumerated types.
# https://docs.python.org/3/library/enum.html
import enum
#
# JSON module.
# https://docs.python.org/3/library/json.html
import json
#
# Regular expressions module.
# https://docs.python.org/3/library/re.html
import re

def dump_match(match):
    if match is None:
        return str(None)

    groups = match_groups(match)
    spans = match.span()
    spanned = tuple(spans) + tuple(
        part.encode('ascii') if len(part) > 0 else ""
        for part in match_spans(match)
    )
    return '{}\n    {}\n    {}'.format(
        str(match.string.encode('ascii')), spanned, groups)

def match_groups(match):
    groups = {}
    for key, value in match.groupdict().items():
        if value is not None:
            groups[key] = value
    return groups    

def match_spans(match):
    str_ = match.string
    spans = match.span()
    return str_[:spans[0]], str_[spans[0]:spans[1]], str_[spans[1]:]

class CommentLineType(enum.Enum):
    START = enum.auto()
    CONTINUE = enum.auto()
    FINISH = enum.auto()

class SourceLine:
    # See: https://docs.python.org/3/library/functions.html#classmethod
    @classmethod
    def read_file(cls, sourcePath, tabSize=4, *args, **kwargs):
        with open(sourcePath) as sourceFile:
            lineNumber = 0
            for line in sourceFile:
                lineNumber += 1
                # Tabs have to be expanded here, when the context of the whole
                # line is available.
                yield cls(lineNumber, line.expandtabs(tabSize), *args, **kwargs)

    @property
    def lineNumber(self):
        '''Line number in source file.'''
        return self._lineNumber
    @lineNumber.setter
    def lineNumber(self, lineNumber):
        self._lineNumber = lineNumber
    
    @property
    def line(self):
        '''Line, including end-of-line if present.'''
        return self._line
    @line.setter
    def line(self, line):
        self._line = line
    
    @property
    def lineType(self):
        return None
    
    def outputs(self, *args, **kwargs):
        yield self.line
    
    def __init__(self, lineNumber=None, line=None):
        self._lineNumber = lineNumber
        self._line = line
    
    def __repr__(self):
        return tuple((self.lineNumber, self.line)).__repr__()

class CommentLine(SourceLine):
    # Following regular expression compilation will happen only once, when this
    # script is run. It's a kind of static class-level value. If it were in the
    # __init__ instead then it would happen every time the class was
    # instantiated.
    _matchTextEOL = re.compile(r'[\r\n]*$')
    
    # Override to an actual property.
    @property
    def lineType(self):
        return self._lineType
    @lineType.setter
    def lineType(self, lineType):
        if isinstance(lineType, CommentLineType):
            self._lineType = lineType
        else:
            raise TypeError('Line type must be a CommentLineType value.')

    # Principal properties.
    @property
    def indent(self):
        '''Indentation space.'''
        return self._indent
    @indent.setter
    def indent(self, indent):
        self._indent = indent

    @property
    def symbol(self):
        '''Comment symbol like /** or * or */.'''
        return self._symbol
    @symbol.setter
    def symbol(self, symbol):
        self._symbol = symbol

    @property
    def margin(self):
        '''Margin space.'''
        return self._margin
    @margin.setter
    def margin(self, margin):
        self._margin = margin

    @property
    def text(self):
        '''Text in the comment.'''
        return self._text
    @text.setter
    def text(self, text):
        self._text = text

    @property
    def eol(self):
        '''End-of-line.'''
        return self._eol
    @eol.setter
    def eol(self, eol):
        self._eol = eol
    
    # Special properties
    @property
    def indentStr(self):
        '''Indentation space.'''
        return None if self.indent is None else " " * self.indent
    @indentStr.setter
    def indentStr(self, indentStr):
        if indentStr is None:
            self.indent = None
            return
        indent = len(indentStr)
        if indent != indentStr.count(' '):
            raise ValueError('Value for indentStr must be all spaces but was'
                             ' passed {}.'.format(indentStr.encode('ascii')))
        self.indent = indent
    
    @property
    def marginStr(self):
        '''Margin as a string.'''
        return None if self.margin is None else " " * self.margin
    @marginStr.setter
    def marginStr(self, marginStr):
        if marginStr is None:
            self.margin = None
            return
        margin = len(marginStr)
        if margin != marginStr.count(' '):
            raise ValueError('Value for marginStr must be all spaces but was'
                             ' passed {}.'.format(marginStr.encode('ascii')))
        self.margin = margin
    
    @property
    def textEOL(self):
        if self.text is None and self.eol is None:
            return None
        return ''.join(("" if self.text is None else self.text,
                        "" if self.eol is None else self.eol))
    @textEOL.setter
    def textEOL(self, textEOL):
        if textEOL is None:
            self.text = None
            self.eol = None
            return
        match = self.matchTextEOL.search(textEOL)
        self.text = textEOL[:match.start()]
        self.eol = textEOL[match.start():]

    # Regular expression properties are provided for readability and so that
    # they can be tested.
    @property
    def matchTextEOL(self):
        return self._matchTextEOL
    
    # https://docs.python.org/3/library/functions.html#staticmethod
    @staticmethod
    def group_startswith(match, prefix):
        '''First parameter can be re.match or groupdict-like.'''
        try:
            groupdict = match.groupdict()
        except AttributeError:
            # Doesn't seem to be an re.match instance. Assume it is
            # groupdict-like.
            groupdict = match
        for key, value in groupdict.items():
            if key.startswith(prefix) and value is not None:
                return key, value
        return None, None

    def read_match(self, match):
        symbol = self.group_startswith(match, 'symbol')[1]
        if symbol is not None:
            self.symbol = symbol
        for attr in ('indent', 'margin'):
            value = self.group_startswith(match, attr)[1]
            if value is not None:
                try:
                    setattr(self, attr + 'Str', value)
                except ValueError as error:
                    # Supplement the Exception context with the whole match.
                    # https://docs.python.org/3/library/exceptions.html
                    raise ValueError('Wrong value in match {}.'.format(
                        dump_match(match))) from error
        return self

    def __init__(self, lineNumber=None, match=None):
        self._lineType = None
        self._lineNumber = lineNumber
        self._indent = None
        self._symbol = None
        self._margin = None
        self._text = None
        self._eol = None
        if match is not None:
            self.read_match(match)
    
    def as_dict(self):
        return_ = {}
        for attr in (
            'lineNumber', 'indent', 'symbol', 'margin', 'text', 'eol'
        ):
            value = getattr(self, attr)
            if value is not None:
                return_[attr] = value
        if self.lineType is not None:
            return_['lineType'] = self.lineType.name
        
        return return_
    
    def __repr__(self):
        return self.as_dict().__repr__()

class CommentLineJSONEncoder(json.JSONEncoder):
    def default(self, object_):
        if isinstance(object_, CommentLine):
            return object_.as_dict()
        return super().default(object_)
