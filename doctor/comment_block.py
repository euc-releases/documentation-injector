# Run with Python 3
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
"""\
Comment Block module. Part of the Doctor documentation tool.
No standalone capability.
"""
# Exit if run other than as a module.
if __name__ == '__main__':
    print(__doc__)
    raise SystemExit(1)
#
# Standard library imports, in alphabetic order.
#
# File path module.
# https://docs.python.org/3/library/os.path.html
import os.path
#
# Regular expressions module.
# https://docs.python.org/3/library/re.html
import re
#
# Local imports
#
# Module with enumeration of comment line types and a handy RE helper.
from doctor.comment_line import CommentLineType, CommentLine
#
# Module for outputting Markdown items.
from doctor.markdown import MarkdownItem, BlockType, SpanType

class CommentBlock:
    # Constant regular expressions get compiled here. See CommentLine class for
    # short discussion.
    #
    # Following syntax elements are used:
    #
    # -   Python r'...' for raw strings that don't get backslash expansion.
    # -   (?P<name>...) for named capture groups.
    # -   Not ^ to anchor because these are called with .match() so it's
    #     implicit.
    # -   Not \s but a space character, because expandtabs will have been called
    #     on the string long before matching. A \s could match some end-of-line
    #     characters, which isn't wanted.
    atCommand = re.compile(
        # Group for matching one of a number of expressions, after an @ sign.
        # The group isn't captured, which is specified by ?:
        r'@(?:'
            # At-commands that are dropped for Swift.
            r'(?P<commandDrop>(?:brief|description|details)) +'
            r'|'
            # At-command for the return value, which gets slightly special
            # handling.
            r'(?P<commandReturn>return)s? +'
            r'|'
            # At-command that is the same in Swift except for an initial
            # capital.
            r'(?P<commandCapitalise>version) +'
            r'|'
            # At-command for parameters, which are followed by a parameter name.
            # Matches param and parameter, but only captures param.
            r'(?P<commandParameter>param)(?:eter)? +(?P<name>\w+) *'
            r'|'
            # At-commands that are ignored, only at-file at the moment.
            r'(?P<commandIgnore>file) +'
        r')'
    )
    
    def __init__(self, commentLines, sourcePath):
        self.indentStart = None
        self.indentContinue = None
        self.allHaveSymbol = True
        self.allIndentedOK = True
        
        self.markdownItems = None
    
        self._swiftSource = (sourcePath is not None
                             and os.path.splitext(sourcePath)[1] == ".swift")
        self._sourcePath = sourcePath[:]
        
        # lines could be a generator or other iterable. This code goes makes
        # more than one pass through the lines so read all of them here.
        self._commentLines = tuple(commentLines)
        self._shuffle()
    
    @classmethod
    def read(cls, iterator, *args, **kwargs):
        comment = None
        for item in iterator:
            endComment = comment is not None
            if item.lineType is not None:
                if comment is None:
                    comment = []
                comment.append(item)
                endComment = item.lineType is CommentLineType.FINISH
                item = None
            
            if endComment:
                yield cls(comment, *args, **kwargs)
                comment = None
            
            if item is not None:
                yield item
    
        if comment is not None:
            yield cls(comment, *args, **kwargs)
    
    def get_texts(self):
        for commentLine in self._commentLines:
            if commentLine.textEOL is not None:
                yield commentLine.textEOL
    
    def write_replacement(self, file, path, fragment):
        start = self._commentLines[0]
        finish = self._commentLines[-1]
        file.writelines((
            start.indentStr, start.symbol, start.marginStr,
            "[doc://", path, "#", fragment, "]",
            "" if start.eol is None else start.eol,
            "" if finish.indentStr is None else finish.indentStr,
            finish.symbol,
            "" if finish.eol is None else finish.eol
        ))
    
    def _attrs_dict(self):
        return {'indentStart': self.indentStart,
                'indentContinue': self.indentContinue,
                'allHaveSymbol': self.allHaveSymbol,
                'allIndentedOK': self.allIndentedOK,
                'swiftSource': self._swiftSource,
                'sourcePath': self._sourcePath}
    
    def __repr__(self):
        return_ = self._attrs_dict()
        return_['texts'] = tuple(self.get_texts())
        return return_

    def __str__(self):
        attrs = self._attrs_dict()
        attrs['lineNumber'] = self.lineNumber
        return '\n'.join(
            [str(attrs), "Block texts:"]
            + ["".join((" " * 4, str(text.encode('ascii'))))
               for text in self.get_texts()]
            + ["Block outputs:"]
            + ["".join((" " * 4, str(output.encode('ascii'))))
               for output in self.outputs()])
    
    @property
    def lineNumber(self):
        return (None if self._commentLines is None
                else (self._commentLines[0].lineNumber,
                      self._commentLines[-1].lineNumber))

    @property
    def markdownTuples(self):
        if self.markdownItems is None:
            return None
        return tuple(item.asTuple() for item in self.markdownItems)
    
    def outputs(self, maxWidth=None):
        yield " " * self.indentStart
        yield "/**"
        yield "\n" if self._swiftSource else " "

        # In the next statement, + 1 because the continuation leaders have one
        # more space than the initial leader.
        indentContinue = " " * (self.indentStart + 1)
        
        # Following code would preserve the original indentation, which might be
        # wanted as an option.
        # indentContinue = " " * (
        #     self.indentStart + 1 if self.indentContinue is None
        #     else self.indentContinue)
        
        if self.markdownItems is not None:
            # import json
            # def json_dump(iterator, indent=4):
            #     return json.dumps(tuple(
            #         item.asTuple() for item in iterator), indent=4)
            
            self._process_at_paragraphs(maxWidth)

            # print("CommentBlock outputs{}".format(json_dump(self.markdownItems)))
            
            # In the next statement, 3 is the length of " * " which will be the
            # comment leader.
            outputs = MarkdownItem.output_all(
                self.markdownItems
                , None if maxWidth is None
                else maxWidth - (self.indentStart
                                 + (2 if self._swiftSource else 3)))

            for index, line in enumerate(''.join(outputs).splitlines(True)):
                if index > 0 or self._swiftSource:
                    yield indentContinue
                    if not self._swiftSource:
                        yield "* "
                yield line

        yield "\n"
        yield indentContinue
        yield "*/"
    
    def _process_at_paragraphs(self, maxWidth):
        for item in self.markdownItems:
            if item.blockType is not BlockType.PARAGRAPH:
                continue
            content0 = item.contents[0]
            if (isinstance(content0, MarkdownItem)
                and content0.spanType is SpanType.TEXT
            ):
                if not isinstance(content0.contents, str):
                    raise AssertionError(
                        "Text span has {} contents.".format(
                            content0.content.__class__))
                atPrefix, line = self._at_line(content0.contents)
                if atPrefix is not None:
                    if maxWidth is not None:
                        if item.custom is not None:
                            raise AssertionError(
                                "Paragraph custom property in use.")
                        item.custom = len(atPrefix)
                    content0.contents = "".join((atPrefix, line))

    def _at_line(self, line):
        message = " on line:\n{}\nin block {}".format(line, self.__repr__())
        
        match = self.atCommand.match(line)
        if match is None:
            if line.startswith("@"):
                print("".join((
                    'Warning: Apparent unrecognised at-command', message)))
            return None, line

        if match.start() != 0:
            raise AssertionError("".join((
                "At-command doesn't start at zero", message)))

        lineAfter = line[match.end():]
        prefix = None

        key, value = CommentLine.group_startswith(match, 'command')
        if key is None:
            raise AssertionError("".join(("No command match", message)))

        lowered = "@{} ".format(value.lower())

        # Xcode will highlight either keyword Returns or Parameter, if there is
        # exactly one space between the hyphen and the keyword.
        if key == 'commandParameter':
            prefix = "".join((
                ("- Parameter " if self._swiftSource else lowered),
                match.group('name'), ":" if self._swiftSource else "", " "
            ))
        elif key == 'commandDrop':
            prefix = "" if self._swiftSource else lowered
        elif key == 'commandCapitalise':
            prefix = ("- {}: ".format(value.capitalize())
                      if self._swiftSource else lowered)                      
        elif key == 'commandReturn':
            # The returns at-command has special handling. The RE captures
            # either @return or @returns as just return. The code here changes
            # it to a consistent Returns, for Swift, or @return otherwise.
            prefix = ("- Returns: " if self._swiftSource else lowered)
        elif key == 'commandIgnore':
            return None, line

        if prefix is None:
            raise AssertionError(
                'Matched at-command "{}" not handled{}'.format(
                    key, message))
    
        return prefix, lineAfter

    def _shuffle(self):
        # This method may change the analysis of comment lines but doesn't
        # change the overall content. It may rearrange between indent, symbol,
        # margin, and text.

        for line in self._commentLines:
            if self.indentStart is None:
                if line.lineType is CommentLineType.START:
                    self.indentStart = line.indent
                else:
                    raise ValueError(
                        'First line should have lineType {} {}.'.format(
                            CommentLineType.START.name, line))

            if line.symbol is None or line.symbol == '':
                self.allHaveSymbol = False
                break
        
        if not self.allHaveSymbol:
            # Not all lines have *, so assume any apart from the start and
            # finish that do shouldn't and shuffle it into the text. This
            # supports, for example, Markdown lists indicated by *, but without
            # comment leaders.
            for line in self._commentLines:
                if line.lineType is not CommentLineType.CONTINUE:
                    continue

                indentLoss = 0
                if (line.indent is not None
                    and line.indent > self.indentStart + 1
                ):
                    indentLoss = line.indent - (self.indentStart + 1)
                    line.indent -= indentLoss
                
                symbol = "" if line.symbol is None else line.symbol
                margin = 0 if line.margin is None else line.margin
                
                if (indentLoss == 0 and symbol == "" and margin == 0):
                    continue

                line.text = ''.join((
                    " " * indentLoss, symbol, " " * margin,
                    "" if line.text is None else line.text))

                line.symbol = None
                line.margin = None
                 # Hmm, maybe "" and 0 instead?
        
        # Lines that are blank or only spaces are allowed in symbol-less
        # comment blocks. Otherwise, everything must be indented the same as the
        # start, or one more than that.

        for index in range(1, len(self._commentLines)):
            line = self._commentLines[index]
            if line.lineType is CommentLineType.START:
                raise ValueError(
                    "Lines after the first shouldn't have lineType"
                    " {} {}.".format(CommentLine.LineType.START.name, line))

            # Ignore blank and space-only lines in leaderless comments.
            textLen = 0 if line.text is None else len(line.text)
            if (not self.allHaveSymbol
                and (line.symbol == "" or line.symbol is None)
                and (textLen == 0 or textLen == line.text.count(' '))
            ):
                continue
            
            if self.indentContinue is None:
                if (line.indent == self.indentStart
                    or line.indent == self.indentStart + 1
                ):
                    self.indentContinue = line.indent
                else:
                    self.allIndentedOK = False
                    break
            
            if line.indent != self.indentContinue:
                self.allIndentedOK = False
                break
        